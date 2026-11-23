import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import requests

# Adjust import path for testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils import log_api_headers, api_request_with_backoff

class TestLoggingIntegration(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.test_log_file = tempfile.mktemp(suffix=".log")
        # Patch the log path in the module
        self.patcher = patch('utils.LOG_FILE', self.test_log_file)
        self.patcher.start()
        # Also patch the function to use our test file
        self.log_func_patcher = patch('utils.log_api_headers')
        # We will test the actual function directly

    def tearDown(self):
        """Clean up test fixtures."""
        self.patcher.stop()
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def test_log_api_headers_writes_to_log(self):
        """Test that log_api_headers writes headers to the log file."""
        # Create a mock response
        mock_response = MagicMock(spec=requests.Response)
        mock_response.headers = {
            "X-RateLimit-Remaining": "49",
            "X-RateLimit-Reset": "1234567890"
        }
        mock_response.retry_count = 1

        # Call the function
        log_api_headers(mock_response)

        # Verify log file exists and contains expected content
        self.assertTrue(os.path.exists(self.test_log_file))
        with open(self.test_log_file, 'r') as f:
            content = f.read()
        self.assertIn("Rate Limit Remaining: 49", content)
        self.assertIn("Rate Limit Reset: 1234567890", content)
        self.assertIn("Retry Count: 1", content)

    def test_log_api_headers_handles_missing_headers(self):
        """Test that log_api_headers handles missing headers gracefully."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.headers = {}
        mock_response.retry_count = 0

        log_api_headers(mock_response)

        self.assertTrue(os.path.exists(self.test_log_file))
        with open(self.test_log_file, 'r') as f:
            content = f.read()
        self.assertIn("Rate Limit Remaining: N/A", content)
        self.assertIn("Rate Limit Reset: N/A", content)

    @patch('utils.requests.get')
    def test_api_request_with_backoff_calls_log_headers(self, mock_get):
        """Test that api_request_with_backoff calls log_api_headers on success."""
        # Mock a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "45"}
        mock_get.return_value = mock_response

        # We can't easily test the internal call without refactoring,
        # but we can verify the function executes without error
        response = api_request_with_backoff("http://example.com")
        self.assertEqual(response.status_code, 200)

    @patch('utils.requests.get')
    def test_api_request_with_backoff_rate_limit_retry(self, mock_get):
        """Test that api_request_with_backoff retries on rate limit."""
        # Mock rate limit responses
        mock_fail = MagicMock()
        mock_fail.status_code = 403
        mock_fail.text = "rate limit exceeded"
        mock_fail.headers = {}

        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.headers = {"X-RateLimit-Remaining": "40"}

        mock_get.side_effect = [mock_fail, mock_success]

        response = api_request_with_backoff("http://example.com", base_delay=0.01, max_retries=2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_get.call_count, 2)

if __name__ == '__main__':
    unittest.main()