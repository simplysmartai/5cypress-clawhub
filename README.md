# 5 Cypress — ClawHub Skills

Five paid ClawHub skills backed by a single FastAPI service.
All revenue flows through Stripe. One backend powers everything.

## Skills

| Skill | Plan | Price | Endpoint Prefix |
|-------|------|-------|-----------------|
| TCG Price Tracker | `tcg` | $9.99/mo | `/tcg` |
| OSHA Monitor | `osha` | $19.99/mo | `/osha` |
| Federal Contracts | `contracts` | $14.99/mo | `/contracts` |
| Baseball Sabermetrics | `baseball` | $7.99/mo | `/baseball` |
| AI Onboarding Kit | `onboarding` | $99 one-time | `/onboarding` |

---

## Repo Structure

```
backend/           FastAPI service (deploy this to your VPS/Railway)
├── main.py        App entrypoint
├── auth.py        API key validation middleware
├── db.py          SQLite/Postgres key store
├── stripe_webhooks.py  Subscription lifecycle handler
├── models.py      Shared Pydantic models
├── routers/
│   ├── tcg.py
│   ├── osha.py
│   ├── contracts.py
│   ├── baseball.py
│   └── onboarding.py
├── requirements.txt
├── .env.example   Copy to .env and fill in keys
├── Dockerfile
├── Procfile       Heroku/Railway
└── railway.toml

skills/            ClawHub skill bundles (publish each to ClawHub)
├── tcg-price-tracker/SKILL.md
├── osha-monitor/SKILL.md
├── federal-contracts/SKILL.md
├── baseball-sabermetrics/SKILL.md
└── ai-onboarding-kit/SKILL.md
```

---

## Local Development

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
cp .env.example .env          # Fill in your Stripe key etc.

uvicorn main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### Create a test API key (dev only)
```bash
curl -X POST "http://localhost:8000/stripe/test-create-key?email=test@example.com&plan=tcg"
# Returns: {"key": "5cy_abc123...", ...}
```

### Test an endpoint with that key
```bash
curl "http://localhost:8000/tcg/price?card=Lightning+Bolt&game=mtg" \
  -H "X-API-Key: 5cy_abc123..."
```

---

## Deploying to Railway (Recommended)

1. Install Railway CLI: `npm i -g @railway/cli`
2. `cd backend && railway login && railway init`
3. Set environment variables in Railway dashboard (copy from `.env.example`)
4. `railway up`
5. Set your custom domain: `api.5cypress.com` → Railway

Full deploy takes ~3 minutes.

---

## Stripe Setup

For each subscription skill, create a Stripe Product and add metadata:
```
clawhub_plan = tcg        (or osha, contracts, baseball)
```

For the onboarding kit (one-time):
- Create a Payment Link
- Add metadata to the Checkout Session: `clawhub_plan=onboarding`

Set your webhook endpoint in Stripe:
```
https://api.5cypress.com/stripe/webhook
```

Events to listen for:
- `customer.subscription.created`
- `customer.subscription.deleted`
- `customer.subscription.paused`
- `checkout.session.completed`

---

## Publishing to ClawHub

```bash
# Install ClawHub CLI
npx clawhub@latest --version

# Publish each skill
npx clawhub@latest publish skills/tcg-price-tracker
npx clawhub@latest publish skills/osha-monitor
npx clawhub@latest publish skills/federal-contracts
npx clawhub@latest publish skills/baseball-sabermetrics
npx clawhub@latest publish skills/ai-onboarding-kit
```

---

## TODO Before Launch

- [ ] Deploy backend to Railway + set `api.5cypress.com` subdomain
- [ ] Create Stripe products with `clawhub_plan` metadata
- [ ] Set `STRIPE_WEBHOOK_SECRET` in Railway env vars
- [ ] Get free SAM.gov API key → set `SAM_GOV_API_KEY`
- [ ] Add email delivery (Resend.com) in `stripe_webhooks.py` TODOs
- [ ] Create landing page at `5cypress.com/keys` with Stripe embedded checkout
- [ ] Publish all 5 skills to ClawHub
- [ ] Post launch threads to r/magicTCG, r/PokemonTCG, r/fantasybaseball, r/OSHA, r/smallbusiness
