"""
Skill 3: Federal Contract / SAM.gov Opportunity Digest
Queries the SAM.gov Opportunities API (free public API key required from SAM.gov).
Filters by NAICS code, state, and keyword so small businesses get only relevant contracts.

SAM.gov API key: free at https://sam.gov/profile/details (API Keys tab)
Set in env: SAM_GOV_API_KEY=your_key_here

Endpoints:
  GET /contracts/digest?category=electrical&state=FL&limit=10
  GET /contracts/search?q=roofing+repair&state=TX
  GET /contracts/categories  (valid NAICS category names)
"""

import os
import logging
from typing import Literal

import httpx
from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, Query

from auth import AuthenticatedKey, require_plan
from models import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# 6-hour cache — contract listings update daily
_cache: TTLCache = TTLCache(maxsize=200, ttl=21600)

SAM_API_BASE = "https://api.sam.gov/opportunities/v2/search"
SAM_API_KEY = os.getenv("SAM_GOV_API_KEY", "")

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


async def _query_sam(
    naics: str,
    state: str | None,
    keyword: str | None,
    limit: int,
) -> list[dict]:
    if not SAM_API_KEY:
        # Return mock data if no key configured so skill is still testable
        return _mock_contracts(naics, state)

    params: dict = {
        "api_key": SAM_API_KEY,
        "ptype": "o",          # opportunities
        "ncode": naics,
        "limit": str(min(limit, 25)),
        "offset": "0",
        "active": "Yes",
        "sorty": "datePosted",
        "sort": "-",
    }
    if state:
        params["state"] = state.upper()
    if keyword:
        params["q"] = keyword

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(SAM_API_BASE, params=params)
            r.raise_for_status()
            data = r.json()
            return data.get("opportunitiesData", [])
    except httpx.HTTPStatusError as e:
        logger.error(f"SAM.gov HTTP error: {e.response.status_code} — {e.response.text[:200]}")
        return []
    except Exception as e:
        logger.error(f"SAM.gov query error: {e}")
        return []


def _mock_contracts(naics: str, state: str | None) -> list[dict]:
    """Returns example data when SAM_GOV_API_KEY is not configured."""
    return [
        {
            "noticeId": "MOCK-001",
            "title": f"[EXAMPLE] Facility Upgrade — NAICS {naics}",
            "postedDate": "2026-02-20",
            "responseDeadLine": "2026-03-20",
            "naicsCode": naics,
            "type": "Combined Synopsis/Solicitation",
            "fullParentPathName": "DEPT OF DEFENSE",
            "placeOfPerformance": {"state": {"code": state or "VA"}},
            "pointOfContact": [{"email": "contracting@agency.gov", "name": "Jane Smith"}],
            "_note": "This is example data. Add SAM_GOV_API_KEY env var for live data.",
        }
    ]


def _format_contract(raw: dict) -> dict:
    pop = raw.get("placeOfPerformance", {})
    state_info = pop.get("state", {})
    contacts = raw.get("pointOfContact", [{}])
    contact = contacts[0] if contacts else {}
    return {
        "id": raw.get("noticeId"),
        "title": raw.get("title"),
        "type": raw.get("type"),
        "agency": raw.get("fullParentPathName", "").split(".")[0].strip(),
        "posted": raw.get("postedDate"),
        "deadline": raw.get("responseDeadLine"),
        "naics": raw.get("naicsCode"),
        "state": state_info.get("code"),
        "city": pop.get("city", {}).get("name"),
        "contact_name": contact.get("name"),
        "contact_email": contact.get("email"),
        "set_aside": raw.get("typeOfSetAsideDescription"),
        "url": f"https://sam.gov/opp/{raw.get('noticeId')}/view" if raw.get("noticeId") else None,
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
    raw = await _query_sam(naics, state, None, limit)
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
    return SuccessResponse(data=result, source="SAM.gov Opportunities API")


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

    if not SAM_API_KEY:
        return SuccessResponse(
            data={"note": "Add SAM_GOV_API_KEY env var for live search results.", "query": q},
            source="mock",
        )

    params: dict = {
        "api_key": SAM_API_KEY,
        "q": q,
        "ptype": "o",
        "limit": str(limit),
        "active": "Yes",
    }
    if state:
        params["state"] = state.upper()

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(SAM_API_BASE, params=params)
            r.raise_for_status()
            data = r.json()
            raw = data.get("opportunitiesData", [])
    except Exception as e:
        logger.error(f"SAM.gov search error: {e}")
        raw = []

    formatted = [_format_contract(r) for r in raw]
    _cache[cache_key] = formatted
    return SuccessResponse(data={"count": len(formatted), "results": formatted}, source="SAM.gov")
