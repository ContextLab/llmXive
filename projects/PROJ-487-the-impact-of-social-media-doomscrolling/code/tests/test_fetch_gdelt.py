import unittest
import time
from unittest.mock import patch, MagicMock, call, Mock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logging import get_logger
from data.fetch_gdelt import fetch_with_retry

logger = get_logger(__name__)

class TestGDELTRetryLogic(unittest.TestCase):
    """Unit tests for GDELT fetch retry logic."""

    @patch('data.fetch_gdelt.requests.get')
    def test_retry_logic_on_failure(self, mock_get):
        """
        Test that the function retries exactly 3 times (1 initial + 2 retries)
        when encountering 500 errors, and returns the success response on the 3rd attempt.
        """
        # Setup mock responses: 2 failures (500), then 1 success
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = Exception("500 Internal Server Error")

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"EventCount": 150, "date": "2023-01-01"}
        mock_response_success.raise_for_status = Mock()  # No exception on success

        # Configure the mock to return 500 twice, then success
        mock_get.side_effect = [
            mock_response_500,
            mock_response_500,
            mock_response_success
        ]

        # Call the function
        result = fetch_with_retry("http://fake-gdelt-api.com/query", max_retries=3)

        # Assert that requests.get was called exactly 3 times
        self.assertEqual(mock_get.call_count, 3)

        # Assert the result is the success response data
        self.assertEqual(result, {"EventCount": 150, "date": "2023-01-01"})

        # Verify the call arguments (optional but good for completeness)
        expected_calls = [
            call("http://fake-gdelt-api.com/query"),
            call("http://fake-gdelt-api.com/query"),
            call("http://fake-gdelt-api.com/query")
        ]
        mock_get.assert_has_calls(expected_calls, any_order=False)

    @patch('data.fetch_gdelt.requests.get')
    def test_retry_exhaustion_raises_error(self, mock_get):
        """
        Test that the function raises an error after max_retries are exhausted.
        """
        # Setup mock to always fail
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = Exception("500 Internal Server Error")
        mock_get.return_value = mock_response_500

        # Assert that calling with max_retries=3 raises an exception
        with self.assertRaises(Exception):
            fetch_with_retry("http://fake-gdelt-api.com/query", max_retries=3)

        # Verify it was called 3 times (1 initial + 2 retries)
        self.assertEqual(mock_get.call_count, 3)

if __name__ == '__main__':
    unittest.main()