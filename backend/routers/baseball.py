"""
Skill 4: Baseball / Fantasy Sabermetrics Digest
Uses pybaseball (free, wraps FanGraphs, Baseball Reference, Baseball Savant/Statcast).
Returns fantasy-relevant advanced stats with trend analysis.

Install: pip install pybaseball

Endpoints:
  GET /baseball/player?name=Shohei+Ohtani&year=2025
  GET /baseball/digest?names=Ohtani,Judge,Acuna&year=2025
  GET /baseball/leaders?stat=wRC&year=2025&limit=20
  GET /baseball/statcast?name=Freddie+Freeman&year=2025
"""

import logging
from typing import Literal
from functools import lru_cache

import httpx
from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, Query

from auth import AuthenticatedKey, require_plan
from models import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# 12-hour cache — stats update daily during season
_cache: TTLCache = TTLCache(maxsize=300, ttl=43200)

# Season year default
CURRENT_YEAR = 2025

# Key fantasy stats to surface (FanGraphs field names)
BATTING_STATS = [
    "Name", "Team", "G", "PA", "HR", "R", "RBI", "SB",
    "BB%", "K%", "ISO", "BABIP", "AVG", "OBP", "SLG", "wOBA", "wRC+",
    "xBA", "xSLG", "xwOBA", "EV", "LA", "Barrel%",
]

PITCHING_STATS = [
    "Name", "Team", "W", "L", "ERA", "G", "GS", "IP", "K/9", "BB/9",
    "HR/9", "BABIP", "LOB%", "ERA-", "FIP", "xFIP", "K%", "BB%",
    "Barrel%", "HardHit%",
]


def _safe_import_pybaseball():
    """Import pybaseball only when needed to avoid slow startup."""
    try:
        import pybaseball
        pybaseball.cache.enable()
        return pybaseball
    except ImportError:
        return None


def _round_stat(val, decimals: int = 3):
    try:
        return round(float(val), decimals)
    except (TypeError, ValueError):
        return val


def _format_batting_row(row: dict, stat_cols: list[str]) -> dict:
    result = {}
    for col in stat_cols:
        if col in row:
            val = row[col]
            result[col] = _round_stat(val) if isinstance(val, float) else val
    return result


def _fantasy_grade(wrc_plus: float | None, era: float | None) -> str:
    """Quick fantasy tier label."""
    if wrc_plus is not None:
        if wrc_plus >= 140:  return "Elite"
        if wrc_plus >= 120:  return "Excellent"
        if wrc_plus >= 105:  return "Above Average"
        if wrc_plus >= 90:   return "Average"
        return "Below Average"
    if era is not None:
        if era <= 2.5:  return "Elite"
        if era <= 3.5:  return "Excellent"
        if era <= 4.5:  return "Above Average"
        if era <= 5.0:  return "Average"
        return "Below Average"
    return "Unknown"


@router.get("/player", response_model=SuccessResponse)
async def get_player_stats(
    name: str = Query(..., description="Player's full name, e.g. 'Shohei Ohtani'"),
    year: int = Query(CURRENT_YEAR, ge=2000, le=2026),
    auth: AuthenticatedKey = Depends(require_plan("baseball")),
):
    """
    Returns advanced batting + pitching stats for a player in a given year.
    Includes fantasy-grade tier and key metrics for lineup decisions.
    """
    cache_key = f"player:{name.lower()}:{year}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    pb = _safe_import_pybaseball()
    if not pb:
        raise HTTPException(status_code=503, detail="pybaseball not installed on this server.")

    try:
        # Fetch batting leaderboard and filter by name
        batting = pb.batting_stats(year, qual=1)
        batting_row = batting[batting["Name"].str.lower() == name.lower()]

        pitching = pb.pitching_stats(year, qual=1)
        pitching_row = pitching[pitching["Name"].str.lower() == name.lower()]

        if batting_row.empty and pitching_row.empty:
            # Try partial match
            batting_row = batting[batting["Name"].str.lower().str.contains(name.lower(), na=False)]
            pitching_row = pitching[pitching["Name"].str.lower().str.contains(name.lower(), na=False)]

        if batting_row.empty and pitching_row.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Player '{name}' not found for {year}. Check spelling or try year={year-1}.",
            )

        result: dict = {"name": name, "year": year}

        if not batting_row.empty:
            row = batting_row.iloc[0].to_dict()
            wrc = _round_stat(row.get("wRC+"))
            result["batting"] = {
                k: _round_stat(row[k]) if isinstance(row.get(k), float) else row.get(k)
                for k in BATTING_STATS if k in row
            }
            result["fantasy_grade"] = _fantasy_grade(wrc, None)

        if not pitching_row.empty:
            row = pitching_row.iloc[0].to_dict()
            era = _round_stat(row.get("ERA"))
            result["pitching"] = {
                k: _round_stat(row[k]) if isinstance(row.get(k), float) else row.get(k)
                for k in PITCHING_STATS if k in row
            }
            if "fantasy_grade" not in result:
                result["fantasy_grade"] = _fantasy_grade(None, era)

        _cache[cache_key] = result
        return SuccessResponse(data=result, source=f"FanGraphs via pybaseball ({year})")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"pybaseball error for {name}/{year}: {e}")
        raise HTTPException(status_code=502, detail=f"Stats fetch failed: {str(e)[:200]}")


