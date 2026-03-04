# Production Deploy Checklist

Before deploying the 5 Cypress ClawHub backend to VPS, complete these items in order. **Do NOT skip any steps.**

---

## ✅ Pre-Deploy Verification (Complete Locally First)

- [ ] All tests pass: `pytest tests/ -v` returns 40+ passed, 0 failed
- [ ] Health check works: `curl http://localhost:8000/health` returns 200
- [ ] Auth layer tested: Invalid key returns 401, valid key works
- [ ] Rate limiting tested: 101st request returns 429
- [ ] All 5 skills tested locally (see TESTING.md Phase 5)

---

## 🔑 1. Collect Required Configuration Values

**These 6 values are BLOCKING. Without them, deploy will fail on day 1.**

### 1.1 Stripe Setup

- [ ] **Stripe Secret Key**: Get from Stripe Dashboard → Developers → Keys. Format: `sk_test_...` or `sk_live_...`
  - Value: `________________________`

- [ ] **Stripe Webhook Secret**: Dashboard → Developers → Webhooks → Signing secret. Format: `whsec_...`
  - Value: `________________________`

- [ ] **Stripe Product IDs**: Create 5 products (or use existing):
  - [ ] Product ID for TCG skill (monthly subscription)
    - Product name: "TCG Price Tracker"
    - Pricing: $9.99/month
    - Value: `prod_________________________`
  - [ ] Product ID for OSHA skill (monthly subscription)
    - Product name: "OSHA Monitor"
    - Pricing: $14.99/month
    - Value: `prod_________________________`
  - [ ] Product ID for Contracts skill (monthly subscription)
    - Product name: "Federal Contracts"
    - Pricing: $19.99/month
    - Value: `prod_________________________`
  - [ ] Product ID for Baseball skill (monthly subscription)
    - Product name: "Baseball Sabermetrics"
    - Pricing: $9.99/month
    - Value: `prod_________________________`
  - [ ] Product ID for Onboarding skill (one-time purchase)
    - Product name: "AI Onboarding Kit"
    - Pricing: $99 (one-time)
    - **Important:** Ensure one-time purchase is configured (not subscription)
    - Value: `prod_________________________`

### 1.2 VPS Domain

- [ ] Confirm VPS domain or subdomain (e.g., `api.5cypress.com` or `clawhub.5cypress.com`)
  - Value: `________________________`
  - Update `.env` variable: `VPS_BASE_URL=https://api.5cypress.com`

### 1.3 External API Keys

- [ ] **SAM.gov API Key** (for Federal Contracts skill):
  - Go to https://api.sam.gov → Create developer account (free, 2 min)
  - Get API key from account settings
  - Value: `________________________`
  - Update `.env` variable: `SAM_GOV_API_KEY=your_key_here`

- [ ] **Resend Email API Key** (optional, for sending API keys to users):
  - Go to https://resend.com → Create account → Get API key
  - Value: `________________________`
  - Update `.env` variable: `RESEND_API_KEY=your_key_here`

### 1.4 GitHub

- [ ] Confirm GitHub repository name (default: `5cypress-clawhub`)
  - Go to GitHub → Create new public repo: `5cypress/5cypress-clawhub`
  - Clone locally: `git clone https://github.com/5cypress/5cypress-clawhub.git`
  - Value: `https://github.com/5cypress/5cypress-clawhub`

---

## 📝 2. Update Environment Variables

Create **2 files** in the repo root:

### 2.1 `.env.production`

```bash
# Application
ENVIRONMENT=production
PORT=8000
VPS_BASE_URL=https://api.5cypress.com  # ← Replace with your domain

# Database (use PostgreSQL on VPS, not SQLite)
DATABASE_URL=postgresql://user:password@db.railway.app:5432/5cypress

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxxx  # ← Your secret key
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx  # ← Your webhook secret

# External APIs
SAM_GOV_API_KEY=your_key_from_api.sam.gov  # ← Your SAM.gov key
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxx  # ← Optional: for email delivery

# Logging
LOG_LEVEL=info
```

**⚠️ CRITICAL: This file contains secrets. NEVER commit to git. Add to `.gitignore`:**

```
.env.production
.env.local
.env.*.local
.DS_Store
*.pyc
__pycache__/
.pytest_cache/
htmlcov/
.venv/
```

### 2.2 `.env.example` (for public repo)

