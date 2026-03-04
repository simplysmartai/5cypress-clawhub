"""
Stripe webhook handler.
Listens for subscription events and automatically activates/deactivates API keys.

Stripe products map to plans:
  - prod_tcg         → plan="tcg"
  - prod_osha        → plan="osha"
  - prod_contracts   → plan="contracts"
  - prod_baseball    → plan="baseball"
  - prod_onboarding  → plan="onboarding"  (one-time price)

Set STRIPE_PRODUCT_PLAN_MAP in your Stripe metadata:
  On each Product, add metadata key: clawhub_plan = <plan_name>
"""

import os
import logging
import stripe
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from db import create_api_key, deactivate_key_by_subscription

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Optional: hardcode product → plan if you don't use metadata
PRODUCT_PLAN_MAP: dict[str, str] = {}

router = APIRouter()


def _plan_from_event(event_data: dict) -> str:
    """Extract plan name from Stripe subscription/payment intent data."""
    # Try subscription items
    try:
        items = event_data["object"]["items"]["data"]
        for item in items:
            price_id = item["price"]["id"]
            product_id = item["price"]["product"]
            product = stripe.Product.retrieve(product_id)
            plan = product.get("metadata", {}).get("clawhub_plan")
            if plan:
                return plan
            if product_id in PRODUCT_PLAN_MAP:
                return PRODUCT_PLAN_MAP[product_id]
    except Exception:
        pass
    # Try payment_intent metadata fallback
    try:
        meta = event_data["object"].get("metadata", {})
        if "clawhub_plan" in meta:
            return meta["clawhub_plan"]
    except Exception:
        pass
    return "unknown"


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event["type"]
    data = event["data"]
    obj = data["object"]

    logger.info(f"Stripe event received: {event_type}")

    # ── Subscription created / renewed ──────────────────────────────────────
    if event_type == "customer.subscription.created":
        customer_id = obj["customer"]
        subscription_id = obj["id"]
        plan = _plan_from_event(data)

        customer = stripe.Customer.retrieve(customer_id)
        email = customer.get("email", "unknown@5cypress.com")

        new_key = await create_api_key(
            user_email=email,
            plan=plan,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
        )
        logger.info(f"New subscription: {email} / plan={plan} / key={new_key[:12]}…")
        # TODO: Send email with new_key here (e.g., via SendGrid or Resend)

    # ── Subscription cancelled / payment failed ─────────────────────────────
    elif event_type in (
        "customer.subscription.deleted",
        "customer.subscription.paused",
    ):
        subscription_id = obj["id"]
        await deactivate_key_by_subscription(subscription_id)
        logger.info(f"Deactivated keys for subscription {subscription_id}")

    # ── One-time payment (onboarding kit) ──────────────────────────────────
    elif event_type == "checkout.session.completed":
        mode = obj.get("mode")
        if mode == "payment":  # one-time purchase
            customer_email = obj.get("customer_details", {}).get("email", "")
            plan = obj.get("metadata", {}).get("clawhub_plan", "onboarding")
            new_key = await create_api_key(
                user_email=customer_email,
                plan=plan,
                stripe_customer_id=obj.get("customer"),
            )
            logger.info(f"One-time purchase: {customer_email} / plan={plan} / key={new_key[:12]}…")
            # TODO: Send email with new_key

    return JSONResponse({"received": True})


@router.post("/test-create-key")
async def test_create_key(email: str, plan: str):
    """DEV ONLY — remove before production. Creates a test key without Stripe."""
    if os.getenv("ENVIRONMENT", "dev") != "dev":
        raise HTTPException(status_code=404)
    key = await create_api_key(user_email=email, plan=plan)
    return {"key": key, "email": email, "plan": plan}