@router.get("/digest", response_model=SuccessResponse)
async def get_player_digest(
    names: str = Query(..., description="Comma-separated player names, e.g. 'Ohtani,Judge,Acuna'"),
    year: int = Query(CURRENT_YEAR, ge=2000, le=2026),
    auth: AuthenticatedKey = Depends(require_plan("baseball")),
):
    """
    Bulk stats for a roster of players. Returns a comparison table
    perfect for weekly fantasy waiver decisions.
    """
    player_list = [n.strip() for n in names.split(",") if n.strip()][:12]  # Max 12

    cache_key = f"digest:{','.join(sorted(player_list)).lower()}:{year}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    pb = _safe_import_pybaseball()
    if not pb:
        raise HTTPException(status_code=503, detail="pybaseball not installed on this server.")

    try:
        batting = pb.batting_stats(year, qual=1)
        pitching = pb.pitching_stats(year, qual=1)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FanGraphs data unavailable: {str(e)[:200]}")

    output = []
    not_found = []

    for name in player_list:
        b_row = batting[batting["Name"].str.lower() == name.lower()]
        p_row = pitching[pitching["Name"].str.lower() == name.lower()]

        if b_row.empty:
            b_row = batting[batting["Name"].str.lower().str.contains(name.lower(), na=False)]
        if p_row.empty:
            p_row = pitching[pitching["Name"].str.lower().str.contains(name.lower(), na=False)]

        if b_row.empty and p_row.empty:
            not_found.append(name)
            continue

        player_data: dict = {"name": name}
        if not b_row.empty:
            row = b_row.iloc[0].to_dict()
            player_data["G"] = row.get("G")
            player_data["HR"] = row.get("HR")
            player_data["RBI"] = row.get("RBI")
            player_data["SB"] = row.get("SB")
            player_data["wRC+"] = _round_stat(row.get("wRC+"))
            player_data["wOBA"] = _round_stat(row.get("wOBA"))
            player_data["AVG"] = _round_stat(row.get("AVG"))
            player_data["OBP"] = _round_stat(row.get("OBP"))
            player_data["type"] = "hitter"
            player_data["fantasy_grade"] = _fantasy_grade(player_data["wRC+"], None)
        elif not p_row.empty:
            row = p_row.iloc[0].to_dict()
            player_data["W"] = row.get("W")
            player_data["ERA"] = _round_stat(row.get("ERA"))
            player_data["xFIP"] = _round_stat(row.get("xFIP"))
            player_data["K/9"] = _round_stat(row.get("K/9"))
            player_data["WHIP"] = _round_stat(row.get("WHIP"))
            player_data["IP"] = _round_stat(row.get("IP"))
            player_data["type"] = "pitcher"
            player_data["fantasy_grade"] = _fantasy_grade(None, player_data["ERA"])
        output.append(player_data)

    result = {
        "year": year,
        "players": output,
        "not_found": not_found,
    }
    _cache[cache_key] = result
    return SuccessResponse(data=result, source=f"FanGraphs via pybaseball ({year})")


@router.get("/leaders", response_model=SuccessResponse)
async def get_stat_leaders(
    stat: str = Query("wRC+", description="Stat column to rank by. Common: wRC+, HR, SB, ERA, xFIP, K/9"),
    year: int = Query(CURRENT_YEAR, ge=2000, le=2026),
    player_type: Literal["hitter", "pitcher"] = Query("hitter"),
    limit: int = Query(20, ge=5, le=50),
    auth: AuthenticatedKey = Depends(require_plan("baseball")),
):
    """
    Returns the top N leaders for any FanGraphs stat column.
    Great for identifying pickups in categories you're losing.
    """
    cache_key = f"leaders:{stat}:{year}:{player_type}:{limit}"
    if cache_key in _cache:
        return SuccessResponse(data=_cache[cache_key], source="cache", cached=True)

    pb = _safe_import_pybaseball()
    if not pb:
        raise HTTPException(status_code=503, detail="pybaseball not installed on this server.")

    try:
        if player_type == "hitter":
            df = pb.batting_stats(year, qual=50)
        else:
            df = pb.pitching_stats(year, qual=20)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FanGraphs unavailable: {str(e)[:200]}")

    if stat not in df.columns:
        available = [c for c in df.columns if not c.startswith("playerid")]
        raise HTTPException(
            status_code=400,
            detail=f"Stat '{stat}' not found. Available stats include: {', '.join(available[:30])}",
        )

    ascending = stat in ("ERA", "FIP", "xFIP", "WHIP", "BB/9", "BB%")
    top = df.nsmallest(limit, stat) if ascending else df.nlargest(limit, stat)

    display_cols = ["Name", "Team", stat]
    for extra in (["HR", "RBI", "SB", "wRC+", "AVG"] if player_type == "hitter" else ["ERA", "xFIP", "K/9", "IP", "W"]):
        if extra in top.columns and extra != stat:
            display_cols.append(extra)

    rows = []
    for rank, (_, row) in enumerate(top.iterrows(), 1):
        entry: dict = {"rank": rank}
        for col in display_cols:
            if col in row.index:
                val = row[col]
                entry[col] = _round_stat(val) if isinstance(val, float) else val
        rows.append(entry)

    result = {"stat": stat, "year": year, "player_type": player_type, "leaders": rows}
    _cache[cache_key] = result
    return SuccessResponse(data=result, source=f"FanGraphs via pybaseball ({year})")
