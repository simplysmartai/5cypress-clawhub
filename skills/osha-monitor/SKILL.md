---
name: osha-monitor
description: Monitor OSHA enforcement violations by trade (roofing, electrical, construction, etc.) and state. Returns recent inspections, penalty amounts, and top violators from the federal enforcement database. Use when user asks about OSHA violations, safety compliance, job site penalties, or wants a monthly violation digest.
homepage: https://5cypress.com/keys
metadata: {"openclaw":{"requires":{"env":["5CYPRESS_API_KEY"]},"primaryEnv":"5CYPRESS_API_KEY","emoji":"🦺"}}
---

# OSHA Violation Monitor

Federal OSHA enforcement data filtered for your trade and state.
Designed for safety consultants, insurance brokers, and contractors who need to monitor job site compliance trends.

## Setup

Get your API key at **https://5cypress.com/keys** ($19.99/mo).

Add to your environment:
```
5CYPRESS_API_KEY=5cy_your_key_here
```

## When to Use This Skill

- User wants recent OSHA violations for a specific trade or state
- Safety consultant needs a monthly digest of violations in their region
- Insurance broker is researching a company's compliance history
- Contractor wants to benchmark industry compliance rates
- User asks about penalty amounts or common violation types

## Valid Trade Categories

Call `/osha/trades` to see the full list. Common values:
`roofing`, `electrical`, `plumbing`, `construction`, `hvac`, `concrete`, `painting`, `excavation`, `manufacturing`, `warehousing`

## How to Call the API

All requests require: `X-API-Key: <5CYPRESS_API_KEY>`
Base URL: `https://api.5cypress.com`

### Recent violations for a trade + state
```bash
curl "https://api.5cypress.com/osha/violations?trade=roofing&state=TX&limit=20" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

### Aggregate summary (for reports)
```bash
curl "https://api.5cypress.com/osha/summary?trade=electrical&state=FL" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

### Top violators by penalty amount
```bash
curl "https://api.5cypress.com/osha/top-violators?trade=construction&state=CA" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

### List all valid trade categories
```bash
curl "https://api.5cypress.com/osha/trades" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

## Response Format

```json
{
  "ok": true,
  "data": {
    "count": 18,
    "violations": [
      {
        "inspection_id": "1234567",
        "company": "ABC Roofing LLC",
        "address": "456 Oak St Dallas TX 75201",
        "state": "TX",
        "naics": "238160",
        "inspection_type": "Unprogrammed",
        "opened": "2025-11-12",
        "closed": "2025-12-01",
        "penalty_usd": 14500.00,
        "gravity": "High"
      }
    ]
  }
}
```

## Example Workflows

**Weekly monitoring cron** — run every Monday and deliver to Telegram:
> "Run my OSHA roofing monitor for Texas"

**Monthly safety report** — for a safety consultant:
> "Give me the OSHA summary for electrical contractors in Florida"

**Prospect research** — for insurance sales:
> "Who are the top OSHA violators for construction in California?"

## Handling Errors

- **400**: Invalid trade or state → call `/osha/trades` for valid values
- **401/402**: Key issue → https://5cypress.com/keys
