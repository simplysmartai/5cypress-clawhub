# 5 Cypress ClawHub Backend — API Gateway
# Powers all 5 published ClawHub skills with a single API key auth model.

import os
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from dotenv import load_dotenv
load_dotenv()

from db import init_db
from routers import tcg, osha, contracts, baseball, onboarding
from stripe_webhooks import router as stripe_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiter: 100 requests per minute globally, 10 per minute per IP for /stripe
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="5 Cypress ClawHub API",
    description="Backend for 5 Cypress ClawHub skills. Visit https://5cypress.com/keys to get an API key.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"error": "Rate limit exceeded. Max 100 requests/min. Try again later."},
))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all responses for debugging."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Register routers
app.include_router(tcg.router, prefix="/tcg", tags=["TCG Price Tracker"])
app.include_router(osha.router, prefix="/osha", tags=["OSHA Monitor"])
app.include_router(contracts.router, prefix="/contracts", tags=["Federal Contracts"])
app.include_router(baseball.router, prefix="/baseball", tags=["Baseball Sabermetrics"])
app.include_router(onboarding.router, prefix="/onboarding", tags=["AI Onboarding Kit"])
app.include_router(stripe_router, prefix="/stripe", tags=["Stripe Webhooks"])


@app.get("/health")
async def health():
    from datetime import datetime, timezone
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error. Please contact support@5cypress.com.",
            "request_id": request_id,
        },
    )
