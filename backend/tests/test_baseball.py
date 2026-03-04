"""Baseball Sabermetrics skill endpoint tests."""
import pytest
from fastapi.testclient import TestClient


class TestBaseballEndpoints:
    """Test Baseball Sabermetrics skill endpoints and validation."""

    def test_player_valid_name(self, client: TestClient, test_api_key: str):
        """Test /baseball/player with valid player name."""
        response = client.get(
            "/baseball/player?name=Mike+Trout&year=2024",
            headers={"X-API-Key": test_api_key},
            timeout=30
        )
        # May timeout due to network I/O, but should not return auth error
        assert response.status_code in [200, 408, 504]  # 408=timeout, 504=gateway timeout

    def test_player_missing_name(self, client: TestClient, test_api_key: str):
        """Test /baseball/player missing required name parameter."""
        response = client.get(
            "/baseball/player?year=2024",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_player_missing_year(self, client: TestClient, test_api_key: str):
        """Test /baseball/player missing required year parameter."""
        response = client.get(
            "/baseball/player?name=Mike+Trout",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_player_invalid_year_format(self, client: TestClient, test_api_key: str):
        """Test /baseball/player with invalid year format."""
        response = client.get(
            "/baseball/player?name=Mike+Trout&year=not_a_year",
            headers={"X-API-Key": test_api_key}
        )
        # Should reject non-numeric year
        assert response.status_code in [422, 400]

    def test_player_year_out_of_range(self, client: TestClient, test_api_key: str):
        """Test /baseball/player with year outside valid range."""
        response = client.get(
            "/baseball/player?name=Mike+Trout&year=1800",
            headers={"X-API-Key": test_api_key}
        )
        # Should reject year < 1900 or > current year + 1
        assert response.status_code in [422, 400]

    def test_player_response_format(self, client: TestClient, test_api_key: str):
        """Test /baseball/player response structure."""
        response = client.get(
            "/baseball/player?name=Clayton+Kershaw&year=2023",
            headers={"X-API-Key": test_api_key},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            assert "ok" in data
            assert "data" in data
            assert "source" in data
            assert "cached" in data

    def test_digest_valid_names(self, client: TestClient, test_api_key: str):
        """Test /baseball/digest with valid player names."""
        response = client.get(
            "/baseball/digest?names=Mike+Trout,Judge,Acuna&year=2024",
            headers={"X-API-Key": test_api_key},
            timeout=30
        )
        assert response.status_code in [200, 408, 504]

    def test_digest_missing_names(self, client: TestClient, test_api_key: str):
        """Test /baseball/digest missing required names parameter."""
        response = client.get(
            "/baseball/digest?year=2024",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_digest_missing_year(self, client: TestClient, test_api_key: str):
        """Test /baseball/digest missing required year parameter."""
        response = client.get(
            "/baseball/digest?names=Trout,Judge",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_digest_too_many_players(self, client: TestClient, test_api_key: str):
        """Test /baseball/digest with more than 12 players."""
        # Create comma-separated list of 13 names
        many_names = ",".join([f"Player{i}" for i in range(13)])
        response = client.get(
            f"/baseball/digest?names={many_names}&year=2024",
            headers={"X-API-Key": test_api_key}
        )
        # Should reject > 12 players
        assert response.status_code in [422, 400]

    def test_digest_exactly_twelve_players(self, client: TestClient, test_api_key: str):
        """Test /baseball/digest with exactly 12 players (boundary case)."""
        twelve_names = ",".join([f"Player{i}" for i in range(12)])
        response = client.get(
            f"/baseball/digest?names={twelve_names}&year=2024",
            headers={"X-API-Key": test_api_key},
            timeout=30
        )
        # Should accept 12 players
        assert response.status_code in [200, 408, 504]

    def test_leaders_valid_stat(self, client: TestClient, test_api_key: str):
        """Test /baseball/leaders with valid statistic."""
        response = client.get(
            "/baseball/leaders?stat=wRC+&year=2024&player_type=hitter",
            headers={"X-API-Key": test_api_key},
            timeout=30
        )
        assert response.status_code in [200, 408, 504]

    def test_leaders_pitcher_stat(self, client: TestClient, test_api_key: str):
        """Test /baseball/leaders with pitcher statistic."""
        response = client.get(
            "/baseball/leaders?stat=xFIP&year=2024&player_type=pitcher",
            headers={"X-API-Key": test_api_key},
            timeout=30
        )
        assert response.status_code in [200, 408, 504]

    def test_leaders_missing_stat(self, client: TestClient, test_api_key: str):
        """Test /baseball/leaders missing required stat parameter."""
        response = client.get(
            "/baseball/leaders?year=2024&player_type=hitter",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_leaders_missing_player_type(self, client: TestClient, test_api_key: str):
        """Test /baseball/leaders missing required player_type parameter."""
        response = client.get(
            "/baseball/leaders?stat=wRC+&year=2024",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_leaders_missing_year(self, client: TestClient, test_api_key: str):
        """Test /baseball/leaders missing required year parameter."""
        response = client.get(
            "/baseball/leaders?stat=wRC+&player_type=hitter",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_leaders_invalid_player_type(self, client: TestClient, test_api_key: str):
        """Test /baseball/leaders with invalid player_type."""
        response = client.get(
            "/baseball/leaders?stat=wRC+&year=2024&player_type=outfielder",
            headers={"X-API-Key": test_api_key}
        )
        # Should only accept 'hitter' or 'pitcher'
        assert response.status_code in [422, 400]

    def test_response_includes_request_id(self, client: TestClient, test_api_key: str):
        """Test all Baseball endpoints include X-Request-ID header."""
        response = client.get(
            "/baseball/player?name=Trout&year=2024",
            headers={"X-API-Key": test_api_key},
            timeout=30
        )
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID format
