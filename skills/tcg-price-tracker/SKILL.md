---
name: tcg-price-tracker
description: Track MTG and Pokemon TCG card prices, spot movers, and search set values via live TCGPlayer data. Use when user asks about card prices, recent price spikes, set releases, or portfolio value.
homepage: https://5cypress.com/keys
metadata: {"openclaw":{"requires":{"env":["5CYPRESS_API_KEY"]},"primaryEnv":"5CYPRESS_API_KEY","emoji":"🃏"}}
---

# TCG Price Tracker

Real-time MTG and Pokémon card prices powered by TCGPlayer + PriceCharting data.
Get card prices, spot market movers before they're widely known, and evaluate set values.

## Setup

Get your API key at **https://5cypress.com/keys** ($9.99/mo).

Add to your environment:
```
5CYPRESS_API_KEY=5cy_your_key_here
```

Or tell OpenClaw: `set my 5CYPRESS_API_KEY to 5cy_...`

## When to Use This Skill

- User asks about a card's current price or recent price movement
- User wants to know what cards are trending/spiking right now
- User wants to search cards in a specific set
- User is evaluating whether to buy/sell a card or collection

## How to Call the API

All requests require the header: `X-API-Key: <5CYPRESS_API_KEY>`
Base URL: `https://api.5cypress.com`

### Get a card's price
```bash
curl "https://api.5cypress.com/tcg/price?card=Black+Lotus&game=mtg" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

```bash
curl "https://api.5cypress.com/tcg/price?card=Charizard&game=pokemon" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

### Search cards (by name, optional set filter)
```bash
curl "https://api.5cypress.com/tcg/search?q=Lightning+Bolt&game=mtg&set=alpha" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

### Get trending movers right now
```bash
curl "https://api.5cypress.com/tcg/movers?game=mtg" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```
```bash
curl "https://api.5cypress.com/tcg/movers?game=pokemon" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

## Response Format

All endpoints return:
```json
{
  "ok": true,
  "data": { ... },
  "source": "tcgplayer.com + pricecharting.com",
  "cached": false
}
```

Price fields (where available):
- `prices.ungraded` — raw/played price
- `prices.grade_9` — PSA/BGS 9 equivalent
- `prices.psa_10` — gem mint graded price
- `market_price` / `low_price` / `mid_price` — TCGPlayer listing prices

## Handling Errors

- **401**: Key missing or invalid → direct user to https://5cypress.com/keys
- **402**: Subscription lapsed → direct user to renew at https://5cypress.com/keys
- **404**: Card not found → suggest checking spelling or trying without set filter

## Example Responses to User

For `/tcg/price`:
> "**Black Lotus (Alpha)** is currently priced at $X,XXX ungraded on PriceCharting, with PSA 10 copies at $XX,XXX. Prices cached as of [timestamp]."

For `/tcg/movers`:
> "Top MTG movers right now: 1. **[Card]** — $XX (up from $XX), 2. **[Card]** — $XX. Likely driven by recent tournament results."
