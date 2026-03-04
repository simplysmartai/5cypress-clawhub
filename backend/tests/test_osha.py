"""OSHA Monitor skill endpoint tests."""
import pytest
from fastapi.testclient import TestClient


class TestOSHAEndpoints:
    """Test OSHA Monitor skill endpoints and validation."""

    def test_trades_list_valid(self, client: TestClient, test_api_key: str):
        """Test /osha/trades returns list of valid trade categories."""
        response = client.get(
            "/osha/trades",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        # Should have at least the expected trades
        assert len(data["data"]) > 0
        # Check structure of trade item
        if data["data"]:
            trade = data["data"][0]
            assert "trade" in trade
            assert "naics_code" in trade

    def test_violations_valid_trade(self, client: TestClient, test_api_key: str):
        """Test /osha/violations with valid trade and state."""
        response = client.get(
            "/osha/violations?trade=roofing&state=TX",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "data" in data

    def test_violations_missing_trade(self, client: TestClient, test_api_key: str):
        """Test /osha/violations missing required trade parameter."""
        response = client.get(
            "/osha/violations?state=TX",
            headers={"X-API-Key": test_api_key}
        )
        # Should fail validation
        assert response.status_code in [422, 400]

    def test_violations_missing_state(self, client: TestClient, test_api_key: str):
        """Test /osha/violations missing required state parameter."""
        response = client.get(
            "/osha/violations?trade=roofing",
            headers={"X-API-Key": test_api_key}
        )
        # Should fail validation
        assert response.status_code in [422, 400]

    def test_violations_invalid_state_format(self, client: TestClient, test_api_key: str):
        """Test /osha/violations with invalid state (3+ chars should fail)."""
        response = client.get(
            "/osha/violations?trade=roofing&state=TEXAS",
            headers={"X-API-Key": test_api_key}
        )
        # Should reject state > 2 chars
        assert response.status_code in [422, 400]

    def test_summary_valid(self, client: TestClient, test_api_key: str):
        """Test /osha/summary with valid trade."""
        response = client.get(
            "/osha/summary?trade=electrical",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "data" in data

    def test_summary_missing_trade(self, client: TestClient, test_api_key: str):
        """Test /osha/summary missing trade parameter."""
        response = client.get(
            "/osha/summary",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_summary_invalid_trade(self, client: TestClient, test_api_key: str):
        """Test /osha/summary with invalid trade name."""
        response = client.get(
            "/osha/summary?trade=invalid_trade_xyz",
            headers={"X-API-Key": test_api_key}
        )
        # Should still return 200 (trade might not exist in data, but endpoint valid)
        # or 400 if trade validation is strict
        assert response.status_code in [200, 400, 422]

    def test_top_violators_valid(self, client: TestClient, test_api_key: str):
        """Test /osha/top-violators with valid trade and state."""
        response = client.get(
            "/osha/top-violators?trade=construction&state=CA",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "data" in data

    def test_top_violators_missing_state(self, client: TestClient, test_api_key: str):
        """Test /osha/top-violators missing required state."""
        response = client.get(
            "/osha/top-violators?trade=construction",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_top_violators_response_format(self, client: TestClient, test_api_key: str):
        """Test /osha/top-violators response format."""
        response = client.get(
            "/osha/top-violators?trade=electrical&state=FL",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert "data" in data
        assert "source" in data
        assert "cached" in data

    def test_response_includes_request_id(self, client: TestClient, test_api_key: str):
        """Test all OSHA endpoints include X-Request-ID header."""
        response = client.get(
            "/osha/trades",
            headers={"X-API-Key": test_api_key}
        )
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID format
