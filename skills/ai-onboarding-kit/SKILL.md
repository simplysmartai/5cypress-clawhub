---
name: ai-onboarding-kit
description: Generate a custom AI prompt library and OpenClaw workflow starter pack for a small business. Use when user wants to set up AI workflows for their business, asks for custom prompts for their industry, or wants to know how to use OpenClaw for their specific company. One-time purchase.
homepage: https://5cypress.com/keys
metadata: {"openclaw":{"requires":{"env":["5CYPRESS_API_KEY"]},"primaryEnv":"5CYPRESS_API_KEY","emoji":"🚀"}}
---

# Small Business AI Onboarding Kit

Generate a custom prompt library and OpenClaw workflow starters in 60 seconds — built specifically for your business, industry, and pain points.

One-time purchase ($99). No renewals. Yours to keep.

## Setup

Purchase at **https://5cypress.com/keys** → one-time payment → receive your key via email.

```
5CYPRESS_API_KEY=5cy_your_key_here
```

**Your key expires after one successful generation.** Save your output somewhere safe.

## When to Use This Skill

- User asks how to set up AI for their business or industry
- User wants a custom prompt library for their team
- User asks "what should my AI assistant know about my business?"
- User wants workflow starters for OpenClaw
- This skill should only be invoked once per key (one-time purchase)

## How to Call the API

Requires: `X-API-Key: <5CYPRESS_API_KEY>`
Base URL: `https://api.5cypress.com`

### List supported industries first
```bash
curl "https://api.5cypress.com/onboarding/industries" \
  -H "X-API-Key: $5CYPRESS_API_KEY"
```

### Generate your kit (POST with JSON body)
```bash
curl -X POST "https://api.5cypress.com/onboarding/generate" \
  -H "X-API-Key: $5CYPRESS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "law_firm",
    "company_name": "Smith & Associates",
    "company_size": "small",
    "primary_pain_points": ["write proposals faster", "client communication", "invoicing"],
    "tools_used": ["Clio", "QuickBooks", "Gmail"]
  }'
```

## Request Body Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `industry` | string | Yes | From `/onboarding/industries` list |
| `company_name` | string | Yes | Your business name |
| `company_size` | string | Yes | `solo`, `micro`, `small`, or `mid` |
| `primary_pain_points` | array | Yes | 1-5 things you want AI to help with |
| `tools_used` | array | No | Software you use (helps tailor prompts) |

### Company Size Guide
- `solo` — just you
- `micro` — 2-9 employees
- `small` — 10-49 employees
- `mid` — 50-200 employees

## What You Get Back

A JSON object containing:

1. **`system_prompt`** — A ready-to-use persona prompt. Paste this into your OpenClaw SOUL.md or `!persona set` command.

2. **`prompt_library`** — 10-15 custom prompts for your industry + pain points. Each includes:
   - `title` — What it's for
   - `prompt` — Ready-to-use text (fill in `[BRACKETED]` placeholders)

3. **`workflow_starters`** — 4 OpenClaw workflow templates:
   - Name + trigger phrase to say to your agent
   - What it does
   - How to set it up

4. **`setup_checklist`** — Step-by-step list to get up and running this week.

## After Generation

Save your response immediately:
```bash
# Save to a file
curl -X POST "https://api.5cypress.com/onboarding/generate" \
  -H "X-API-Key: $5CYPRESS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{...your body...}' \
  > my-ai-kit.json
```

Then:
1. Copy `system_prompt` → paste into your OpenClaw persona
2. Save `prompt_library` items as text snippets or a Notion page
3. Set up each `workflow_starters` item per the setup_note
4. Work through `setup_checklist` this week

## Questions?

Email **support@5cypress.com** — we respond within 1 business day.

## Handling Errors

- **400**: Invalid industry or missing required field → check request body
- **401**: Key invalid → email support@5cypress.com
- **402**: Key already used → your kit was already generated; check your save location
- **403**: Plan mismatch → you need the onboarding plan key