```bash
# Copy of .env.production with placeholders ONLY
ENVIRONMENT=production
PORT=8000
VPS_BASE_URL=https://api.5cypress.com

DATABASE_URL=postgresql://user:password@db.railway.app:5432/clawhub
STRIPE_SECRET_KEY=sk_live_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here

SAM_GOV_API_KEY=your_sam_gov_key
RESEND_API_KEY=your_resend_key_here

LOG_LEVEL=info
```

---

## 🛠️ 3. Wire Stripe Product IDs into Code

Update `stripe_webhooks.py` with your actual product IDs:

```python
# In stripe_webhooks.py, function get_or_create_plan_from_product():

# Replace these placeholder values:
PLAN_MAPPING = {
    "prod_abc123xyz": "tcg",              # ← Your TCG product ID
    "prod_def456uvw": "osha",             # ← Your OSHA product ID
    "prod_ghi789rst": "contracts",        # ← Your Contracts product ID
    "prod_jkl012opq": "baseball",         # ← Your Baseball product ID
    "prod_mno345lmn": "onboarding",       # ← Your Onboarding product ID
}
```

---

## 🚀 4. Deploy to Railway (Recommended)

Railway is recommended for fastest deployment (Heroku and others also work).

### 4.1 Create Railway Account

- [ ] Go to https://railway.app
- [ ] Sign up with GitHub account
- [ ] Create new project

### 4.2 Deploy Backend

```bash
# In the backend folder, login to Railway
railway login

# Link to your Railway project
railway link

# Deploy
railway up
```

### 4.3 Set Environment Variables on Railway

