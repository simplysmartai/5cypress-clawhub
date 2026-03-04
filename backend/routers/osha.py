"""
Skill 2: OSHA Violation Monitor
Queries the OSHA Enforcement public API for inspection/violation data.
Filters by trade category (NAICS code) and state.
No API key required from OSHA — fully free public data.

Endpoints:
  GET /osha/violations?trade=roofing&state=TX&limit=20
  GET /osha/summary?trade=roofing&state=TX
  GET /osha/top-violators?trade=roofing&state=TX
  GET /osha/trades  (returns valid trade names + NAICS codes)
"""

import logging
from typing import Literal

import httpx
from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, Query

from auth import AuthenticatedKey, require_plan
from models import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# 4-hour cache — OSHA data doesn't change hourly
_cache: TTLCache = TTLCache(maxsize=200, ttl=14400)

OSHA_API_BASE = "https://data.dol.gov/get/inspection/search"

# NAICS code map for common trades
TRADE_NAICS: dict[str, list[str]] = {
    "roofing":      ["238160"],
    "electrical":   ["238210"],
    "plumbing":     ["238220"],
    "construction": ["236115", "236116", "236117", "236118", "237110", "237120", "237130", "237310", "237990"],
    "hvac":         ["238220"],
    "concrete":     ["238110"],
    "framing":      ["238130"],
    "painting":     ["238320"],
    "excavation":   ["238910"],
    "landscaping":  ["561730"],
    "warehousing":  ["493110", "493120", "493130", "493190"],
    "manufacturing":["311", "312", "313", "314", "315", "316", "321", "322"],
}

TRADE_NAMES = list(TRADE_NAICS.keys())

OSHA_COLUMNS = (
    "activity_nr,reporting_id,estab_name,site_address,site_city,site_state,"
    "site_zip,naics_code,insp_type,open_date,close_case_date,citation_id,"
    "issuance_date,gravity,penalty_amt,current_penalty"
)

STATE_CODES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY",
]


async def _query_osha(naics_codes: list[str], state: str | None, limit: int) -> list[dict]:
    """Query the OSHA BLS enforcement API."""
    results = []
    for naics in naics_codes[:3]:  # Cap to avoid too many requests
        params = {
            "naics_code": naics,
            "limit": str(min(limit, 50)),
            "orderby": "open_date desc",
        }
        if state:
            params["site_state"] = state.upper()

        url = "https://data.dol.gov/get/inspection/search"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(url, params=params, headers={"Accept": "application/json"})
                if r.status_code == 200:
                    data = r.json()
                    items = data if isinstance(data, list) else data.get("inspection", [])
                    results.extend(items)
        except Exception as e:
            logger.error(f"OSHA API error for NAICS {naics}: {e}")

    # Deduplicate by activity_nr
    seen = set()
    deduped = []
    for item in results:
        key = item.get("activity_nr", "")
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped[:limit]


def _format_violation(raw: dict) -> dict:
    try:
        penalty = float(raw.get("current_penalty") or raw.get("penalty_amt") or 0)
    except (ValueError, TypeError):
        penalty = 0.0
    return {
        "inspection_id": raw.get("activity_nr"),
        "company": raw.get("estab_name", "Unknown"),
        "address": f"{raw.get('site_address', '')} {raw.get('site_city', '')} {raw.get('site_state', '')} {raw.get('site_zip', '')}".strip(),
        "state": raw.get("site_state"),
        "naics": raw.get("naics_code"),
        "inspection_type": raw.get("insp_type"),
        "opened": raw.get("open_date"),
        "closed": raw.get("close_case_date"),
        "penalty_usd": penalty,
        "citation_id": raw.get("citation_id"),
        "gravity": raw.get("gravity"),
    }


@router.get("/trades", response_model=SuccessResponse)
async def list_trades():
    """Returns valid trade names you can filter by."""
    return SuccessResponse(
        data={t: TRADE_NAICS[t] for t in TRADE_NAMES},
        source="5cypress internal mapping",
    )


