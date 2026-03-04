"""Federal Contracts skill endpoint tests."""
import pytest
from fastapi.testclient import TestClient


class TestContractsEndpoints:
    """Test Federal Contracts skill endpoints and validation."""

    def test_categories_list_valid(self, client: TestClient, test_api_key: str):
        """Test /contracts/categories returns valid category list."""
        response = client.get(
            "/contracts/categories",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        # Check structure
        if data["data"]:
            category = data["data"][0]
            assert "category" in category
            assert "naics_code" in category

    def test_digest_valid_category_state(self, client: TestClient, test_api_key: str):
        """Test /contracts/digest with valid category and state."""
        response = client.get(
            "/contracts/digest?category=it&state=VA",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "data" in data

    def test_digest_missing_category(self, client: TestClient, test_api_key: str):
        """Test /contracts/digest missing required category parameter."""
        response = client.get(
            "/contracts/digest?state=VA",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_digest_missing_state(self, client: TestClient, test_api_key: str):
        """Test /contracts/digest missing required state parameter."""
        response = client.get(
            "/contracts/digest?category=it",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_digest_invalid_state_format(self, client: TestClient, test_api_key: str):
        """Test /contracts/digest with invalid state format."""
        response = client.get(
            "/contracts/digest?category=it&state=VIRGINIA",
            headers={"X-API-Key": test_api_key}
        )
        # Should reject state > 2 chars
        assert response.status_code in [422, 400]

    def test_digest_response_format(self, client: TestClient, test_api_key: str):
        """Test /contracts/digest response structure."""
        response = client.get(
            "/contracts/digest?category=construction&state=TX",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert "data" in data
        assert "source" in data
        assert "cached" in data
        # Data should be list or object
        assert data["data"] is not None

    def test_search_valid_query(self, client: TestClient, test_api_key: str):
        """Test /contracts/search with valid keyword query."""
        response = client.get(
            "/contracts/search?q=software+development",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "data" in data

    def test_search_missing_query(self, client: TestClient, test_api_key: str):
        """Test /contracts/search missing required query parameter."""
        response = client.get(
            "/contracts/search",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code in [422, 400]

    def test_search_empty_query(self, client: TestClient, test_api_key: str):
        """Test /contracts/search with empty query string."""
        response = client.get(
            "/contracts/search?q=",
            headers={"X-API-Key": test_api_key}
        )
        # Empty query should be rejected
        assert response.status_code in [422, 400]

    def test_search_query_too_long(self, client: TestClient, test_api_key: str):
        """Test /contracts/search with excessively long query."""
        long_query = "a" * 500
        response = client.get(
            f"/contracts/search?q={long_query}",
            headers={"X-API-Key": test_api_key}
        )
        # Should reject queries > 200 chars
        assert response.status_code in [422, 400]

    def test_search_special_characters(self, client: TestClient, test_api_key: str):
        """Test /contracts/search with special characters in query."""
        response = client.get(
            "/contracts/search?q=IT+services+%26+support",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_search_with_state_filter(self, client: TestClient, test_api_key: str):
        """Test /contracts/search with optional state parameter."""
        response = client.get(
            "/contracts/search?q=construction&state=CA",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_response_includes_request_id(self, client: TestClient, test_api_key: str):
        """Test all Contracts endpoints include X-Request-ID header."""
        response = client.get(
            "/contracts/categories",
            headers={"X-API-Key": test_api_key}
        )
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID format

    def test_response_includes_source(self, client: TestClient, test_api_key: str):
        """Test all Contracts responses include 'source' field."""
        response = client.get(
            "/contracts/categories",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "source" in data
        assert data["source"] in ["api", "cache", "mock"]

    def test_response_includes_cached_flag(self, client: TestClient, test_api_key: str):
        """Test all Contracts responses include 'cached' boolean."""
        response = client.get(
            "/contracts/categories",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "cached" in data
        assert isinstance(data["cached"], bool)
