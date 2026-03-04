"""
Pytest configuration and fixtures for all tests.
"""

import pytest
import os
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """FastAPI test client."""
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_placeholder"
    os.environ["ENVIRONMENT"] = "test"
    from main import app
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client():
    """Async HTTP client for testing."""
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_placeholder"
    from main import app
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client


@pytest.fixture
async def test_api_key():
    """Create a test API key for auth tests."""
    from db import create_api_key
    await db.init_db()
    key = await create_api_key(
        user_email="test@example.com",
        plan="all",  # all plans for testing
    )
    return key
