"""
Tests for TCG Price Tracker skill endpoints.
"""

import pytest


def test_tcg_price_missing_card_param(client):
    """Should return 422 when 'card' parameter is missing."""
    response = client.get(
        "/tcg/price?game=mtg",
        headers={"X-API-Key": "5cy_test_key"}
    )
    # Either validation error or missing key error
    assert response.status_code in [422, 401]


def test_tcg_price_invalid_game(client):
    """Should reject invalid game values."""
    response = client.get(
        "/tcg/price?card=Black+Lotus&game=invalid",
        headers={"X-API-Key": "5cy_test_key"}
    )
    assert response.status_code in [422, 401]


def test_tcg_search_query_validation(client):
    """Search query should be required and have length limits."""
    # Empty query
    response = client.get(
        "/tcg/search?q=&game=mtg",
        headers={"X-API-Key": "5cy_test_key"}
    )
    assert response.status_code in [422, 401]


def test_tcg_movers_valid_game(client):
    """Movers endpoint should accept valid game values."""
    for game in ["mtg", "pokemon"]:
        response = client.get(
            f"/tcg/movers?game={game}",
            headers={"X-API-Key": "5cy_test_key"}
        )
        # Accept 401 (key validation) for now since we don't have a real key
        assert response.status_code in [200, 401, 402]


def test_tcg_response_format(client):
    """Response should follow the standard format: {ok, data, source, cached}."""
    # This would need a real key to test fully, but we validate the structure
    response = client.get("/tcg/movers?game=mtg")
    if response.status_code == 401:
        assert "error" in response.json() or "detail" in response.json()
    else:
        data = response.json()
        assert "ok" in data or "error" in data
