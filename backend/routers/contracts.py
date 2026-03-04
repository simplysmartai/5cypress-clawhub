"""
Skill 3: Federal Contract Digest
Queries the USA Spending API (public, no API key required).
Real federal contract data — no mock/example fallbacks.
Filters by NAICS code, state, and keyword so small businesses get only relevant contracts.

USA Spending API: https://api.usaspending.gov/api/v2 (free, public, real data)
No API key needed. Data refreshes weekly.

Endpoints:
  GET /contracts/digest?category=electrical&state=FL&limit=10
  GET /contracts/search?q=roofing+repair&state=TX
  GET /contracts/categories  (valid NAICS category names)
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

# 6-hour cache — contract listings update weekly on USA Spending
_cache: TTLCache = TTLCache(maxsize=200, ttl=21600)

USA_SPENDING_API_BASE = "https://api.usaspending.gov/api/v2/search/spending_by_award"

# Trade category → NAICS code mapping
CATEGORY_NAICS: dict[str, str] = {
    "it":           "541512",
    "cybersecurity":"541519",
    "construction": "236220",
    "electrical":   "238210",
    "roofing":      "238160",
    "plumbing":     "238220",
    "hvac":         "238220",
    "janitorial":   "561720",
    "landscaping":  "561730",
    "staffing":     "561310",
    "accounting":   "541211",
    "legal":        "541110",
    "marketing":    "541810",
    "training":     "611430",
    "logistics":    "488510",
    "security":     "561612",
    "medical":      "621111",
    "engineering":  "541330",
    "architecture": "541310",
}

CATEGORIES = list(CATEGORY_NAICS.keys())


async def _query_usa_spending(
    naics: str,
    state: str | None,
    keyword: str | None,
    limit: int,
) -> list[dict]:
    """Query USA Spending API for real federal contract data (no API key needed)."""
    
    # Build filter criteria
    filters = {
        "naics": [{"contains": naics}],
        "keywords": [keyword] if keyword else [],
        "award_type_codes": ["A", "B", "C", "D"],  # All federal contract types
    }
    
    if state:
        filters["place_of_performance_locations"] = [{"state": state.upper()}]

    params = {
        "filters": filters,
        "limit": min(limit, 100),
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                USA_SPENDING_API_BASE,
                params={"limit": min(limit, 100)},
                json=params,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("results", [])
    except httpx.HTTPStatusError as e:
        logger.error(f"USA Spending HTTP error: {e.response.status_code}")
        raise HTTPException(status_code=502, detail="Federal contract data unavailable")
    except Exception as e:
        logger.error(f"USA Spending query error: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch contracts")


def _format_contract(raw: dict) -> dict:
    """Format USA Spending API response into consistent contract object."""
    award = raw.get("award", {})
    recipient = award.get("recipient", {})
    txn = raw.get("latest_transaction", {})
    place = award.get("place_of_performance", {})
    
    return {
        "id": award.get("id"),
        "title": award.get("description", award.get("title", "Unnamed Award")),
        "type": award.get("type"),
        "agency": award.get("federal_agency", {}).get("name", "Unknown Agency"),
        "posted": txn.get("action_date"),
        "deadline": award.get("period_of_performance_current_end_date"),
        "naics": award.get("naics_code", {}).get("code"),
        "state": place.get("state_code"),
        "city": place.get("city_name"),
        "contact_name": None,  # USA Spending doesn't always have contact info
        "contact_email": None,
        "amount": award.get("total_obligation", 0),
        "url": f"https://www.usaspending.gov/award/{award.get('id')}" if award.get("id") else None,
    }


@router.get("/categories", response_model=SuccessResponse)
async def list_categories():
    """Returns valid category names and their NAICS codes."""
    return SuccessResponse(data=CATEGORY_NAICS, source="5cypress internal mapping")


@router.get("/digest", response_model=SuccessResponse)
async def get_digest(
    category: str = Query(..., description=f"Business category. Valid: {', '.join(CATEGORIES)}"),
    state: str | None = Query(None, description="2-letter state code to filter by location"),
    limit: int = Query(10, ge=1, le=25),
    auth: AuthenticatedKey = Depends(require_plan("contracts")),
):
    """
    Returns active federal contract opportunities for your trade/category.
    Sorted by deadline (soonest first). Perfect for a weekly digest workflow.
    """
    category = category.lower()
    if category not in CATEGORY_NAICS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category '{category}'. Valid: {', '.join(CATEGORIES)}",
        )

    cache_key = f"digest:{category}:{state}:{limit}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    naics = CATEGORY_NAICS[category]
    raw = await _query_usa_spending(naics, state, None, limit)
    formatted = [_format_contract(r) for r in raw]
    formatted.sort(key=lambda x: x.get("deadline") or "9999", reverse=False)

    result = {
        "category": category,
        "naics": naics,
        "state_filter": state,
        "count": len(formatted),
        "opportunities": formatted,
    }
    _cache[cache_key] = result
    return SuccessResponse(data=result, source="USA Spending API")


@router.get("/search", response_model=SuccessResponse)
async def search_contracts(
    q: str = Query(..., description="Keyword search, e.g. 'electrical wiring repair'"),
    state: str | None = Query(None),
    limit: int = Query(10, ge=1, le=25),
    auth: AuthenticatedKey = Depends(require_plan("contracts")),
):
    """
    Full-text keyword search across active SAM.gov opportunities.
    Returns matching contracts with deadline and contact info.
    """
    cache_key = f"search:{q.lower()}:{state}:{limit}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    raw = await _query_usa_spending("", state, q, limit)
    formatted = [_format_contract(r) for r in raw]
    _cache[cache_key] = formatted
    return SuccessResponse(data={"count": len(formatted), "results": formatted}, source="USA Spending API")
