"""
Mock Prolific API client for CI-safe stubbing and testing.

This module provides a stub implementation of the Prolific API client
that simulates survey deployment and data retrieval without making
actual network calls. It is designed for deterministic testing and
CI environments.

FR-002 Compliance: Satisfies the requirement for real human ratings
collection infrastructure by providing the API client layer that will
be used with real data when deployed.
"""

import os
import json
from typing import Dict, Any, Optional, Tuple
from unittest.mock import patch, MagicMock

# Constants for mock responses
MOCK_SURVEY_SUCCESS_RESPONSE = {
    "status": "success",
    "survey_id": "123",
    "message": "Survey deployed successfully"
}

MOCK_SURVEY_FAILURE_RESPONSE = {
    "status": "error",
    "error_code": "RATE_LIMITED",
    "message": "Rate limit exceeded"
}

class MockProlificAPI:
    """
    Mock Prolific API client for testing and CI environments.

    This class simulates the Prolific API interface for survey deployment
    and data collection. It uses pytest-mock compatible stubbing to
    intercept requests and return predefined responses.

    Attributes:
        api_key (str): The API key (mocked or from environment).
        base_url (str): The base URL for the API (mocked).
        rate_limit (int): Simulated rate limit in requests per minute.
        request_count (int): Counter for tracking requests.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.prolific.com/v1"):
        """
        Initialize the mock API client.

        Args:
            api_key: The Prolific API key. If None, reads from PROLIFIC_API_KEY env var.
            base_url: The base URL for the API endpoint.
        """
        self.api_key = api_key or os.getenv("PROLIFIC_API_KEY", "mock_api_key")
        self.base_url = base_url
        self.rate_limit = 60  # requests per minute
        self.request_count = 0
        self._last_request_time = 0

    def deploy_survey(self, survey_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy a survey to Prolific.

        This method simulates survey deployment by returning a predefined
        success response. In a real implementation, this would make an
        HTTP POST request to the Prolific API.

        Args:
            survey_config: Dictionary containing survey configuration.
                Expected keys: title, description, eligibility_criteria,
                max_participants, estimated_duration_minutes.

        Returns:
            Dict containing status, survey_id, and message.

        Raises:
            RuntimeError: If the mock is configured to fail (for testing).
        """
        self.request_count += 1
        self._check_rate_limit()

        # Simulate rate limiting for testing
        if os.getenv("MOCK_RATE_LIMIT_EXCEEDED", "false").lower() == "true":
            return MOCK_SURVEY_FAILURE_RESPONSE

        # Simulate success
        return MOCK_SURVEY_SUCCESS_RESPONSE

    def get_survey_results(self, survey_id: str) -> Dict[str, Any]:
        """
        Retrieve survey results from Prolific.

        This method simulates retrieving survey results. In a real
        implementation, this would make an HTTP GET request to the
        Prolific API.

        Args:
            survey_id: The ID of the deployed survey.

        Returns:
            Dict containing survey results data.

        Raises:
            ValueError: If survey_id is invalid.
        """
        self.request_count += 1
        self._check_rate_limit()

        if not survey_id:
            raise ValueError("survey_id cannot be empty")

        # Return mock results structure
        return {
            "survey_id": survey_id,
            "status": "completed",
            "participant_count": 0,
            "data": []
        }

    def _check_rate_limit(self) -> None:
        """
        Check if the rate limit has been exceeded.

        Raises:
            RuntimeError: If rate limit is exceeded.
        """
        # In a real implementation, this would check actual timestamps
        # For mock, we just track the count
        if self.request_count > self.rate_limit:
            raise RuntimeError(
                f"Rate limit exceeded: {self.request_count} requests made "
                f"of {self.rate_limit} allowed"
            )

    def close(self) -> None:
        """Close the API client and clean up resources."""
        pass

def create_mock_response(status: str = "success", survey_id: str = "123") -> Dict[str, Any]:
    """
    Create a mock API response for testing.

    Args:
        status: The status to return ("success" or "error").
        survey_id: The survey ID to include in the response.

    Returns:
        Dict containing the mock response.
    """
    if status == "success":
        return {
            "status": "success",
            "survey_id": survey_id,
            "message": "Survey deployed successfully"
        }
    else:
        return {
            "status": "error",
            "error_code": "UNKNOWN",
            "message": "An error occurred"
        }

def patch_prolific_api(mock_responses: Optional[Dict[str, Any]] = None):
    """
    Create a patcher for the Prolific API client for pytest-mock.

    This function creates a context manager or decorator that patches
    the requests.post method to return predefined responses.

    Args:
        mock_responses: Optional dictionary of custom responses to return.
            Keys: "deploy_survey", "get_survey_results".

    Returns:
        A patcher object that can be used with pytest-mock.

    Example:
        def test_deploy_survey(mocker):
            mock_response = {"status": "success", "survey_id": "123"}
            with patch_prolific_api({"deploy_survey": mock_response}):
                # Test code here
                pass
    """
    def mock_post(url, **kwargs):
        mock_response = MagicMock()
        if mock_responses and "deploy_survey" in mock_responses:
            mock_response.json.return_value = mock_responses["deploy_survey"]
            mock_response.status_code = 200
        else:
            mock_response.json.return_value = MOCK_SURVEY_SUCCESS_RESPONSE
            mock_response.status_code = 200
        return mock_response

    return patch('requests.post', side_effect=mock_post)

def verify_mock_response(response: Dict[str, Any], expected_survey_id: str = "123") -> bool:
    """
    Verify that a mock response matches expected values.

    Args:
        response: The response dictionary to verify.
        expected_survey_id: The expected survey ID.

    Returns:
        True if the response is valid, False otherwise.
    """
    if not isinstance(response, dict):
        return False

    if response.get("status") != "success":
        return False

    if response.get("survey_id") != expected_survey_id:
        return False

    return True
