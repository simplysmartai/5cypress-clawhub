"""
Skill 1: MTG / Pokemon TCG Price Tracker
Fetches card prices from TCGPlayer's public search API + scrapes where needed.
Caches responses for 1 hour to stay polite to the source.

Endpoints:
  GET /tcg/price?card=<name>&game=<mtg|pokemon>&set=<optional>
  GET /tcg/movers?game=<mtg|pokemon>&days=7
  GET /tcg/set?name=<set_name>&game=<mtg|pokemon>
"""

import logging
import time
from typing import Literal
from urllib.parse import quote_plus

import httpx
from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, Query

from auth import AuthenticatedKey, require_plan
from models import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# 1-hour TTL cache, max 500 entries
_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)

TCGPLAYER_API_BASE = "https://api.tcgplayer.com"
TCGPLAYER_SEARCH_BASE = "https://www.tcgplayer.com"

# Public TCGPlayer catalog search (no auth needed for basic pricing pages)
PRICECHARTING_API = "https://www.pricecharting.com/api/product"
PRICECHARTING_KEY = ""  # Optional: pricecharting.com has a free tier

GAME_IDS = {
    "mtg": "magic",
    "pokemon": "pokemon",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; 5CypressBot/1.0; +https://5cypress.com)",
    "Accept": "application/json",
}


async def _fetch_pricecharting(card_name: str, game: str) -> dict | None:
    """Query pricecharting.com public API for card price data."""
    game_slug = GAME_IDS.get(game, "magic")
    url = f"https://www.pricecharting.com/api/products?q={quote_plus(card_name)}&id={game_slug}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, headers=HEADERS)
            r.raise_for_status()
            data = r.json()
            products = data.get("products", [])
            if not products:
                return None
            # Return the best match
            return products[0]
    except Exception as e:
        logger.error(f"Pricecharting fetch error: {e}")
        return None


async def _fetch_tcgplayer_search(card_name: str, game: str, set_name: str | None = None) -> list[dict]:
    """
    Scrape TCGPlayer public pricing search.
    Uses TCGPlayer's public JSON endpoint for product search.
    """
    game_slug = GAME_IDS.get(game, "magic")
    params = {
        "q": card_name,
        "productLineName": game_slug,
    }
    if set_name:
        params["setName"] = set_name

    url = f"https://mp-search-api.tcgplayer.com/v1/search/request?q={quote_plus(card_name)}&isFoil=&inStock=true&productLineName={game_slug}"
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(url, headers=HEADERS)
            if r.status_code != 200:
                return []
            data = r.json()
            results = data.get("results", [{}])[0].get("hits", [])
            return results[:10]
    except Exception as e:
        logger.error(f"TCGPlayer search error: {e}")
        return []


def _format_price_result(raw: dict, game: str) -> dict:
    """Normalize a raw pricecharting result into a clean response."""
    return {
        "name": raw.get("product-name", "Unknown"),
        "set": raw.get("console-name", "Unknown"),
        "game": game.upper(),
        "prices": {
            "ungraded": raw.get("price", None),
            "grade_7": raw.get("grade-7-price", None),
            "grade_8": raw.get("grade-8-price", None),
            "grade_9": raw.get("grade-9-price", None),
            "psa_10": raw.get("grade-10-price", None),
        },
        "id": raw.get("id"),
        "url": f"https://www.pricecharting.com/game/{raw.get('console-name', '').lower().replace(' ', '-')}/{raw.get('product-name', '').lower().replace(' ', '-')}",
    }


@router.get("/price", response_model=SuccessResponse)
async def get_card_price(
    card: str = Query(..., description="Card name, e.g. 'Black Lotus' or 'Charizard'"),
    game: Literal["mtg", "pokemon"] = Query("mtg", description="Game: 'mtg' or 'pokemon'"),
    set: str | None = Query(None, description="Optional set name filter"),
    auth: AuthenticatedKey = Depends(require_plan("tcg")),
):
    """
    Get current market price for a TCG card.
    Returns ungraded and graded price tiers where available.
    """
    cache_key = f"price:{game}:{card.lower()}:{set}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    result = await _fetch_pricecharting(card, game)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Card '{card}' not found for game '{game}'. Try a more specific name.",
        )

    formatted = _format_price_result(result, game)
    _cache[cache_key] = formatted

    return SuccessResponse(
        data=formatted,
        source="pricecharting.com",
        cached=False,
    )


@router.get("/search", response_model=SuccessResponse)
async def search_cards(
    q: str = Query(..., description="Search query"),
    game: Literal["mtg", "pokemon"] = Query("mtg"),
    set: str | None = Query(None),
    auth: AuthenticatedKey = Depends(require_plan("tcg")),
):
    """
    Search for cards matching a query. Returns top 10 results with prices.
    """
    cache_key = f"search:{game}:{q.lower()}:{set}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    hits = await _fetch_tcgplayer_search(q, game, set)

    results = []
    for h in hits[:10]:
        results.append({
            "name": h.get("productName", "Unknown"),
            "set": h.get("setName", "Unknown"),
            "market_price": h.get("marketPrice"),
            "low_price": h.get("lowPrice"),
            "mid_price": h.get("midPrice"),
            "rarity": h.get("rarityName"),
            "condition": "Near Mint",
            "url": f"https://www.tcgplayer.com/product/{h.get('productId')}",
            "image_url": h.get("imageUrl"),
        })

    if not results:
        # Fallback to pricecharting
        raw = await _fetch_pricecharting(q, game)
        if raw:
            results = [_format_price_result(raw, game)]

    _cache[cache_key] = results
    return SuccessResponse(data=results, source="tcgplayer.com + pricecharting.com")


@router.get("/movers", response_model=SuccessResponse)
async def get_price_movers(
    game: Literal["mtg", "pokemon"] = Query("mtg"),
    auth: AuthenticatedKey = Depends(require_plan("tcg")),
):
    """
    Returns currently trending / most-viewed cards from TCGPlayer.
    Great for spotting price spikes before they're widely known.
    """
    cache_key = f"movers:{game}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    game_slug = GAME_IDS.get(game, "magic")
    url = f"https://mp-search-api.tcgplayer.com/v1/search/request?q=&isFoil=&inStock=true&productLineName={game_slug}&sort=trending"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, headers=HEADERS)
            r.raise_for_status()
            data = r.json()
            hits = data.get("results", [{}])[0].get("hits", [])[:20]
    except Exception as e:
        logger.error(f"Movers fetch error: {e}")
        hits = []

    movers = [
        {
            "name": h.get("productName"),
            "set": h.get("setName"),
            "market_price": h.get("marketPrice"),
            "low_price": h.get("lowPrice"),
            "rarity": h.get("rarityName"),
            "url": f"https://www.tcgplayer.com/product/{h.get('productId')}",
        }
        for h in hits
    ]

    _cache[cache_key] = movers
    return SuccessResponse(data=movers, source="tcgplayer.com")
