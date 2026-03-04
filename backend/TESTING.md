# 5 Cypress ClawHub Backend — Local Testing Playbook

**Purpose:** This document walks you through testing the 5 ClawHub skills locally before VPS deployment.

**Duration:** ~30 minutes for a full test cycle
**Tools needed:** curl, Python 3.12+, git, bash (Windows users: use WSL or Git Bash)

---

## Phase 1: Environment Setup (5 min)

### 1.1 Clone the repository

```bash
cd c:\Users\smart\OneDrive\Documents\Side Gig\n8n\websites
git clone https://github.com/5cypress/5cypress-clawhub.git
cd 5cypress-clawhub/backend
```

### 1.2 Create Python virtual environment

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux (bash)
python3 -m venv venv
source venv/bin/activate
```

### 1.3 Install dependencies

```bash
pip install -r requirements.txt
```

Expected output: 18 packages installed (fastapi, uvicorn, pydantic, stripe, httpx, slowapi, pytest, pytest-asyncio, pybaseball, beautifulsoup4, lxml, cachetools, python-dotenv, tenacity, aiosqlite, etc.)

### 1.4 Create test environment file

```bash
cp .env.example .env.test
```

Edit `.env.test` and set these values:

```
ENVIRONMENT=development
PORT=8000
DATABASE_URL=sqlite:///./test.db
STRIPE_SECRET_KEY=sk_test_placeholder_for_tests
STRIPE_WEBHOOK_SECRET=whsec_test_placeholder
SAM_GOV_API_KEY=test_key_or_empty
RESEND_API_KEY=test_key_or_empty
VPS_BASE_URL=http://localhost:8000
```

### 1.5 Verify Python imports

```bash
python -c "from main import app; print('✓ All imports successful')"
```

Expected: `✓ All imports successful`

---

## Phase 2: Start Local Server (2 min)

### 2.1 Run the FastAPI server

```bash
# In new terminal
uvicorn main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### 2.2 Verify server is running

In a separate terminal:

```bash
curl http://localhost:8000/health -s | jq .
```

Expected response:
```json
{
  "status": "running",
  "version": "1.0.0",
  "timestamp": "2025-01-15T14:32:45.123456Z",
  "ok": true,
  "source": "api",
  "cached": false
}
```

---

## Phase 3: Get Test API Key (2 min)

Generate a test API key that bypasses Stripe validation:

```bash
response=$(curl -s -X POST "http://localhost:8000/stripe/test-create-key?email=test@example.com&plan=all")
TEST_KEY=$(echo "$response" | jq -r '.data.key')
echo "Test key: $TEST_KEY"
```

Example output:
```
Test key: 5cy_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5
```

**Save this key—you'll use it for all endpoint tests.**

---

## Phase 4: Auth & Middleware Tests (3 min)

### 4.1 Test missing API key (should fail)

```bash
curl -s http://localhost:8000/tcg/price?card=Black+Lotus&game=mtg | jq .
```

Expected: 401 error with message about missing X-API-Key header

```json
{
  "ok": false,
  "error": "Unauthorized",
  "hint": "Missing or invalid X-API-Key header. Get a key at https://5cypress.com/keys"
}
```

### 4.2 Test invalid API key (should fail)

```bash
curl -s -H "X-API-Key: invalid_key" http://localhost:8000/tcg/price?card=Black+Lotus&game=mtg | jq .
```

Expected: 401 error (same as above)

### 4.3 Test valid API key (should pass)

```bash
curl -s -H "X-API-Key: $TEST_KEY" http://localhost:8000/health | jq .
```

Expected: 200 with health data

### 4.4 Test request ID header

```bash
curl -si -H "X-API-Key: $TEST_KEY" http://localhost:8000/health | grep "X-Request-ID"
```

Expected:
```
X-Request-ID: a1234567-b890-c123-d456-e78901f23g45
```

---

## Phase 5: Individual Skill Tests (15 min)

All commands assume `$TEST_KEY` is set. If not, re-run Phase 3.

### 5.1 TCG Price Tracker Skill

**Test 1: Get card price (MTG)**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/tcg/price?card=Black+Lotus&game=mtg" | jq .
```

Expected: 200 with price data or cached price

**Test 2: Search cards**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/tcg/search?q=Lightning+Bolt&game=mtg" | jq .
```

Expected: 200 with list of matching cards and prices

**Test 3: Get trending cards (movers)**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/tcg/movers?game=pokemon" | jq '.data[0:3]'
```

Expected: 200 with top 3 trending cards

**Test 4: Invalid game parameter (should fail)**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/tcg/price?card=test&game=invalid" | jq .
```

Expected: 422 validation error

### 5.2 OSHA Monitor Skill

**Test 1: List all trades**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/osha/trades" | jq '.data[0:5]'
```

Expected: 200 with list of 5+ trade categories

**Test 2: Get violations by trade and state**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/osha/violations?trade=roofing&state=TX" | jq '.data[0:2]'
```

Expected: 200 with recent violations (may be empty if no data)

