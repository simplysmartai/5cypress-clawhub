"""
Input validation helpers — Pydantic models for every endpoint.
Prevents malformed requests from reaching business logic.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional


class TCGPriceRequest(BaseModel):
    card: str = Field(..., min_length=1, max_length=200, description="Card name")
    game: str = Field("mtg", pattern="^(mtg|pokemon)$")
    set: Optional[str] = Field(None, max_length=100)


class TCGSearchRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=200)
    game: str = Field("mtg", pattern="^(mtg|pokemon)$")
    set: Optional[str] = Field(None, max_length=100)
    

class OSHAViolationsRequest(BaseModel):
    trade: str = Field(..., min_length=3, max_length=50, description="Trade category (lowercase)")
    state: Optional[str] = Field(None, regex="^[A-Z]{2}$")
    limit: int = Field(20, ge=1, le=50)


class ContractsDigestRequest(BaseModel):
    category: str = Field(..., min_length=2, max_length=50)
    state: Optional[str] = Field(None, regex="^[A-Z]{2}$")
    limit: int = Field(10, ge=1, le=25)


class ContractsSearchRequest(BaseModel):
    q: str = Field(..., min_length=3, max_length=300)
    state: Optional[str] = Field(None, regex="^[A-Z]{2}$")
    limit: int = Field(10, ge=1, le=25)


class BaseballPlayerRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    year: int = Field(2025, ge=2000, le=2026)


class BaseballDigestRequest(BaseModel):
    names: str = Field(..., min_length=3, max_length=500, description="Comma-separated player names")
    year: int = Field(2025, ge=2000, le=2026)
    
    @validator("names")
    def validate_names(cls, v):
        names_list = [n.strip() for n in v.split(",")]
        if len(names_list) > 12:
            raise ValueError("Maximum 12 players per request")
        if any(len(n) < 2 for n in names_list):
            raise ValueError("Each player name must be at least 2 characters")
        return v


class BaseballLeadersRequest(BaseModel):
    stat: str = Field("wRC+", min_length=2, max_length=20)
    year: int = Field(2025, ge=2000, le=2026)
    player_type: str = Field("hitter", pattern="^(hitter|pitcher)$")
    limit: int = Field(20, ge=5, le=50)


class OnboardingGenerateRequest(BaseModel):
    industry: str = Field(..., min_length=5, max_length=50)
    company_name: str = Field(..., min_length=1, max_length=100)
    company_size: str = Field("small", pattern="^(solo|micro|small|mid)$")
    primary_pain_points: list[str] = Field(..., min_items=1, max_items=5)
    tools_used: list[str] = Field(default=[], max_items=10)
    
    @validator("primary_pain_points", "tools_used", pre=True, each_item=True)
    def validate_strings(cls, v):
        if not isinstance(v, str) or len(v) < 2 or len(v) > 100:
            raise ValueError("Each item must be 2-100 characters")
        return v.strip()
