import unittest
import time
from unittest.mock import patch, MagicMock, call, Mock
import sys
import os
from utils.logging import get_logger

# Add parent directory to path to allow imports if running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.fetch_gdelt import fetch_with_retry

class TestGDELTRetryLogic(unittest.TestCase):
    """
    Unit test for GDELT fetch retry logic.
    Uses 'responses' concept via unittest.mock to simulate network failures.
    """

    @patch('data.fetch_gdelt.requests.get')
    def test_retry_logic_on_failure(self, mock_get):
        """
        Assert that the function retries exactly 3 times (total 4 calls: 1 initial + 3 retries)
        when the first two requests fail with 500 errors, and the third attempt succeeds.
        """
        # Setup mock responses
        # First call: 500 error
        mock_response_1 = Mock()
        mock_response_1.status_code = 500
        mock_response_1.ok = False
        mock_response_1.raise_for_status.side_effect = Exception("Server Error")

        # Second call: 500 error
        mock_response_2 = Mock()
        mock_response_2.status_code = 500
        mock_response_2.ok = False
        mock_response_2.raise_for_status.side_effect = Exception("Server Error")

        # Third call: Success
        mock_response_3 = Mock()
        mock_response_3.status_code = 200
        mock_response_3.ok = True
        mock_response_3.text = '{"Data": "Success"}'
        mock_response_3.json.return_value = {"Data": "Success"}

        # Configure the side_effect sequence
        mock_get.side_effect = [mock_response_1, mock_response_2, mock_response_3]

        # Execute the function
        # Note: fetch_with_retry expects url, params, max_retries, backoff_factor
        # We assume default backoff_factor is small enough for the test to run quickly
        result = fetch_with_retry(
            url="http://fake-gdelt-api.com/query",
            params={"Action": "Count"},
            max_retries=3,
            backoff_factor=0.01
        )

        # Assertions
        # 1. Verify the request was called 4 times (1 initial + 3 retries)
        self.assertEqual(mock_get.call_count, 4)

        # 2. Verify the calls were made in sequence
        expected_calls = [
            call(url="http://fake-gdelt-api.com/query", params={"Action": "Count"}),
            call(url="http://fake-gdelt-api.com/query", params={"Action": "Count"}),
            call(url="http://fake-gdelt-api.com/query", params={"Action": "Count"}),
            call(url="http://fake-gdelt-api.com/query", params={"Action": "Count"})
        ]
        mock_get.assert_has_calls(expected_calls)

        # 3. Verify the result is the successful response content
        self.assertEqual(result, {"Data": "Success"})

    @patch('data.fetch_gdelt.requests.get')
    def test_max_retries_exceeded(self, mock_get):
        """
        Assert that the function raises an exception after exhausting retries.
        """
        # Setup mock to always fail
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.ok = False
        mock_response_fail.raise_for_status.side_effect = Exception("Server Error")
        mock_get.return_value = mock_response_fail

        # Expect the function to raise an exception
        with self.assertRaises(Exception):
            fetch_with_retry(
                url="http://fake-gdelt-api.com/query",
                params={"Action": "Count"},
                max_retries=3,
                backoff_factor=0.01
            )

        # Verify it was called 4 times (1 initial + 3 retries)
        self.assertEqual(mock_get.call_count, 4)

if __name__ == '__main__':
    unittest.main()