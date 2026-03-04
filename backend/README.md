# 5 Cypress ClawHub Backend — Documentation Index

**Choose your entry point below based on what you need right now.**

---

## 🎯 Quick Start (Pick One)

### ⚡ I Just Want to Run It Locally (5 min)
**→ Read:** [START_HERE.md](START_HERE.md) → "Quick Start" section

**What you'll learn:** How to install, start server, create test key, call endpoints

**Expected outcome:** Server running on http://localhost:8000, one successful API call

---

### 🧪 I Want to Run the Full Test Suite (3 min)
**→ Read:** [START_HERE.md](START_HERE.md) → "Quick Start" section, then [TEST_OVERVIEW.md](TEST_OVERVIEW.md) → "Test Execution Quick Start"

**What you'll learn:** How to run 80+ automated tests, interpret results, coverage metrics

**Expected outcome:** `pytest tests/ -v` shows 40+ passed tests in <3 seconds

---

### 🚀 I'm Ready to Deploy to Production (30 min)
**→ Follow:** [DEPLOYMENT.md](DEPLOYMENT.md) in exact order (10 sections)

**What you'll learn:**
1. 6 required configuration values (Stripe, domain, SAM.gov API key)
2. How to create `.env.production` file
3. Step-by-step Railway deployment
4. Stripe webhook configuration
5. Smoke tests to verify live VPS
6. Rollback procedures

**Expected outcome:** Live API at https://api.5cypress.com with all 5 skills functional

---

### 📚 I Want to Understand the Codebase (30 min)
**→ Read in order:**
1. [START_HERE.md](START_HERE.md) → "What You Have" + "Project Structure" sections
2. [START_HERE.md](START_HERE.md) → "How Each Skill Works" section
3. [TEST_OVERVIEW.md](TEST_OVERVIEW.md) → "Test Coverage by Module" section
4. Look at actual code: `routers/tcg.py` (simplest), `routers/onboarding.py` (most complex)

**What you'll learn:** Overall architecture, how each skill works, where tests are

**Expected outcome:** Can navigate code, understand flow, modify endpoints

---

### 🎪 I'm Publishing to ClawHub Marketplace (2 hours)
**→ Prerequisites first:** Live VPS from DEPLOYMENT.md, then proceed
**→ Read:**
1. `skills/*/SKILL.md` files (understand ClawHub format)
2. [START_HERE.md](START_HERE.md) → "Path 3: Publish to ClawHub" section

**What you'll learn:** What goes in SKILL.md, marketplace requirements, testing in staging

**Expected outcome:** Live skills on ClawHub marketplace, accepting Stripe payments

---

## 📖 Full Documentation Map

### Master Overview
| Document | Length | Purpose | When to Read |
|----------|--------|---------|--------------|
| **START_HERE.md** | 30 min | Master overview, architecture, quick start | **First** — before anything else |
| **DELIVERY_SUMMARY.md** | 10 min | What was delivered, final stats | After understanding architecture |

### Operational Guides
| Document | Length | Purpose | When to Read |
|----------|--------|---------|--------------|
| **TESTING.md** | 45 min | 10-phase testing playbook with cURL examples | Before deploying anywhere |
| **DEPLOYMENT.md** | 60 min | Step-by-step production checklist (6 config sections) | Before going live |
| **TEST_OVERVIEW.md** | 30 min | Test suite analysis, coverage, CI/CD patterns | Understanding test infrastructure |

