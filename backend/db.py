"""
Database layer — SQLite for dev, Postgres-compatible via env swap.
Manages API keys, user plans, and subscription state.
"""

import os
import uuid
import logging
import aiosqlite
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "5cypress_clawhub.db")

# All plans a key can hold. Controls which router endpoints are authorized.
VALID_PLANS = {"tcg", "osha", "contracts", "baseball", "onboarding", "all"}

CREATE_KEYS_TABLE = """
CREATE TABLE IF NOT EXISTS api_keys (
    key TEXT PRIMARY KEY,
    user_email TEXT NOT NULL,
    plan TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT
);
"""

CREATE_USAGE_TABLE = """
CREATE TABLE IF NOT EXISTS usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    called_at TEXT NOT NULL
);
"""


async def init_db():
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(CREATE_KEYS_TABLE)
        await db.execute(CREATE_USAGE_TABLE)
        await db.commit()
    logger.info("DB tables ensured.")


async def create_api_key(
    user_email: str,
    plan: str,
    stripe_customer_id: str | None = None,
    stripe_subscription_id: str | None = None,
    expires_at: datetime | None = None,
) -> str:
    key = f"5cy_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc).isoformat()
    exp = expires_at.isoformat() if expires_at else None
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """INSERT INTO api_keys
               (key, user_email, plan, status, stripe_customer_id, stripe_subscription_id, created_at, expires_at)
               VALUES (?, ?, ?, 'active', ?, ?, ?, ?)""",
            (key, user_email, plan, stripe_customer_id, stripe_subscription_id, now, exp),
        )
        await db.commit()
    logger.info(f"Created API key for {user_email} / plan={plan}")
    return key


async def get_key_record(key: str) -> dict | None:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM api_keys WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def deactivate_key_by_subscription(stripe_subscription_id: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "UPDATE api_keys SET status = 'cancelled' WHERE stripe_subscription_id = ?",
            (stripe_subscription_id,),
        )
        await db.commit()
    logger.info(f"Deactivated keys for subscription {stripe_subscription_id}")


async def deactivate_key_by_email(user_email: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "UPDATE api_keys SET status = 'cancelled' WHERE user_email = ?",
            (user_email,),
        )
        await db.commit()


async def mark_key_used(key: str, endpoint: str):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "INSERT INTO usage_log (api_key, endpoint, called_at) VALUES (?, ?, ?)",
            (key, endpoint, now),
        )
        # For onboarding one-time keys: deactivate after first meaningful use
        await db.commit()
