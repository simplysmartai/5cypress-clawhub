"""
Shared Pydantic response models used across all skill routers.
"""

from pydantic import BaseModel
from typing import Any


class SuccessResponse(BaseModel):
    ok: bool = True
    data: Any
    source: str | None = None
    cached: bool = False


class ErrorResponse(BaseModel):
    ok: bool = False
    error: str
    hint: str | None = None