In Railway dashboard:
1. Click your project
2. Go to Variables tab
3. Add all variables from `.env.production` (don't include `.env.production` file itself)
4. **Important:** Set `DATABASE_URL` to Railway-provided PostgreSQL URL

### 4.4 Add PostgreSQL Database

In Railway dashboard:
1. Click "Add Service"
2. Select "PostgreSQL"
3. Railway will auto-populate `DATABASE_URL` variable

### 4.5 Verify Deployment

```bash
# Get the deployed service URL from Railway dashboard
# Should be something like: https://5cypress-clawhub-server-prod.up.railway.app

curl https://5cypress-clawhub-server-prod.up.railway.app/health
```

Expected: 200 status with health data

---

## 🔗 5. Configure Stripe Webhook

This tells Stripe to send events to your deployed API.

### 5.1 Create Webhook Endpoint

In Stripe Dashboard → Developers → Webhooks:

1. Click "Add endpoint"
2. URL: `https://your-railway-url/stripe/webhook`
3. Events to send: Select only these 3:
   - `customer.subscription.created`
   - `customer.subscription.deleted`
   - `customer.subscription.paused`
   - `checkout.session.completed`
4. Click "Add endpoint"
5. Copy the signing secret (`whsec_...`)
6. Update Railway variable: `STRIPE_WEBHOOK_SECRET=whsec_...`

### 5.2 Test Webhook

```bash
# Send test event (from Stripe dashboard)
# Trigger a test subscription.created event
# Check Railway logs to confirm webhook received
```

Expected in logs: `Webhook received: customer.subscription.created`

---

## 📧 6. Configure Email Delivery (Optional)

If users complain they never receive API keys:

### 6.1 Set Resend API Key

- [ ] Go to https://resend.com
- [ ] Get API key
- [ ] Update Railway variable: `RESEND_API_KEY=re_...`

### 6.2 Update Email Address in stripe_webhooks.py

```python
# In stripe_webhooks.py, function on_subscription_created():

# Replace placeholder:
FROM_EMAIL = "keys@5cypress.com"  # ← Use your actual email domain
TO_EMAIL = customer.email

# Send email via Resend
```

---

## 🧪 7. Production Smoke Tests

Once deployed, run these tests against live VPS:

```bash
# Replace https://your-railway-url with actual URL
LIVE_URL=https://5cypress-clawhub-server-prod.up.railway.app
API_KEY=your_test_api_key_from_db

# Test health
curl $LIVE_URL/health

# Test auth with invalid key
curl -H "X-API-Key: invalid" $LIVE_URL/health  # Should return 401

# Test TCG endpoint
curl -H "X-API-Key: $API_KEY" "$LIVE_URL/tcg/price?card=Black+Lotus&game=mtg"

# Test rate limiting (send 101 requests)
for i in {1..101}; do curl -s -H "X-API-Key: $API_KEY" $LIVE_URL/health > /dev/null; done
curl -H "X-API-Key: $API_KEY" $LIVE_URL/health  # Should return 429

# All other skill endpoints
curl -H "X-API-Key: $API_KEY" "$LIVE_URL/osha/trades"
curl -H "X-API-Key: $API_KEY" "$LIVE_URL/contracts/categories"
curl -H "X-API-Key: $API_KEY" "$LIVE_URL/onboarding/industries"
```

All should return 200 (except rate limit test returns 429).

---

## 📊 8. Monitoring & Logging

### 8.1 Set Up Logging

Ensure `LOG_LEVEL=info` in production. Check Railway logs:

```bash
railway logs --follow
```

### 8.2 Monitor Key Metrics

Set alerts for:
- Error rate > 5%
- Response time p95 > 1 second
- Database connection failures

---

## 🎯 9. Publish to ClawHub Marketplace

Once everything works on live VPS:

### 9.1 Create ClawHub Account

- [ ] Go to https://clawhub.ai
- [ ] Sign up as developer
- [ ] Create publisher profile

### 9.2 Register 5 Skills

For each skill, provide:
- Name (e.g., "TCG Price Tracker")
- SKILL.md file (already created in `skills/` folder)
- API endpoint URL (your Railway URL + `/tcg/price`)
- Pricing (must match Stripe products)
- Description & screenshots

### 9.3 Test on ClawHub Staging

- [ ] Install skill in OpenClaw staging environment
- [ ] Test workflow: Create key on ClawHub → Use API endpoint → Verify data returns
- [ ] Check that pricing works: free tier (limited requests) → paid tier (unlimited)

### 9.4 Submit for Review

- [ ] ClawHub team reviews for:
  - API stability
  - Response time < 2 seconds avg
  - Error rate < 1%
  - Pricing competitive
  - Documentation clarity
- [ ] Once approved, skills go live on marketplace

---

## 🎉 10. Post-Launch Monitoring

### 10.1 First 24 Hours

- [ ] Monitor error logs every hour
- [ ] Check response times (should be <500ms avg)
- [ ] Verify webhook events arriving (1-2 new users expected)
- [ ] Confirm email delivery if enabled

### 10.2 First Week

- [ ] Monitor API usage across all 5 skills
- [ ] Check for any rate-limit abuse patterns
- [ ] Track user onboarding completions
- [ ] Respond to any support emails

### 10.3 Ongoing

- [ ] Weekly: Review error logs
- [ ] Monthly: Check performance metrics, update if needed
- [ ] Quarterly: A/B test pricing, review feature requests

---

## 📋 Rollback Plan

If issues occur post-deploy:

### Emergency Rollback (< 5 min)

```bash
# Option 1: Revert to previous Railway deployment
railway rollback

# Option 2: Take down API immediately
railway down

# Option 3: Disable all webhooks in Stripe dashboard (prevents new keys from being created)
```

---

## ⚠️ Blocking Issues (Stop & Fix Before Launch)

- [ ] Stripe keys not set → All transactions fail
- [ ] SAM.gov API key missing → Contracts skill returns mock data only
- [ ] Database connection fails → 500 errors on every request
- [ ] Webhook secret wrong → Keys not provisioned to users
- [ ] VPS domain not resolving → Can't reach API from internet

If any of these occur, stop immediately and fix before proceeding to production.

---

## Final Sign-Off

Before declaring the backend "ready for live":

- [ ] All 40+ tests pass locally AND on VPS
- [ ] Smoke tests pass on live VPS (all endpoints return 200/429 as expected)
- [ ] Rate limiting works (101st request returns 429)
- [ ] Stripe webhooks configured and tested
- [ ] Database migrations applied
- [ ] Error logs clean (no unhandled exceptions)
- [ ] All 6 configuration values provided and verified
- [ ] Email delivery tested (if enabled)
- [ ] Team has access to Firebase/Datadog for monitoring
- [ ] Support contact (nick@5cypress.com) updated
- [ ] Incident response plan documented

Once all sign-offs complete, skills are ready for ClawHub marketplace publication.

---

**Deployment Checklist Version:** 1.0
**Last Updated:** 2025-01-15
**Questions:** nick@5cypress.com
