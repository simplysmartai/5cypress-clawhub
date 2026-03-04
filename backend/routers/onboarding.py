"""
Skill 5: Small Business AI Onboarding Kit
One-time purchase ($99). The VPS generates a custom prompt library
and workflow starter pack for the buyer's specific industry.

Endpoints:
  POST /onboarding/generate
  GET  /onboarding/industries  (list supported industries)

After generation, the key is marked as used (one-time).
The buyer receives a full JSON object they can copy into their OpenClaw.
"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import AuthenticatedKey, require_plan
from db import mark_key_used
from models import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()

SUPPORTED_INDUSTRIES = [
    "medical_practice", "dental_office", "law_firm", "real_estate",
    "accounting_cpa", "construction_contractor", "roofing", "plumbing",
    "electrical", "auto_repair", "restaurant", "retail_store",
    "ecommerce", "saas_startup", "marketing_agency", "consulting",
    "financial_advisory", "insurance_broker", "trucking_logistics",
    "home_services", "cleaning_service", "landscaping", "gym_fitness",
    "manufacturing", "staffing_agency",
]

COMPANY_SIZE_LABELS = {
    "solo": "solo operator (just you)",
    "micro": "micro business (2-9 employees)",
    "small": "small business (10-49 employees)",
    "mid": "mid-size business (50-200 employees)",
}


class OnboardingRequest(BaseModel):
    industry: str = Field(..., description="Industry slug from /onboarding/industries")
    company_name: str = Field(..., min_length=1, max_length=100)
    company_size: Literal["solo", "micro", "small", "mid"] = "small"
    primary_pain_points: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Top 1-5 pain points or goals, e.g. ['follow up with leads', 'write proposals faster']",
    )
    tools_used: list[str] = Field(
        default=[],
        description="Current tools, e.g. ['QuickBooks', 'HubSpot', 'Gmail']",
    )


def _build_prompt_library(req: OnboardingRequest) -> list[dict]:
    """Generate a custom prompt set based on industry + pain points."""
    industry_label = req.industry.replace("_", " ").title()
    size_label = COMPANY_SIZE_LABELS[req.company_size]
    tools = ", ".join(req.tools_used) if req.tools_used else "standard office tools"

    base_context = (
        f"You are an expert assistant for {req.company_name}, a {size_label} in the {industry_label} industry. "
        f"They use: {tools}. Always be concise, professional, and action-oriented."
    )

    # Industry-specific prompt packs
    INDUSTRY_PROMPTS: dict[str, list[dict]] = {
        "medical_practice": [
            {"title": "Patient Appointment Reminder", "prompt": f"{base_context}\n\nDraft a warm, professional appointment reminder message for a patient visiting tomorrow. Include: appointment time, location, what to bring, cancellation policy. Keep under 100 words."},
            {"title": "Insurance Denial Appeal Letter", "prompt": f"{base_context}\n\nWrite a medical insurance denial appeal letter for [PROCEDURE] denied for [PATIENT_ID]. The denial code is [CODE]. Be firm, professional, and cite medical necessity."},
            {"title": "Patient Feedback Response", "prompt": f"{base_context}\n\nRespond to this patient review: [REVIEW_TEXT]. Acknowledge their experience, address concerns without disclosing PHI, and invite them to contact the office directly."},
        ],
        "law_firm": [
            {"title": "Client Intake Summary", "prompt": f"{base_context}\n\nSummarize this client intake note into a structured case overview: [INTAKE_NOTES]. Include: matter type, key facts, immediate next steps, and statute of limitations if applicable."},
            {"title": "Demand Letter Draft", "prompt": f"{base_context}\n\nDraft a firm demand letter for [CLIENT] against [OPPOSING_PARTY] regarding [MATTER]. State the demand amount of [AMOUNT] and a response deadline of [DATE]."},
            {"title": "Research Memo Outline", "prompt": f"{base_context}\n\nCreate a legal research memo outline on [ISSUE] under [JURISDICTION] law. Include: question presented, short answer, applicable statutes, and case law starting points."},
        ],
        "construction_contractor": [
            {"title": "Project Estimate Email", "prompt": f"{base_context}\n\nWrite a professional estimate follow-up email for [CLIENT_NAME] for [PROJECT_TYPE]. The estimate total is $[AMOUNT] with a [X]-day timeline. Emphasize quality and our warranty."},
            {"title": "Subcontractor RFQ", "prompt": f"{base_context}\n\nWrite a request for quote (RFQ) to subcontractors for [TRADE] work on [PROJECT]. Include scope, site location [ADDRESS], bid deadline [DATE], and required certifications."},
            {"title": "Punch List Summary", "prompt": f"{base_context}\n\nConvert this voice note into a structured punch list: [VOICE_NOTE]. Group items by room/area, assign priority (critical/standard/cosmetic), and format for handoff to the crew."},
        ],
        "real_estate": [
            {"title": "Property Listing Description", "prompt": f"{base_context}\n\nWrite a compelling MLS listing description for this property: [PROPERTY_DETAILS]. Highlight: location, square footage, upgrades, lifestyle benefits. 150-200 words. No clichés."},
            {"title": "Offer Negotiation Script", "prompt": f"{base_context}\n\nCreate a negotiation talking points script for presenting an offer of $[AMOUNT] on [ADDRESS]. Counter-offer from seller is $[COUNTER]. Key leverage points: [POINTS]."},
            {"title": "Client Market Update", "prompt": f"{base_context}\n\nWrite a brief monthly market update email for past clients about [NEIGHBORHOOD]. Include: median prices, days on market, inventory levels. Keep it conversational and under 200 words."},
        ],
        "accounting_cpa": [
            {"title": "Engagement Letter Outline", "prompt": f"{base_context}\n\nCreate an engagement letter outline for [SERVICE_TYPE] services for [CLIENT_NAME] covering [TAX_YEAR]. Include: scope, fee estimate of $[AMOUNT], deadlines, and document requirements."},
            {"title": "Tax Planning Talking Points", "prompt": f"{base_context}\n\nPrepare year-end tax planning talking points for a [ENTITY_TYPE] client with revenue of $[REVENUE]. Highlight: [TOP_3_STRATEGIES] tailored to their situation."},
            {"title": "Client Onboarding Checklist", "prompt": f"{base_context}\n\nGenerate a new client onboarding checklist for a [ENTITY_TYPE] business. Include: documents to collect, system access needed, key deadlines, and initial questions to ask."},
        ],
    }

    # Get industry-specific pack, fallback to generic
    industry_pack = INDUSTRY_PROMPTS.get(req.industry, [])

    # Generic prompts based on pain points
    generic_prompts: list[dict] = []
    pain_map = {
        "follow up with leads": {
            "title": "Lead Follow-Up Sequence",
            "prompt": f"{base_context}\n\nWrite a 3-touch follow-up sequence for a lead who expressed interest in [SERVICE] but hasn't responded. Tone: persistent but not pushy. Channels: email, then text, then email. Space them 3 days apart.",
        },
        "write proposals faster": {
            "title": "Proposal Template Filler",
            "prompt": f"{base_context}\n\nFill in this proposal template for [CLIENT_NAME] for [SERVICE]. Context: [CONTEXT]. Output a complete, professional proposal section including executive summary, scope, timeline, pricing, and next steps.",
        },
        "save time on emails": {
            "title": "Email Response Drafts",
            "prompt": f"{base_context}\n\nRead this email and draft 3 response options (brief/detailed/decline): [EMAIL_CONTENT]. Label each option and keep the tone professional and friendly.",
        },
        "client communication": {
            "title": "Status Update Message",
            "prompt": f"{base_context}\n\nWrite a project status update for [CLIENT_NAME] for [PROJECT]. Current status: [STATUS]. Next milestone: [MILESTONE] by [DATE]. Include any blockers or needs from the client.",
        },
        "invoicing": {
            "title": "Invoice Follow-Up",
            "prompt": f"{base_context}\n\nWrite a polite but firm invoice follow-up for Invoice #[NUM] for $[AMOUNT] sent [DATE]. This is the [1st/2nd/3rd] reminder. Adjust tone accordingly.",
        },
        "social media": {
            "title": "Weekly Social Posts",
            "prompt": f"{base_context}\n\nCreate 3 LinkedIn posts for this week. Topic: [TOPIC]. Mix: 1 educational, 1 behind-the-scenes, 1 call-to-action. Each under 150 words, no hashtag spam.",
        },
        "hiring": {
            "title": "Job Posting",
            "prompt": f"{base_context}\n\nWrite a job posting for a [ROLE] position. Requirements: [REQUIREMENTS]. Salary range: [RANGE]. Emphasize company culture and growth opportunity. Keep under 400 words.",
        },
        "scheduling": {
            "title": "Meeting Prep Brief",
            "prompt": f"{base_context}\n\nCreate a meeting prep brief for an upcoming call with [CLIENT/PROSPECT]. Context: [CONTEXT]. Include: goals for the call, questions to ask, potential objections, and desired next steps.",
        },
    }

    for pain in req.primary_pain_points:
        pain_lower = pain.lower()
        for key, prompt_data in pain_map.items():
            if key in pain_lower or any(word in pain_lower for word in key.split()):
                generic_prompts.append(prompt_data)
                break
        else:
            # Fallback: create a general prompt for unmatched pain points
            generic_prompts.append({
                "title": f"Help with: {pain.title()}",
                "prompt": f"{base_context}\n\nI need help with: {pain}. Context: [CONTEXT]. Please provide a specific, actionable response that I can immediately use for {req.company_name}.",
            })

    all_prompts = industry_pack + generic_prompts
    # Deduplicate by title
    seen_titles = set()
    final = []
    for p in all_prompts:
        if p["title"] not in seen_titles:
            seen_titles.add(p["title"])
            final.append(p)

    return final[:15]  # Cap at 15 prompts


def _build_workflow_starters(req: OnboardingRequest) -> list[dict]:
    """Build OpenClaw workflow starters (SKILL.md-compatible trigger phrases)."""
    workflows = [
        {
            "name": "Weekly Digest",
            "trigger": f"Run my weekly {req.company_name} digest",
            "description": "Summarizes emails, flags urgent items, lists overdue tasks, and preps the day's priorities.",
            "setup_note": "Connect Gmail skill + Calendar skill first. Run every Monday at 8am via cron.",
        },
        {
            "name": "Lead Follow-Up",
            "trigger": "Follow up on leads from [SOURCE]",
            "description": "Pulls contacts from [CRM/SHEET], drafts personalized follow-up emails, logs activity.",
            "setup_note": f"Pair with {'HubSpot' if 'HubSpot' in req.tools_used else 'your CRM'} skill for automatic contact sync.",
        },
        {
            "name": "Document Generator",
            "trigger": "Create a [proposal/contract/invoice] for [CLIENT_NAME]",
            "description": "Uses your templates + client context to generate a draft document in 30 seconds.",
            "setup_note": "Store your templates in /documents folder. Connect Google Drive skill for auto-save.",
        },
        {
            "name": "Daily Briefing",
            "trigger": "Give me my morning briefing",
            "description": "Checks calendar, emails, and open tasks. Summarizes what needs your attention today.",
            "setup_note": "Set up a heartbeat cron at 7am. Deliver via Telegram or email.",
        },
    ]
    return workflows


@router.get("/industries", response_model=SuccessResponse)
async def list_industries():
    """Returns all supported industry slugs for the onboarding kit."""
    return SuccessResponse(
        data={"industries": SUPPORTED_INDUSTRIES},
        source="5cypress internal",
    )


@router.post("/generate", response_model=SuccessResponse)
async def generate_onboarding_kit(
    req: OnboardingRequest,
    auth: AuthenticatedKey = Depends(require_plan("onboarding")),
):
    """
    Generates a custom AI onboarding kit for a small business.
    Returns:
      - 10-15 custom prompts for their industry + pain points
      - 4 OpenClaw workflow starters
      - A system prompt template for their AI assistant
      - Setup checklist

    One-time use: key is deactivated after generation.
    """
    prompts = _build_prompt_library(req)
    workflows = _build_workflow_starters(req)

    industry_label = req.industry.replace("_", " ").title()
    tools = ", ".join(req.tools_used) if req.tools_used else "standard office tools"

    system_prompt = (
        f"You are {req.company_name}'s AI business assistant. "
        f"You specialize in supporting {industry_label} operations for a {COMPANY_SIZE_LABELS[req.company_size]}. "
        f"You have working knowledge of: {tools}. "
        f"Your priorities are: {', '.join(req.primary_pain_points)}. "
        f"Always respond concisely and professionally. When drafting documents, ask for missing details rather than making them up. "
        f"Default to {req.company_name}'s brand voice: professional, trustworthy, and client-focused."
    )

    setup_checklist = [
        f"[ ] Copy the system prompt into your OpenClaw SOUL.md or persona file",
        f"[ ] Install skills relevant to your tools: {', '.join(req.tools_used[:3]) if req.tools_used else 'Gmail, Calendar, Notion'}",
        f"[ ] Add your prompt library to a /prompts folder in your OpenClaw home directory",
        f"[ ] Set up a heartbeat cron for your Daily Briefing workflow",
        f"[ ] Test each workflow starter with a real example this week",
        f"[ ] Save this kit to a safe location — your key has been used (one-time purchase)",
    ]

    kit = {
        "company": req.company_name,
        "industry": req.industry,
        "generated_at": "2026-02-24",
        "system_prompt": system_prompt,
        "prompt_library": prompts,
        "workflow_starters": workflows,
        "setup_checklist": setup_checklist,
        "support": "Questions? Email support@5cypress.com",
    }

    # Mark key as used (one-time purchase — deactivate after delivery)
    await mark_key_used(auth.key, "/onboarding/generate")
    from db import deactivate_key_by_email
    await deactivate_key_by_email(auth.email)

    return SuccessResponse(
        data=kit,
        source="5 Cypress AI Onboarding Engine",
    )
