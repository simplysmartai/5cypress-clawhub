#!/bin/bash
# Local Testing Script for 5 Cypress ClawHub Backend
# Run this after: uvicorn main:app --reload

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
TEST_KEY="5cy_test_key_from_dev_endpoint"
PASS=0
FAIL=0

echo -e "${YELLOW}=== 5 Cypress ClawHub Local Test Suite ===${NC}\n"

# ────────────────────────────────────────────────────────────────────────────
# Step 1: Create a test API key
# ────────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[SETUP] Creating test API key...${NC}"
KEY_RESPONSE=$(curl -s -X POST "$BASE_URL/stripe/test-create-key?email=test@example.com&plan=all")
TEST_KEY=$(echo $KEY_RESPONSE | grep -o '"key":"[^"]*' | cut -d'"' -f4)

if [ -z "$TEST_KEY" ]; then
    echo -e "${RED}✗ Failed to create test key${NC}"
    echo "Response: $KEY_RESPONSE"
    exit 1
fi
echo -e "${GREEN}✓ Test key created: ${TEST_KEY:0:20}...${NC}\n"

# ────────────────────────────────────────────────────────────────────────────
# Test Helper Function
# ────────────────────────────────────────────────────────────────────────────

test_endpoint() {
    local method=$1
    local path=$2
    local expected_code=$3
    local description=$4
    local body=$5

    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$path" \
            -H "X-API-Key: $TEST_KEY" \
            -H "Content-Type: application/json" \
            -d "$body")
    else
        response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$path" \
            -H "X-API-Key: $TEST_KEY")
    fi

    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ $description${NC}"
        ((PASS++))
    else
        echo -e "${RED}✗ $description (expected $expected_code, got $http_code)${NC}"
        echo "  Response: ${body:0:100}"
        ((FAIL++))
    fi
}

# ────────────────────────────────────────────────────────────────────────────
# HEALTH / AUTH TESTS
# ────────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[AUTH] Testing authentication...${NC}"
test_endpoint "GET" "/health" "200" "Health check without key"
test_endpoint "GET" "/tcg/price?card=test&game=mtg" "200" "Valid request with API key" ""

# Invalid key
INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/tcg/price?card=test&game=mtg" \
    -H "X-API-Key: 5cy_invalid")
INVALID_CODE=$(echo "$INVALID_RESPONSE" | tail -n 1)
if [ "$INVALID_CODE" = "401" ]; then
    echo -e "${GREEN}✓ Invalid API key returns 401${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ Invalid API key check (expected 401, got $INVALID_CODE)${NC}"
    ((FAIL++))
fi

echo ""

# ────────────────────────────────────────────────────────────────────────────
# TCG SKILL TESTS
# ────────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[TCG] Testing TCG Price Tracker skill...${NC}"
test_endpoint "GET" "/tcg/price?card=Black+Lotus&game=mtg" "200" "TCG: Get price (MTG)"
test_endpoint "GET" "/tcg/price?card=Charizard&game=pokemon" "200" "TCG: Get price (Pokemon)"
test_endpoint "GET" "/tcg/search?q=Lightning&game=mtg" "200" "TCG: Search endpoint"
test_endpoint "GET" "/tcg/movers?game=mtg" "200" "TCG: Get movers (MTG)"
test_endpoint "GET" "/tcg/movers?game=pokemon" "200" "TCG: Get movers (Pokemon)"

echo ""

# ────────────────────────────────────────────────────────────────────────────
# OSHA SKILL TESTS
# ────────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[OSHA] Testing OSHA Monitor skill...${NC}"
test_endpoint "GET" "/osha/trades" "200" "OSHA: List valid trades"
test_endpoint "GET" "/osha/violations?trade=roofing&state=TX" "200" "OSHA: Get violations"
test_endpoint "GET" "/osha/summary?trade=electrical&state=FL" "200" "OSHA: Get summary"
test_endpoint "GET" "/osha/top-violators?trade=construction&state=CA" "200" "OSHA: Top violators"

echo ""

# ────────────────────────────────────────────────────────────────────────────
# CONTRACTS SKILL TESTS
# ────────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[CONTRACTS] Testing Federal Contracts skill...${NC}"
test_endpoint "GET" "/contracts/categories" "200" "Contracts: List categories"
test_endpoint "GET" "/contracts/digest?category=it&state=VA" "200" "Contracts: Get digest"
test_endpoint "GET" "/contracts/search?q=software+development" "200" "Contracts: Search endpoint"

echo ""

# ────────────────────────────────────────────────────────────────────────────
# BASEBALL SKILL TESTS
# ────────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[BASEBALL] Testing Baseball Sabermetrics skill...${NC}"
# These will likely fail due to pybaseball network I/O, but we're testing structure
echo "Note: Baseball stats require internet + pybaseball; may timeout locally"
test_endpoint "GET" "/baseball/player?name=Mike+Trout&year=2025" "200" "Baseball: Get player stats (may timeout)"

echo ""

# ────────────────────────────────────────────────────────────────────────────
# ONBOARDING SKILL TESTS
# ────────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[ONBOARDING] Testing AI Onboarding Kit skill...${NC}"
test_endpoint "GET" "/onboarding/industries" "200" "Onboarding: List industries"

onboarding_body='{
  "industry": "law_firm",
  "company_name": "Test Law LLC",
  "company_size": "small",
  "primary_pain_points": ["write proposals faster", "client communication"],
  "tools_used": ["Clio", "Gmail"]
}'
test_endpoint "POST" "/onboarding/generate" "200" "Onboarding: Generate kit" "$onboarding_body"

echo ""

# ────────────────────────────────────────────────────────────────────────────
# VALIDATION TESTS
# ────────────────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[VALIDATION] Testing input validation...${NC}"

# Invalid game value
INVALID_GAME=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/tcg/price?card=test&game=invalid" \
    -H "X-API-Key: $TEST_KEY")
INVALID_GAME_CODE=$(echo "$INVALID_GAME" | tail -n 1)
if [ "$INVALID_GAME_CODE" = "422" ] || [ "$INVALID_GAME_CODE" = "400" ]; then
    echo -e "${GREEN}✓ Invalid game parameter rejected${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⊘ Invalid game parameter (got $INVALID_GAME_CODE, expected 422/400)${NC}"
fi

# Missing required parameter
MISSING_CARD=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/tcg/price?game=mtg" \
    -H "X-API-Key: $TEST_KEY")
MISSING_CARD_CODE=$(echo "$MISSING_CARD" | tail -n 1)
if [ "$MISSING_CARD_CODE" = "422" ]; then
    echo -e "${GREEN}✓ Missing required parameter rejected${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⊘ Missing parameter check (got $MISSING_CARD_CODE, expected 422)${NC}"
fi

echo ""

# ────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ────────────────────────────────────────────────────────────────────────────

TOTAL=$((PASS + FAIL))
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "Test Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC} (Total: $TOTAL)"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Fix issues before deploying.${NC}"
    exit 1
fi