**Test 3: Get summary stats**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/osha/summary?trade=electrical" | jq .
```

Expected: 200 with aggregate stats (total_violations, avg_penalty, top_states)

**Test 4: Get top violators**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/osha/top-violators?trade=construction&state=CA" | jq '.data[0:3]'
```

Expected: 200 with companies ranked by penalty amount

**Test 5: Missing state parameter (should fail)**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/osha/violations?trade=roofing" | jq .
```

Expected: 422 validation error

### 5.3 Federal Contracts Skill

**Test 1: List categories**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/contracts/categories" | jq '.data[0:5]'
```

Expected: 200 with 5+ contract categories (IT, construction, cybersecurity, etc.)

**Test 2: Get contract opportunities (digest)**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/contracts/digest?category=it&state=VA" | jq . | head -20
```

Expected: 200 with active contract opportunities (or mock data if SAM.gov key not set)

**Test 3: Search by keyword**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/contracts/search?q=software+development" | jq '.data[0:2]'
```

Expected: 200 with matching contracts

**Test 4: Missing category parameter (should fail)**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/contracts/digest?state=VA" | jq .
```

Expected: 422 validation error

### 5.4 Baseball Sabermetrics Skill

**Test 1: Get player stats**

```bash
curl -s --max-time 30 -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/baseball/player?name=Mike+Trout&year=2024" | jq . | head -20
```

**Expected:** May timeout (30s limit) or return 200 with FanGraphs stats (wRC+, BABIP, ISO, etc.). This skill requires network I/O to FanGraphs.

**Note:** If timeout occurs locally, it's expected. The skill will work faster on a VPS with better network.

**Test 2: List multiple players (digest)**

```bash
curl -s --max-time 30 -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/baseball/digest?names=Ohtani,Judge,Acuna&year=2024" | jq . | head -20
```

**Expected:** Same as Test 1; may timeout locally.

**Test 3: Too many players (should fail)**

```bash
names=$(echo "Player{1..13}" | tr ' ' ',')
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/baseball/digest?names=$names&year=2024" | jq .
```

Expected: 422 validation error (max 12 players)

### 5.5 AI Onboarding Kit Skill

**Test 1: List supported industries**

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/onboarding/industries" | jq '.data[0:10]'
```

Expected: 200 with 10+ industries (Medical Practice, Law Firm, Construction, etc.)

**Test 2: Generate onboarding kit**

```bash
curl -s -X POST -H "X-API-Key: $TEST_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "Medical Practice",
    "company_name": "Bright Health Clinic",
    "company_size": "small",
    "primary_pain_points": ["appointment scheduling", "patient communication"],
    "tools_used": ["EHR", "Stripe"]
  }' \
  "http://localhost:8000/onboarding/generate" | jq . | head -30
```

Expected: 200 with full AI kit (system_prompt, prompt_library, workflow_starters, setup_checklist)

**⚠️ Warning:** This key may be one-time use. If you get 402 on second request, generate a new test key.

**Test 3: Invalid industry (should fail)**

```bash
curl -s -X POST -H "X-API-Key: $TEST_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "MD",
    "company_name": "Test Inc",
    "company_size": "small",
    "primary_pain_points": ["issue"],
    "tools_used": []
  }' \
  "http://localhost:8000/onboarding/generate" | jq .
```

Expected: 422 validation error (industry min 5 chars)

**Test 4: Too many pain points (should fail)**

```bash
curl -s -X POST -H "X-API-Key: $TEST_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "Medical Practice",
    "company_name": "Test Clinic",
    "company_size": "small",
    "primary_pain_points": ["p1", "p2", "p3", "p4", "p5", "p6"],
    "tools_used": []
  }' \
  "http://localhost:8000/onboarding/generate" | jq .
```

Expected: 422 validation error (max 5 pain points)

---

## Phase 6: Run Full Test Suite (3 min)

### 6.1 Run all tests with pytest

```bash
# In a third terminal (server should still be running)
pytest tests/ -v --tb=short
```

Expected output:
```
tests/test_auth.py::test_health_endpoint PASSED
tests/test_auth.py::test_missing_api_key PASSED
tests/test_auth.py::test_invalid_api_key PASSED
...
tests/test_osha.py::test_trades_list_valid PASSED
...
tests/test_contracts.py::test_categories_list_valid PASSED
...
tests/test_baseball.py::test_player_valid_name SKIPPED  (network timeout expected locally)
...
tests/test_onboarding.py::test_industries_list_valid PASSED
...

======================== 40 passed, 2 skipped in 2.34s ========================
```

### 6.2 Run tests with coverage report

```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html  # macOS
# or
start htmlcov/index.html  # Windows
```

