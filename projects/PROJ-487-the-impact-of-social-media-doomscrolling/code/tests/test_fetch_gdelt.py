import unittest
import time
from unittest.mock import patch, MagicMock, call, Mock
import sys
import os

# Add the parent directory to the path to allow importing code modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logging import get_logger
import logging

# Import the function to be tested from the actual implementation file
from data.fetch_gdelt import fetch_with_retry

class TestGDELTRetryLogic(unittest.TestCase):
    """
    Unit tests for the GDELT fetch retry logic.
    Uses 'responses' simulation logic (mocked via unittest.mock here to avoid
    external dependency strictness in the test file itself, though 'responses'
    is in requirements).
    """

    def setUp(self):
        self.logger = get_logger(__name__)
        self.logger.setLevel(logging.DEBUG)

    @patch('data.fetch_gdelt.requests.get')
    def test_retry_logic_on_failure(self, mock_get):
        """
        Test that the function retries exactly 3 times on failure before succeeding.
        Scenario: 2 failed requests (500 errors) followed by a success.
        Expected: mock.call_count == 3 (2 failures + 1 success)
        """
        # Setup the mock to simulate 2 failures then 1 success
        # First call: 500 error
        # Second call: 500 error
        # Third call: Success (200)
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = Exception("Server Error")

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"data": "success"}
        mock_response_success.raise_for_status.return_value = None

        # Configure side_effect to return fail, fail, success
        mock_get.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]

        # Execute the function
        # We pass a dummy URL and max_retries=2 (meaning 2 retries + 1 initial = 3 total attempts)
        try:
            result = fetch_with_retry("http://dummy-url.com", max_retries=2, backoff_factor=0.1)
        except Exception:
            # If the logic raises on the last failure, we check call count before that
            # But based on standard retry logic, it should succeed on the 3rd try
            pass

        # Verify the function was called exactly 3 times
        self.assertEqual(mock_get.call_count, 3, "Expected 3 calls: 2 failures + 1 success")

        # Verify the last call returned the success response
        self.assertEqual(result.status_code, 200)

    @patch('data.fetch_gdelt.requests.get')
    def test_retry_exhaustion_raises_error(self, mock_get):
        """
        Test that the function raises an error after exhausting retries.
        Scenario: All requests fail.
        Expected: Raises an exception after 3 calls (1 initial + 2 retries).
        """
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = Exception("Server Error")

        # Configure side_effect to always fail
        mock_get.side_effect = mock_response_fail

        # Execute the function
        with self.assertRaises(Exception) as context:
            fetch_with_retry("http://dummy-url.com", max_retries=2, backoff_factor=0.1)

        # Verify the function was called exactly 3 times (1 initial + 2 retries)
        self.assertEqual(mock_get.call_count, 3)
        self.assertIn("Server Error", str(context.exception))

if __name__ == '__main__':
    unittest.main()