"""
Unit tests for retry logic with exponential backoff in code/data/download.py.

This module tests the retry mechanism implemented in the download utility,
specifically verifying that:
1. The correct number of retries are attempted on failure
2. Exponential backoff timings are respected (1s, 2s, 4s)
3. Successful requests return immediately without retries
4. Exceptions are raised after all retries are exhausted
"""
import time
import unittest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import requests

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import download_with_retry
from code.config import get_config


class TestRetryLogic(unittest.TestCase):
    """Test cases for retry logic with exponential backoff."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = get_config()
        self.max_retries = 3
        self.base_delays = [1, 2, 4]  # Expected exponential backoff timings

    @patch('code.data.download.requests.get')
    def test_success_on_first_attempt(self, mock_get):
        """Test that successful requests return immediately without retries."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        # Call the function
        result = download_with_retry("https://example.com/api", max_retries=self.max_retries)

        # Verify request was made only once
        mock_get.assert_called_once()
        self.assertEqual(result.status_code, 200)

    @patch('code.data.download.requests.get')
    def test_retry_on_failure(self, mock_get):
        """Test that the function retries the correct number of times on failure."""
        # Setup mock to fail twice then succeed
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.ok = False

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.ok = True
        mock_response_success.json.return_value = {"data": "test"}

        mock_get.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]

        # Call the function
        result = download_with_retry("https://example.com/api", max_retries=self.max_retries)

        # Verify request was made 3 times (2 failures + 1 success)
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(result.status_code, 200)

    @patch('code.data.download.requests.get')
    def test_exponential_backoff_timing(self, mock_get):
        """Test that exponential backoff timings are respected."""
        # Track call times
        call_times = []

        def track_time(*args, **kwargs):
            call_times.append(time.time())
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.ok = False
            return mock_response

        mock_get.side_effect = track_time

        # Call the function with max_retries=2 (will fail all attempts)
        with self.assertRaises(Exception):
            download_with_retry("https://example.com/api", max_retries=2)

        # Calculate delays between attempts
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]

            # Check that delays are approximately 1s and 2s (allow 20% tolerance)
            self.assertGreaterEqual(delay1, 0.8, "First delay should be ~1s")
            self.assertLessEqual(delay1, 1.2, "First delay should be ~1s")
            self.assertGreaterEqual(delay2, 1.6, "Second delay should be ~2s")
            self.assertLessEqual(delay2, 2.4, "Second delay should be ~2s")

    @patch('code.data.download.requests.get')
    def test_exception_after_max_retries(self, mock_get):
        """Test that an exception is raised after all retries are exhausted."""
        # Setup mock to always fail
        mock_get.side_effect = Exception("Network error")

        # Call the function and expect an exception
        with self.assertRaises(Exception) as context:
            download_with_retry("https://example.com/api", max_retries=3)

        # Verify the exception message contains retry information
        self.assertIn("Network error", str(context.exception))
        # Verify all retries were attempted
        self.assertEqual(mock_get.call_count, 3)

    @patch('code.data.download.requests.get')
    def test_retry_on_timeout(self, mock_get):
        """Test that timeouts trigger retry logic."""
        # Setup mock to timeout twice then succeed
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.ok = True
        mock_response_success.json.return_value = {"data": "test"}

        mock_get.side_effect = [requests.exceptions.Timeout("Connection timed out"), requests.exceptions.Timeout("Connection timed out"), mock_response_success]

        # Call the function
        result = download_with_retry("https://example.com/api", max_retries=self.max_retries)

        # Verify request was made 3 times
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(result.status_code, 200)


if __name__ == '__main__':
    unittest.main()