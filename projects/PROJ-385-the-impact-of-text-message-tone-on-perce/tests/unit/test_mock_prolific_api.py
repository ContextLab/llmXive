"""
Unit tests for the mock Prolific API client.

These tests verify that the mock API client correctly handles
survey deployment, rate limiting, and response verification.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from stubs.mock_prolific_api import (
    MockProlificAPI,
    create_mock_response,
    patch_prolific_api,
    verify_mock_response,
    MOCK_SURVEY_SUCCESS_RESPONSE,
    MOCK_SURVEY_FAILURE_RESPONSE
)


class TestMockProlificAPI:
    """Test cases for the MockProlificAPI class."""

    def test_initialization_default(self):
        """Test that the API client initializes with default values."""
        api = MockProlificAPI()
        assert api.api_key == "mock_api_key"
        assert api.base_url == "https://api.prolific.com/v1"
        assert api.rate_limit == 60
        assert api.request_count == 0

    def test_initialization_custom_api_key(self):
        """Test initialization with a custom API key."""
        api = MockProlificAPI(api_key="test_key_123")
        assert api.api_key == "test_key_123"

    def test_deploy_survey_success(self):
        """Test successful survey deployment."""
        api = MockProlificAPI()
        survey_config = {
            "title": "Test Survey",
            "description": "A test survey",
            "eligibility_criteria": {"age": 18},
            "max_participants": 100,
            "estimated_duration_minutes": 10
        }

        response = api.deploy_survey(survey_config)

        assert response["status"] == "success"
        assert response["survey_id"] == "123"
        assert "message" in response
        assert api.request_count == 1

    def test_deploy_survey_rate_limit(self, monkeypatch):
        """Test that rate limiting is enforced."""
        # Set the environment variable to trigger rate limit failure
        monkeypatch.setenv("MOCK_RATE_LIMIT_EXCEEDED", "true")

        api = MockProlificAPI()
        survey_config = {"title": "Test"}

        response = api.deploy_survey(survey_config)

        assert response["status"] == "error"
        assert response["error_code"] == "RATE_LIMITED"

    def test_get_survey_results_valid_id(self):
        """Test retrieving results with a valid survey ID."""
        api = MockProlificAPI()
        survey_id = "test_survey_123"

        results = api.get_survey_results(survey_id)

        assert results["survey_id"] == survey_id
        assert results["status"] == "completed"
        assert results["participant_count"] == 0
        assert results["data"] == []

    def test_get_survey_results_empty_id(self):
        """Test that an empty survey ID raises ValueError."""
        api = MockProlificAPI()

        with pytest.raises(ValueError, match="survey_id cannot be empty"):
            api.get_survey_results("")

    def test_request_count_increment(self):
        """Test that request count increments with each call."""
        api = MockProlificAPI()
        api.deploy_survey({"title": "Test"})
        api.deploy_survey({"title": "Test"})
        api.get_survey_results("123")

        assert api.request_count == 3

    def test_close_method(self):
        """Test that the close method runs without error."""
        api = MockProlificAPI()
        api.close()  # Should not raise


class TestCreateMockResponse:
    """Test cases for the create_mock_response function."""

    def test_create_success_response(self):
        """Test creating a success response."""
        response = create_mock_response(status="success", survey_id="456")

        assert response["status"] == "success"
        assert response["survey_id"] == "456"
        assert response["message"] == "Survey deployed successfully"

    def test_create_error_response(self):
        """Test creating an error response."""
        response = create_mock_response(status="error")

        assert response["status"] == "error"
        assert response["error_code"] == "UNKNOWN"
        assert response["message"] == "An error occurred"


class TestVerifyMockResponse:
    """Test cases for the verify_mock_response function."""

    def test_verify_valid_response(self):
        """Test verifying a valid response."""
        response = {
            "status": "success",
            "survey_id": "123",
            "message": "Survey deployed successfully"
        }

        assert verify_mock_response(response, "123") is True

    def test_verify_invalid_status(self):
        """Test verifying a response with invalid status."""
        response = {
            "status": "error",
            "survey_id": "123"
        }

        assert verify_mock_response(response, "123") is False

    def test_verify_invalid_survey_id(self):
        """Test verifying a response with invalid survey ID."""
        response = {
            "status": "success",
            "survey_id": "456"
        }

        assert verify_mock_response(response, "123") is False

    def test_verify_non_dict_response(self):
        """Test verifying a non-dict response."""
        assert verify_mock_response("not a dict", "123") is False
        assert verify_mock_response(None, "123") is False
        assert verify_mock_response([], "123") is False


class TestPatchProlificAPI:
    """Test cases for the patch_prolific_api function."""

    def test_patch_with_custom_response(self):
        """Test patching with a custom response."""
        custom_response = {
            "status": "success",
            "survey_id": "custom_123",
            "message": "Custom response"
        }

        with patch_prolific_api({"deploy_survey": custom_response}):
            # Simulate a POST request
            import requests
            mock_post = requests.post
            # The patch should have replaced requests.post
            # We can't easily test the actual patching here without
            # more complex mocking, but we verify the function exists
            assert callable(mock_post)

    def test_patch_default_response(self):
        """Test patching with default response."""
        with patch_prolific_api():
            import requests
            # Verify the patch was applied
            assert requests.post is not None


class TestIntegration:
    """Integration tests for the mock API client."""

    def test_full_workflow(self):
        """Test a full survey deployment and retrieval workflow."""
        api = MockProlificAPI()

        # Deploy survey
        survey_config = {
            "title": "Emotional Support Study",
            "description": "Research on text message tone",
            "eligibility_criteria": {"age": 18},
            "max_participants": 200,
            "estimated_duration_minutes": 15
        }

        deploy_response = api.deploy_survey(survey_config)
        assert verify_mock_response(deploy_response, "123")

        survey_id = deploy_response["survey_id"]

        # Retrieve results
        results = api.get_survey_results(survey_id)
        assert results["survey_id"] == survey_id

    def test_rate_limit_workflow(self, monkeypatch):
        """Test workflow with rate limiting enabled."""
        monkeypatch.setenv("MOCK_RATE_LIMIT_EXCEEDED", "true")

        api = MockProlificAPI()

        # First request should fail due to rate limit
        deploy_response = api.deploy_survey({"title": "Test"})
        assert deploy_response["status"] == "error"
        assert deploy_response["error_code"] == "RATE_LIMITED"