### Reference
| Document | Length | Purpose | When to Read |
|----------|--------|---------|--------------|
| **This file** | 5 min | Documentation index, navigation guide | Now (you're reading it) |
| **SKILL.md files** (5) | 5 min each | ClawHub marketplace specifications | Before publishing |
| **README.md** | 5 min | Project overview (if exists) | Optional background |

---

## 🎓 Learning Paths

### Path A: Developer (Understanding the Code)

1. [START_HERE.md](START_HERE.md#-what-you-have) — Project structure
2. Look at `routers/tcg.py` — Simplest skill implementation (320 LOC)
3. [TEST_OVERVIEW.md](TEST_OVERVIEW.md#-tcg-skill-testpy--6-tests) — How TCG is tested
4. Look at `routers/onboarding.py` — Most complex skill (280 LOC, strictest validation)
5. Look at `main.py` — FastAPI structure, middleware, error handling

**Outcome:** Can modify endpoints, add validation, understand request flow

---

### Path B: DevOps (Deployment & Operations)

1. [START_HERE.md](START_HERE.md#-three-paths-forward) — Overview of 3 deployment options
2. [DEPLOYMENT.md](DEPLOYMENT.md#-1-collect-required-configuration-values) — Collect 6 config values
3. [DEPLOYMENT.md](DEPLOYMENT.md#-2-update-environment-variables) — Create .env.production
4. [DEPLOYMENT.md](DEPLOYMENT.md#-4-deploy-to-railway) — Deploy to VPS
5. [DEPLOYMENT.md](DEPLOYMENT.md#-7-production-smoke-tests) — Verify live API

**Outcome:** API running on live VPS, Stripe webhooks working, monitoring in place

---

### Path C: QA (Testing & Validation)

1. [START_HERE.md](START_HERE.md#-quick-start-5-minutes) — Local setup
2. [TESTING.md](TESTING.md#phase-1-environment-setup-5-min) — Phase 1-2: Setup & start server
3. [TESTING.md](TESTING.md#phase-3-get-test-api-key-2-min) — Phase 3: Get test key
4. [TESTING.md](TESTING.md#phase-5-individual-skill-tests-15-min) — Phase 5: Test each endpoint manually
5. [TESTING.md](TESTING.md#phase-6-run-full-test-suite-3-min) — Phase 6: Run full pytest suite

**Outcome:** Verified all endpoints work, know how to test before deploy

---

### Path D: Marketer (Publishing & Monetization)

1. [START_HERE.md](START_HERE.md#-how-each-skill-works) — Understand what each skill does
2. [DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md#-revenue-model) — Revenue potential & pricing
3. [START_HERE.md](START_HERE.md#path-3-publish-to-clawhub-next-month) — ClawHub publication steps
4. `skills/*/SKILL.md` files — What goes on marketplace
5. [DEPLOYMENT.md](DEPLOYMENT.md#-6-configure-stripe-webhook) — Stripe setup for payments

**Outcome:** Ready to list skills on marketplace, understand revenue model

---

## 🔍 Find What You Need

### "I need to fix a bug"
→ [TESTING.md](TESTING.md#debugging-failed-tests) → "Debugging Failed Tests" section

### "I need to add a new skill"
→ [START_HERE.md](START_HERE.md#-common-tasks) → "Need to add a new skill?" section

### "Tests are failing locally"
→ [TESTING.md](TESTING.md#troubleshooting) → "Troubleshooting" section

### "Deployment is stuck"
→ [DEPLOYMENT.md](DEPLOYMENT.md#-10-rollback-plan) → "Rollback plan" section

### "I need to understand rate limiting"
→ [START_HERE.md](START_HERE.md#-how-auth-works) → "How Auth Works" section

### "I don't have the 6 config values"
→ [DEPLOYMENT.md](DEPLOYMENT.md#-1-collect-required-configuration-values) → Section 1 (step-by-step)

### "Baseball endpoint is timing out"
→ [START_HERE.md](START_HERE.md#-important-gotchas) → Gotcha #1

### "Onboarding key won't work twice"
→ [START_HERE.md](START_HERE.md#-important-gotchas) → Gotcha #2 (one-time use by design)

---

## ⏱️ Time Estimates

### Reading/Understanding
- START_HERE.md: 30 min
- Architecture: 30 min
- One skill implementation: 20 min

### Execution
- Local setup & tests: 10 min
- Full test suite: 5 min
- Deployment playbook: 40 min
- VPS smoke tests: 10 min
- ClawHub publishing: 2 hours

### Total: ~5 hours to go from code to live production + marketplace

---

## ✅ Verification Checklist

After reading docs and before executing:

- [ ] I understand the 3-layer architecture (directives → orchestration → execution)
- [ ] I know the 5 skills and what each one does
- [ ] I can run tests locally (`pytest tests/ -v`)
- [ ] I know what the 6 config values are
- [ ] I can describe the Stripe integration (keys provisioned on subscription.created)
- [ ] I understand rate limiting (100 req/min global, 10 req/min for /stripe)
- [ ] I know why baseball endpoint may timeout locally (network I/O)
- [ ] I can explain why onboarding key is one-time use (purchase model)

If you can check all 8 → You're ready to deploy!

---

## 🆘 Getting Help

**Problem:** I'm stuck on [specific step]

**Solution:**
1. Find the step in the relevant doc (above)
2. Read the "Troubleshooting" section of that doc
3. Check inline code comments for context
4. Try the suggested fix
5. If still stuck → contact nick@5cypress.com

**When messaging for help, include:**
- Document you were reading
- Exact error message (from terminal or response)
- What step you were on
- What you expected vs. what happened

---

## 📊 File Organization

```
backend/
├── 📖 START_HERE.md              ← Read this FIRST
├── 📋 TESTING.md                 ← Before any deployment
├── 🚀 DEPLOYMENT.md              ← For going live
├── 📚 TEST_OVERVIEW.md           ← Test suite details
├── 📦 DELIVERY_SUMMARY.md        ← What was delivered
├── 📑 THIS_FILE                  ← You are here
│
├── 💻 Code
│   ├── main.py                   (FastAPI app)
│   ├── auth.py                   (authentication)
│   ├── db.py                     (database)
│   ├── routers/                  (5 skills)
│   └── validators.py             (input validation)
│
├── 🧪 Tests
│   ├── tests/conftest.py        (fixtures)
│   ├── tests/test_auth.py       (auth tests)
│   └── tests/test_*.py          (skill tests)
│
├── 🎪 Skills (for marketplace)
│   ├── skills/tcg-price-tracker/SKILL.md
│   ├── skills/osha-monitor/SKILL.md
│   ├── skills/federal-contracts/SKILL.md
│   ├── skills/baseball-sabermetrics/SKILL.md
│   └── skills/ai-onboarding-kit/SKILL.md
│
├── 🛠️ Deployment
│   ├── Dockerfile
│   ├── Procfile
│   ├── railway.toml
│   ├── requirements.txt
│   └── .env.example
│
└── 📜 Scripts
    ├── scripts/test-local.sh     (cURL tests)
    └── scripts/load-test.js      (K6 performance test)
```

---

## 🎯 Your Next Action

**Stop reading and do ONE of these:**

1. **If this is your first time:** 
   → Read [START_HERE.md](START_HERE.md) (30 minutes)

2. **If you want to test:**
   → Follow [TESTING.md](TESTING.md) Phase 1-4 (15 minutes to running tests)

3. **If you're deploying:**
   → Follow [DEPLOYMENT.md](DEPLOYMENT.md) Section 1 (collect config values)

4. **If you're debugging:**
   → Check the troubleshooting section in the relevant doc (5 minutes)

---

**Version:** 1.0
**Last Updated:** January 15, 2025
**Total Documentation:** ~10,000 words across 6 files
**Status:** ✅ Complete & ready to use
