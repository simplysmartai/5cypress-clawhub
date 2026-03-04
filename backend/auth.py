"""
API key authentication middleware.
Every protected endpoint calls require_plan() as a FastAPI dependency.
"""

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Header, HTTPException, Depends, Request

from db import get_key_record, mark_key_used

logger = logging.getLogger(__name__)


class AuthenticatedKey:
    def __init__(self, key: str, email: str, plan: str):
        self.key = key
        self.email = email
        self.plan = plan


async def _resolve_key(x_api_key: Annotated[str | None, Header()] = None) -> AuthenticatedKey:
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header. Get your key at https://5cypress.com/keys",
        )
    record = await get_key_record(x_api_key)
    if not record:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Get your key at https://5cypress.com/keys",
        )
    if record["status"] != "active":
        raise HTTPException(
            status_code=402,
            detail=f"API key is {record['status']}. Renew your subscription at https://5cypress.com/keys",
        )
    # Check expiry
    if record["expires_at"]:
        exp = datetime.fromisoformat(record["expires_at"])
        if datetime.now(timezone.utc) > exp:
            raise HTTPException(
                status_code=402,
                detail="API key has expired. Renew at https://5cypress.com/keys",
            )
    return AuthenticatedKey(
        key=x_api_key,
        email=record["user_email"],
        plan=record["plan"],
    )


def require_plan(required_plan: str):
    """
    Dependency factory. Usage:
        auth: AuthenticatedKey = Depends(require_plan("tcg"))
    """
    async def _check(request: Request, auth: AuthenticatedKey = Depends(_resolve_key)) -> AuthenticatedKey:
        if auth.plan not in (required_plan, "all"):
            raise HTTPException(
                status_code=403,
                detail=f"Your plan ({auth.plan!r}) does not include the '{required_plan}' skill. "
                       f"Upgrade at https://5cypress.com/keys",
            )
        # Log usage (non-blocking)
        try:
            await mark_key_used(auth.key, str(request.url.path))
        except Exception:
            pass  # Never fail a request due to logging
        return auth
    return _check