@router.get("/violations", response_model=SuccessResponse)
async def get_violations(
    trade: str = Query(..., description=f"Trade category. Valid: {', '.join(TRADE_NAMES)}"),
    state: str | None = Query(None, description="2-letter state code, e.g. TX"),
    limit: int = Query(20, ge=1, le=50),
    auth: AuthenticatedKey = Depends(require_plan("osha")),
):
    """
    Returns recent OSHA inspections/violations for the given trade and state.
    Sorted by date descending. Great for weekly monitoring workflows.
    """
    trade = trade.lower()
    if trade not in TRADE_NAICS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown trade '{trade}'. Valid trades: {', '.join(TRADE_NAMES)}",
        )
    if state and state.upper() not in STATE_CODES:
        raise HTTPException(status_code=400, detail=f"Invalid state code: {state}")

    cache_key = f"violations:{trade}:{state}:{limit}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    raw_items = await _query_osha(TRADE_NAICS[trade], state, limit)
    formatted = [_format_violation(r) for r in raw_items]
    formatted.sort(key=lambda x: x.get("opened") or "", reverse=True)

    _cache[cache_key] = formatted
    return SuccessResponse(
        data={"count": len(formatted), "violations": formatted},
        source="OSHA Enforcement Data (data.dol.gov)",
    )


@router.get("/summary", response_model=SuccessResponse)
async def get_summary(
    trade: str = Query(...),
    state: str | None = Query(None),
    auth: AuthenticatedKey = Depends(require_plan("osha")),
):
    """
    Returns aggregate stats: total violations, total penalties, most common violation types.
    Good for monthly safety consultant reports.
    """
    cache_key = f"summary:{trade}:{state}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    trade = trade.lower()
    if trade not in TRADE_NAICS:
        raise HTTPException(status_code=400, detail=f"Unknown trade: {trade}")

    raw_items = await _query_osha(TRADE_NAICS[trade], state, 50)
    formatted = [_format_violation(r) for r in raw_items]

    total_penalty = sum(v["penalty_usd"] for v in formatted)
    avg_penalty = total_penalty / max(len(formatted), 1)

    summary = {
        "trade": trade,
        "state_filter": state,
        "total_inspections": len(formatted),
        "total_penalties_usd": round(total_penalty, 2),
        "average_penalty_usd": round(avg_penalty, 2),
        "largest_penalty_usd": max((v["penalty_usd"] for v in formatted), default=0),
        "states_represented": list({v["state"] for v in formatted if v["state"]}),
        "recent_period": f"{formatted[-1]['opened']} to {formatted[0]['opened']}" if formatted else "N/A",
    }

    _cache[cache_key] = summary
    return SuccessResponse(data=summary, source="OSHA Enforcement Data (data.dol.gov)")


@router.get("/top-violators", response_model=SuccessResponse)
async def get_top_violators(
    trade: str = Query(...),
    state: str | None = Query(None),
    auth: AuthenticatedKey = Depends(require_plan("osha")),
):
    """
    Returns companies with the highest total penalties in a trade/state.
    Useful for insurance brokers and safety consultants targeting repeat violators.
    """
    cache_key = f"top-violators:{trade}:{state}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    trade = trade.lower()
    if trade not in TRADE_NAICS:
        raise HTTPException(status_code=400, detail=f"Unknown trade: {trade}")

    raw_items = await _query_osha(TRADE_NAICS[trade], state, 50)
    formatted = [_format_violation(r) for r in raw_items]

    # Aggregate by company
    from collections import defaultdict
    company_stats: dict[str, dict] = defaultdict(lambda: {"total_penalty": 0.0, "count": 0, "address": ""})
    for v in formatted:
        name = v["company"]
        company_stats[name]["total_penalty"] += v["penalty_usd"]
        company_stats[name]["count"] += 1
        company_stats[name]["address"] = v["address"]

    top = sorted(company_stats.items(), key=lambda x: x[1]["total_penalty"], reverse=True)[:10]
    result = [
        {
            "company": name,
            "address": stats["address"],
            "inspection_count": stats["count"],
            "total_penalties_usd": round(stats["total_penalty"], 2),
        }
        for name, stats in top
    ]

    _cache[cache_key] = result
    return SuccessResponse(data=result, source="OSHA Enforcement Data (data.dol.gov)")
