---
name: baseball-sabermetrics
description: Advanced baseball statistics and fantasy sabermetrics digest using FanGraphs data. Use when user asks about player stats, fantasy baseball lineup decisions, waiver wire pickups, stat leaders, or player comparisons.
homepage: https://5cypress.com/keys
metadata: {"openclaw":{"requires":{"env":["5CYPRESS_API_KEY"]},"primaryEnv":"5CYPRESS_API_KEY","emoji":"⚾"}}
---

# Baseball Sabermetrics Digest

Advanced FanGraphs stats — wRC+, xFIP, Barrel%, BABIP, and 50+ more — pulled fresh for fantasy lineup decisions.
Get the edge your leaguemates don't have.

## Setup

Get your API key at **https://5cypress.com/keys** ($7.99/mo).

```
5CYPRESS_API_KEY=5cy_your_key_here
```

## When to Use This Skill

- User asks about a player's advanced stats or fantasy value
- User wants to compare multiple players for a lineup or trade decision
- User asks who the leaders are for a specific stat (wRC+, HR, K/9, etc.)
- User wants a waiver wire analysis or weekly digest
- User asks "is [player] worth starting?" or "who should I pick up?"

## How to Call the API

All requests require: `X-API-Key: <5CYPRESS_API_KEY>`
Base URL: `https://api.5cypress.com`

### Individual player stats
```bash
curl "https://api.5cypress.com/baseball/player?name=Shohei+Ohtani&year=2025" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

### Bulk player comparison (max 12 players)
```bash
curl "https://api.5cypress.com/baseball/digest?names=Ohtani,Judge,Acuna&year=2025" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

### Stat leaders (hitters or pitchers)
```bash
# Best wRC+ hitters
curl "https://api.5cypress.com/baseball/leaders?stat=wRC%2B&year=2025&player_type=hitter&limit=20" \
  -H "X-API-Key: $5CYPRESS_API_KEY"

# Best xFIP pitchers (lower = better — ascending sort is automatic)
curl "https://api.5cypress.com/baseball/leaders?stat=xFIP&year=2025&player_type=pitcher&limit=20" \
  -H "X-API-Key: $5CYPRESS_API_KEY"

# Stolen base leaders
curl "https://api.5cypress.com/baseball/leaders?stat=SB&year=2025&player_type=hitter" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

## Key Stats Explained

**Hitters:**
- `wRC+` — Overall offensive value. 100 = league average. 130+ = all-star.
- `wOBA` — Weighted on-base average. Better than OBP.
- `ISO` — Isolated power (SLG - AVG). 0.200+ = power threat.
- `BABIP` — Luck indicator. Career avg ~.300. High = regression coming.
- `K%` / `BB%` — Strikeout and walk rate. Key for plate discipline.
- `Barrel%` — % of balls hit with elite exit velocity + launch angle. Future production predictor.

**Pitchers:**
- `xFIP` — Expected FIP (luck-neutral ERA). Best single pitching predictor.
- `K/9` — Strikeouts per 9 innings. 9+ = dominant.
- `WHIP` — Walks + hits per inning. <1.20 = strong.
- `LOB%` — Left on base %. Anything over 80% is unsustainable.

## Example Response — Player Stats

```json
{
  "name": "Shohei Ohtani",
  "year": 2025,
  "batting": {
    "G": 148, "PA": 640, "HR": 44, "RBI": 103, "SB": 22,
    "wRC+": 167, "wOBA": 0.421, "AVG": 0.295, "OBP": 0.390,
    "Barrel%": 19.8, "K%": 22.1
  },
  "fantasy_grade": "Elite"
}
```

## Fantasy Grade Scale

| Grade | wRC+ (hitter) | ERA (pitcher) |
|-------|--------------|---------------|
| Elite | 140+ | ≤2.50 |
| Excellent | 120-139 | 2.51-3.50 |
| Above Average | 105-119 | 3.51-4.50 |
| Average | 90-104 | 4.51-5.00 |
| Below Average | <90 | 5.00+ |

## Example Workflows

**Weekly waiver wire digest** — run every Tuesday after waivers process:
> "Give me the baseball sabermetrics digest for [my roster players]"

**Trade evaluation**:
> "Compare Yordan Alvarez and Pete Alonso stats for 2025"

**Category strategy** — if you're losing SB:
> "Who are the top 20 stolen base leaders for 2025?"

## Notes

- Data sourced from FanGraphs via the `pybaseball` library (100% free, no rate limits for normal use)
- Stats cached for 12 hours — call again after midnight for latest updates
- `year` defaults to 2025. Use `year=2024` for previous season.
- Player name search is case-insensitive and supports partial matches

## Handling Errors

- **404**: Player not found → check spelling, try without middle name, or try `year=2024`
- **400**: Invalid stat name → the error message lists available stats
- **503**: pybaseball temporarily unavailable → try again in a few minutes
- **401/402**: Key issue → https://5cypress.com/keys
