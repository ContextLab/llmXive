"""
Tests for GDELT data fetching logic.
Specifically tests retry logic on failure.
"""
import unittest
import time
from unittest.mock import patch, MagicMock, call, Mock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logging import get_logger
from data.fetch_gdelt import fetch_with_retry

logger = get_logger(__name__)


class TestGDELTRetryLogic(unittest.TestCase):
    """Test suite for GDELT retry mechanisms."""

    @patch('data.fetch_gdelt.requests.get')
    def test_retry_logic_on_failure(self, mock_get):
        """
        Verify the function retries exactly 3 times (mock.call_count == 3)
        and returns the success response on the final attempt.

        Scenario:
        - Call 1: 500 Error
        - Call 2: 500 Error
        - Call 3: 200 Success
        """
        # Setup mock responses
        error_response = Mock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = Exception("Server Error")

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"data": "success"}

        # Configure the mock to return error, error, then success
        mock_get.side_effect = [error_response, error_response, success_response]

        # Call the function with a short backoff for testing speed
        # We pass max_retries=3 explicitly to ensure we test exactly 3 attempts
        result = fetch_with_retry(
            url="http://example.com/gdelt",
            max_retries=3,
            backoff_factor=0.01  # Very short backoff for unit test speed
        )

        # Assertion 1: Verify the function was called exactly 3 times
        self.assertEqual(mock_get.call_count, 3)

        # Assertion 2: Verify the returned result is the success response data
        self.assertEqual(result, {"data": "success"})

        # Assertion 3: Verify the calls were made in sequence
        # We don't need to check exact arguments for this specific task,
        # but verifying the count is the primary requirement.
        self.assertTrue(mock_get.called)

    @patch('data.fetch_gdelt.requests.get')
    def test_retry_exhaustion_raises_exception(self, mock_get):
        """
        Verify that if all retries fail, the function raises an exception.
        """
        error_response = Mock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = Exception("Server Error")

        # Always fail
        mock_get.side_effect = [error_response, error_response, error_response]

        with self.assertRaises(Exception) as context:
            fetch_with_retry(
                url="http://example.com/gdelt",
                max_retries=3,
                backoff_factor=0.01
            )

        self.assertIn("Server Error", str(context.exception))
        self.assertEqual(mock_get.call_count, 3)


if __name__ == '__main__':
    unittest.main()