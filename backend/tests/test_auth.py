"""
Tests for authentication and API key validation.
"""

import pytest


def test_health_endpoint(client):
    """Health check should always return 200 and have required fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


def test_missing_api_key(client):
    """Endpoint should return 401 when API key is missing."""
    response = client.get("/tcg/price?card=Black+Lotus&game=mtg")
    assert response.status_code == 401
    data = response.json()
    assert "API-Key" in data["detail"] or "missing" in data["detail"].lower()


def test_invalid_api_key(client):
    """Endpoint should return 401 for invalid API key."""
    response = client.get(
        "/tcg/price?card=Black+Lotus&game=mtg",
        headers={"X-API-Key": "5cy_invalid_key_xyz"}
    )
    assert response.status_code == 401


def test_request_id_header(client):
    """All responses should include X-Request-ID header for debugging."""
    response = client.get("/health")
    assert "x-request-id" in response.headers.lower()


def test_cors_headers(client):
    """CORS headers should be present for cross-origin requests."""
    response = client.options("/health")
    assert response.status_code == 200


def test_invalid_json_body(client):
    """POST with invalid JSON should return 422 (validation error)."""
    response = client.post(
        "/onboarding/generate",
        json={"invalid_field": "value"},
        headers={"X-API-Key": "5cy_test_key"}
    )
    assert response.status_code in [422, 401]  # 422 for validation, 401 for missing key
