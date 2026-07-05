import time
import unittest
from unittest.mock import patch, MagicMock, Mock
from requests.exceptions import RequestException

from utils.api_client import RateLimitedSession, fetch_with_backoff


class TestRetryLogic(unittest.TestCase):
    """Unit tests for the API client retry logic, specifically for 429 errors."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_url = "https://api.example.com/data"
        self.test_payload = {"key": "value"}

    @patch('utils.api_client.requests.Session')
    def test_retry_logic_triggers_on_429_error(self, mock_session_class):
        """
        Verify that fetch_with_backoff triggers retry logic when a 429 Too Many Requests
        error is encountered, and eventually succeeds after retries.
        """
        # Mock the session instance
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Create a mock response that returns 429 twice, then 200
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = RequestException("429 Too Many Requests")

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"status": "success"}

        # Configure the side effect sequence: 429, 429, 200
        mock_session.get.side_effect = [
            mock_response_429,
            mock_response_429,
            mock_response_success
        ]

        # Mock time.sleep to avoid actual waiting during the test
        with patch('utils.api_client.time.sleep') as mock_sleep:
            # Execute the function
            result = fetch_with_backoff(self.test_url, max_retries=3, base_delay=0.01)

        # Assertions
        # 1. Verify the request was made 3 times (2 failures + 1 success)
        self.assertEqual(mock_session.get.call_count, 3)

        # 2. Verify time.sleep was called for the retries (2 times)
        self.assertEqual(mock_sleep.call_count, 2)

        # 3. Verify the final result is the successful response data
        self.assertEqual(result, {"status": "success"})

    @patch('utils.api_client.requests.Session')
    def test_retry_logic_raises_after_max_retries(self, mock_session_class):
        """
        Verify that fetch_with_backoff raises an exception after exhausting all retries
        on persistent 429 errors.
        """
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Create a mock response that always returns 429
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = RequestException("429 Too Many Requests")

        mock_session.get.return_value = mock_response_429

        with patch('utils.api_client.time.sleep'):
            with self.assertRaises(RequestException):
                fetch_with_backoff(self.test_url, max_retries=2, base_delay=0.01)

        # Verify the request was made exactly max_retries + 1 times (initial + retries)
        # Actually, the logic usually does: try -> fail -> retry -> fail -> retry -> fail -> raise
        # With max_retries=2, it tries 1 (initial) + 2 (retries) = 3 times.
        self.assertEqual(mock_session.get.call_count, 3)

    def test_rate_limited_session_configuration(self):
        """
        Verify that RateLimitedSession is configured with the correct retry strategy.
        """
        session = RateLimitedSession()

        # Check that the adapter is mounted for http and https
        self.assertIn('http://', session.adapters)
        self.assertIn('https://', session.adapters)

        # Verify the retry configuration
        adapter = session.adapters['http://']
        self.assertIsInstance(adapter.max_retries, Retry)
        self.assertIn(429, adapter.max_retries.status_forcelist)
        self.assertIn(503, adapter.max_retries.status_forcelist)
        self.assertIn(500, adapter.max_retries.status_forcelist)
        self.assertGreater(adapter.max_retries.backoff_factor, 0)
        self.assertTrue(adapter.max_retries.raise_on_status)