---
name: federal-contracts
description: Digest active federal contract opportunities from SAM.gov filtered by business category and state. Use when user asks about government contracts, federal bids, SAM.gov opportunities, or wants a weekly contract digest for their trade.
homepage: https://5cypress.com/keys
metadata: {"openclaw":{"requires":{"env":["5CYPRESS_API_KEY"]},"primaryEnv":"5CYPRESS_API_KEY","emoji":"🏛️"}}
---

# Federal Contracts Digest

Active federal contract opportunities from SAM.gov, filtered for your trade and state.
Stop drowning in irrelevant bids — get only the contracts where you can actually win.

## Setup

Get your API key at **https://5cypress.com/keys** ($14.99/mo).

```
5CYPRESS_API_KEY=5cy_your_key_here
```

## When to Use This Skill

- User asks about federal contracts or government bids in their industry
- Small business owner wants a weekly digest of relevant SAM.gov opportunities
- IT firm or contractor wants contracts filtered to their NAICS code
- User asks about contract deadlines, agencies, or set-aside status

## Valid Categories

Call `/contracts/categories` for the full list. Common values:
`it`, `cybersecurity`, `construction`, `electrical`, `roofing`, `plumbing`,
`hvac`, `accounting`, `legal`, `marketing`, `staffing`, `medical`, `engineering`

## How to Call the API

All requests require: `X-API-Key: <5CYPRESS_API_KEY>`
Base URL: `https://api.5cypress.com`

### Weekly digest for a category + state
```bash
curl "https://api.5cypress.com/contracts/digest?category=electrical&state=FL&limit=10" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

### Keyword search across all active opportunities
```bash
curl "https://api.5cypress.com/contracts/search?q=network+infrastructure+upgrade&state=TX" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

### List all valid categories
```bash
curl "https://api.5cypress.com/contracts/categories" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

## Response Format

```json
{
  "ok": true,
  "data": {
    "category": "electrical",
    "naics": "238210",
    "state_filter": "FL",
    "count": 8,
    "opportunities": [
      {
        "id": "W912DR-26-R-0001",
        "title": "Electrical Upgrades — Camp Blanding",
        "type": "Solicitation",
        "agency": "DEPT OF THE ARMY",
        "posted": "2026-02-10",
        "deadline": "2026-03-15",
        "state": "FL",
        "city": "Jacksonville",
        "contact_name": "Jane Smith",
        "contact_email": "jane.smith@army.mil",
        "set_aside": "Small Business",
        "url": "https://sam.gov/opp/W912DR-26-R-0001/view"
      }
    ]
  }
}
```

## Example Workflows

**Monday morning contract digest** — cron at 8am Monday:
> "Run my federal contracts digest for electrical work in Florida"

**Ad-hoc search**:
> "Search SAM.gov for roofing repair contracts in Texas"

**Set-aside opportunity finder** — good for 8(a) or HUBZone firms:
> "Find federal IT contracts in Virginia" → check `set_aside` field in results

## Notes

- Data sourced directly from SAM.gov via their public Opportunities API
- Requires a free SAM.gov API key (configured server-side — no action needed from you)
- Results may show sample/example data if the server SAM.gov key is being rate-limited; try again in an hour
- All opportunities link directly to SAM.gov for full solicitation details

## Handling Errors

- **400**: Unknown category → call `/contracts/categories` for valid values
- **401/402**: Key issue → https://5cypress.com/keys
