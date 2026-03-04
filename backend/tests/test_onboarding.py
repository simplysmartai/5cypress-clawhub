"""AI Onboarding Kit skill endpoint tests."""
import pytest
from fastapi.testclient import TestClient
import json


class TestOnboardingEndpoints:
    """Test AI Onboarding Kit skill endpoints and validation."""

    def test_industries_list_valid(self, client: TestClient, test_api_key: str):
        """Test /onboarding/industries returns valid industry list."""
        response = client.get(
            "/onboarding/industries",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_industries_response_format(self, client: TestClient, test_api_key: str):
        """Test /onboarding/industries response structure."""
        response = client.get(
            "/onboarding/industries",
            headers={"X-API-Key": test_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert "data" in data
        assert "source" in data
        assert "cached" in data
        # All items should have at least name
        for item in data["data"]:
            assert "name" in item or isinstance(item, str)

    def test_generate_valid_request(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate with valid complete request."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "Bright Health Clinic",
            "company_size": "small",
            "primary_pain_points": ["appointment scheduling", "patient communication"],
            "tools_used": ["EHR system", "Stripe"]
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        # Note: Key may be one-time use, so response might be 402 if already used
        assert response.status_code in [200, 402]
        if response.status_code == 200:
            data = response.json()
            assert data["ok"] is True
            assert "data" in data

    def test_generate_missing_industry(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate missing industry field."""
        payload = {
            "company_name": "Test Inc",
            "company_size": "small",
            "primary_pain_points": ["issue 1"],
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_missing_company_name(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate missing company_name field."""
        payload = {
            "industry": "Medical Practice",
            "company_size": "small",
            "primary_pain_points": ["issue 1"],
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_missing_company_size(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate missing company_size field."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "Test Clinic",
            "primary_pain_points": ["issue 1"],
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        # company_size has default value, so might pass
        assert response.status_code in [200, 402, 422]

    def test_generate_missing_pain_points(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate missing primary_pain_points field."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "Test Clinic",
            "company_size": "small",
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_industry_too_short(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate with industry name too short."""
        payload = {
            "industry": "MD",  # Too short, min 5
            "company_name": "Test Inc",
            "company_size": "small",
            "primary_pain_points": ["issue 1"],
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_company_name_too_long(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate with company_name exceeding max length."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "A" * 101,  # Too long, max 100
            "company_size": "small",
            "primary_pain_points": ["issue 1"],
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_invalid_size(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate with invalid company_size."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "Test Clinic",
            "company_size": "enormous",  # Invalid, must be solo/micro/small/mid
            "primary_pain_points": ["issue 1"],
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_empty_pain_points(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate with empty pain_points list."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "Test Clinic",
            "company_size": "small",
            "primary_pain_points": [],  # Empty, min 1
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_too_many_pain_points(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate with more than 5 pain points."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "Test Clinic",
            "company_size": "small",
            "primary_pain_points": [f"issue {i}" for i in range(6)],  # Too many, max 5
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_pain_point_too_short(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate with pain point string too short."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "Test Clinic",
            "company_size": "small",
            "primary_pain_points": ["x"],  # Too short, min 2
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_pain_point_too_long(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate with pain point string too long."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "Test Clinic",
            "company_size": "small",
            "primary_pain_points": ["A" * 101],  # Too long, max 100
            "tools_used": []
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_too_many_tools(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate with more than 10 tools."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "Test Clinic",
            "company_size": "small",
            "primary_pain_points": ["issue 1"],
            "tools_used": [f"Tool{i}" for i in range(11)]  # Too many, max 10
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [422, 400]

    def test_generate_with_extra_fields(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate with unexpected extra fields (should be ignored)."""
        payload = {
            "industry": "Medical Practice",
            "company_name": "Test Clinic",
            "company_size": "small",
            "primary_pain_points": ["issue 1"],
            "tools_used": [],
            "extra_field": "should be ignored"
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        # Pydantic by default ignores extra fields
        assert response.status_code in [200, 402]

    def test_generate_response_format(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate response structure."""
        payload = {
            "industry": "Law Firm",
            "company_name": "Test Legal LLC",
            "company_size": "small",
            "primary_pain_points": ["document drafting", "client communication"],
            "tools_used": ["Clio"]
        }
        response = client.post(
            "/onboarding/generate",
            headers={"X-API-Key": test_api_key},
            json=payload
        )
        assert response.status_code in [200, 402]
        if response.status_code == 200:
            data = response.json()
            assert "ok" in data
            assert data["ok"] is True
            assert "data" in data
            # Response should contain kit data
            assert data["data"] is not None

    def test_response_includes_request_id(self, client: TestClient, test_api_key: str):
        """Test all Onboarding endpoints include X-Request-ID header."""
        response = client.get(
            "/onboarding/industries",
            headers={"X-API-Key": test_api_key}
        )
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID format

    def test_content_type_json(self, client: TestClient, test_api_key: str):
        """Test /onboarding/generate rejects non-JSON content."""
        response = client.post(
            "/onboarding/generate",
            headers={
                "X-API-Key": test_api_key,
                "Content-Type": "text/plain"
            },
            content="industry=Medical&company_name=Test"
        )
        # Should return 422 or 415
        assert response.status_code in [422, 415, 400]