Look for >80% coverage on auth.py, main.py, and routers/*.py

---

## Phase 7: Rate Limiting Test (2 min)

### 7.1 Test rate limit (100 req/min global)

Send 101 requests in rapid succession:

```bash
for i in {1..101}; do
  curl -s -H "X-API-Key: $TEST_KEY" \
    "http://localhost:8000/health" > /dev/null
  if [ $((i % 20)) -eq 0 ]; then echo "Sent $i requests"; fi
done

# 101st request should get 429
curl -s -H "X-API-Key: $TEST_KEY" "http://localhost:8000/health" | jq .
```

Expected: Request 102 returns 429 with message:
```json
{
  "ok": false,
  "error": "Rate limit exceeded",
  "hint": "Max 100 requests per minute. Try again in 60 seconds."
}
```

---

## Phase 8: Error Case Testing (2 min)

### 8.1 Test invalid JSON body

```bash
curl -s -X POST -H "X-API-Key: $TEST_KEY" \
  -H "Content-Type: application/json" \
  -d '{bad json' \
  "http://localhost:8000/onboarding/generate" | jq .
```

Expected: 422 with JSON parsing error

### 8.2 Test missing required JSON field

```bash
curl -s -X POST -H "X-API-Key: $TEST_KEY" \
  -H "Content-Type: application/json" \
  -d '{"industry": "Medical"}' \
  "http://localhost:8000/onboarding/generate" | jq .
```

Expected: 422 with field validation error

### 8.3 Test nonexistent endpoint

```bash
curl -s -H "X-API-Key: $TEST_KEY" \
  "http://localhost:8000/nonexistent" | jq .
```

Expected: 404 with "Not Found" error

---

## Phase 9: Deploy Readiness Checklist

After all tests pass, verify these items:

✅ **Auth Layer:**
- [x] Missing X-API-Key returns 401
- [x] Invalid key returns 401
- [x] Valid key grants access
- [x] X-Request-ID header present on all responses

✅ **Input Validation:**
- [x] Missing required params return 422
- [x] Invalid enum values return 422
- [x] Too-long/too-short strings rejected
- [x] Non-numeric year fields rejected
- [x] List size constraints enforced (max 12 players, max 5 pain points)

✅ **Response Format:**
- [x] All responses have `ok`, `data/error`, `source`, `cached` fields
- [x] `source` is one of: "api", "cache", "mock"
- [x] Timestamps are ISO 8601 format
- [x] Error responses include `hint` field

✅ **Rate Limiting:**
- [x] 100 req/min global limit enforced
- [x] 10 req/min for /stripe webhook endpoint
- [x] 429 status code returned when exceeded
- [x] Clear error message indicates retry timing

✅ **Error Handling:**
- [x] Invalid JSON returns 422
- [x] Malformed requests return 400
- [x] Auth errors return 401
- [x] Payment/subscription errors return 402
- [x] Bad gateway/timeouts return 504
- [x] All errors logged with request_id

✅ **Skills Verified:**
- [x] TCG: price, search, movers endpoints working
- [x] OSHA: trades, violations, summary, top-violators working
- [x] Contracts: categories, digest, search working
- [x] Baseball: player, digest, leaders endpoints respond (may timeout locally)
- [x] Onboarding: industries, generate endpoints working

---

## Phase 10: Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'X'"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "Connection refused" on http://localhost:8000

**Solution:** Ensure server is running in another terminal:
```bash
uvicorn main:app --reload
```

### Issue: "Test key creation failed"

**Solution:** Ensure database is writable:
```bash
rm -f test.db
curl -X POST "http://localhost:8000/stripe/test-create-key?email=test@example.com&plan=all"
```

### Issue: Baseball endpoint times out locally

**Solution:** Expected behavior. FanGraphs data fetch takes 20-30 sec on local WiFi. On VPS with gigabit ethernet, <200ms typical. Use `--max-time 30` on curl to avoid premature timeouts.

### Issue: OSHA/Contracts return no data

**Solution:** 
- **OSHA:** Public data.dol.gov API may have rate limits or data lag. Try different trade/state combo.
- **Contracts:** If SAM_GOV_API_KEY not set, returns mock data (expected for development).

### Issue: Onboarding key shows 402 "Key already used"

**Solution:** Onboarding is one-time purchase. Generate a new test key:
```bash
curl -X POST "http://localhost:8000/stripe/test-create-key?email=test2@example.com&plan=all"
```

---

## Next Steps: Deploy to VPS

Once all tests in Phase 1-9 pass:

1. **Create Railway/Heroku account**
2. **Set production environment variables** in VPS config
3. **Update Stripe product IDs** in `stripe_webhooks.py` (get from Stripe dashboard)
4. **Register SAM.gov API key** (2 min at https://api.sam.gov)
5. **Create GitHub repo** and push code
6. **Deploy:** `git push railway main` or `git push heroku main`
7. **Run smoke test** on live VPS
8. **Publish to ClawHub** marketplace

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed VPS setup.

---

## Support

If tests fail:
1. Check error message and hint field
2. Look up error code in Phase 8 (Error Case Testing)
3. Run failing test in isolation: `pytest tests/test_tcg.py::test_invalid_game -v`
4. Check server logs in first terminal for detailed error stack trace
5. Contact: nick@5cypress.com with test output

---

**Test Suite Version:** 1.0 (Jan 2025)
**Last Updated:** 2025-01-15
**Coverage:** 40+ test cases across 5 skills + auth + middleware
