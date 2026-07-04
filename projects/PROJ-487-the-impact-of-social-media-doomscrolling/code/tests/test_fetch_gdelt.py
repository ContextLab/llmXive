import unittest
import time
from unittest.mock import patch, MagicMock, call
import sys
import os

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.logging import get_logger

class TestGDELTRetryLogic(unittest.TestCase):
    """
    Unit tests for GDELT API retry logic with configurable maximum attempts.
    Tests verify that the fetch function respects the max_retries parameter,
    logs appropriate warnings on failure, and raises exceptions after exhausting retries.
    """

    def setUp(self):
        self.logger = get_logger(__name__)
        self.mock_url = "https://api.gdeltproject.org/api/v2/doc/doc?query=test"
        
    @patch('code.data.fetch_gdelt.requests.get')
    def test_success_on_first_attempt(self, mock_get):
        """Test successful fetch on first attempt does not retry."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"event": 1}]}
        mock_get.return_value = mock_response

        # Import the function to test (assuming it's in fetch_gdelt.py)
        from code.data.fetch_gdelt import fetch_gdelt_events

        # Act
        result = fetch_gdelt_events(
            start_date="2023-01-01",
            end_date="2023-01-02",
            max_retries=3
        )

        # Assert
        mock_get.assert_called_once()
        self.assertEqual(len(result), 1)

    @patch('code.data.fetch_gdelt.requests.get')
    def test_retry_on_transient_error(self, mock_get):
        """Test that transient errors (503) trigger retries up to max_retries."""
        # Arrange
        mock_fail_response = MagicMock()
        mock_fail_response.status_code = 503
        
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"data": [{"event": 1}]}

        # Sequence: Fail, Fail, Success
        mock_get.side_effect = [mock_fail_response, mock_fail_response, mock_success_response]

        from code.data.fetch_gdelt import fetch_gdelt_events

        # Act
        result = fetch_gdelt_events(
            start_date="2023-01-01",
            end_date="2023-01-02",
            max_retries=3
        )

        # Assert
        # Should have been called 3 times (2 failures + 1 success)
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(len(result), 1)

    @patch('code.data.fetch_gdelt.requests.get')
    def test_exhaust_retries_raises_exception(self, mock_get):
        """Test that failing all retries raises an exception."""
        # Arrange
        mock_fail_response = MagicMock()
        mock_fail_response.status_code = 503
        
        # Always fail
        mock_get.return_value = mock_fail_response

        from code.data.fetch_gdelt import fetch_gdelt_events

        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            fetch_gdelt_events(
                start_date="2023-01-01",
                end_date="2023-01-02",
                max_retries=3
            )
        
        self.assertIn("Failed after 3 attempts", str(context.exception))

    @patch('code.data.fetch_gdelt.requests.get')
    def test_retry_count_matches_config(self, mock_get):
        """Test that the number of attempts strictly matches the configured max_retries."""
        # Arrange
        mock_fail_response = MagicMock()
        mock_fail_response.status_code = 500
        mock_get.return_value = mock_fail_response

        from code.data.fetch_gdelt import fetch_gdelt_events

        # Act: Try with 5 retries
        try:
            fetch_gdelt_events(
                start_date="2023-01-01",
                end_date="2023-01-02",
                max_retries=5
            )
        except RuntimeError:
            pass

        # Assert
        # Should have been called exactly 5 times (initial + 4 retries)
        # Note: Implementation usually counts initial attempt as 1, then retries.
        # If max_retries=5, total calls should be 5.
        self.assertEqual(mock_get.call_count, 5)

    @patch('code.data.fetch_gdelt.requests.get')
    def test_connection_error_triggers_retry(self, mock_get):
        """Test that ConnectionError exceptions trigger retry logic."""
        # Arrange
        import requests
        
        # Sequence: ConnectionError, ConnectionError, Success
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Network error"),
            requests.exceptions.ConnectionError("Network error"),
            MagicMock(status_code=200, json=lambda: {"data": [{"event": 1}]})
        ]

        from code.data.fetch_gdelt import fetch_gdelt_events

        # Act
        result = fetch_gdelt_events(
            start_date="2023-01-01",
            end_date="2023-01-02",
            max_retries=3
        )

        # Assert
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(len(result), 1)

    @patch('code.data.fetch_gdelt.requests.get')
    def test_timeout_error_triggers_retry(self, mock_get):
        """Test that Timeout exceptions trigger retry logic."""
        # Arrange
        import requests
        
        mock_get.side_effect = [
            requests.exceptions.Timeout("Request timed out"),
            MagicMock(status_code=200, json=lambda: {"data": [{"event": 1}]})
        ]

        from code.data.fetch_gdelt import fetch_gdelt_events

        # Act
        result = fetch_gdelt_events(
            start_date="2023-01-01",
            end_date="2023-01-02",
            max_retries=3
        )

        # Assert
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(len(result), 1)

    @patch('code.data.fetch_gdelt.requests.get')
    def test_non_retryable_status_code_no_retry(self, mock_get):
        """Test that 4xx errors (client errors) do not trigger retries."""
        # Arrange
        mock_fail_response = MagicMock()
        mock_fail_response.status_code = 404
        mock_get.return_value = mock_fail_response

        from code.data.fetch_gdelt import fetch_gdelt_events

        # Act & Assert
        with self.assertRaises(RuntimeError):
            fetch_gdelt_events(
                start_date="2023-01-01",
                end_date="2023-01-02",
                max_retries=3
            )
        
        # Should only be called once, as 404 is not retryable
        self.assertEqual(mock_get.call_count, 1)

    @patch('code.data.fetch_gdelt.time.sleep')
    @patch('code.data.fetch_gdelt.requests.get')
    def test_backoff_delay_between_retries(self, mock_get, mock_sleep):
        """Test that a delay occurs between retry attempts."""
        # Arrange
        mock_fail_response = MagicMock(status_code=503)
        mock_success_response = MagicMock(status_code=200, json=lambda: {"data": []})
        mock_get.side_effect = [mock_fail_response, mock_success_response]

        from code.data.fetch_gdelt import fetch_gdelt_events

        # Act
        fetch_gdelt_events(
            start_date="2023-01-01",
            end_date="2023-01-02",
            max_retries=3
        )

        # Assert
        # Should have slept at least once (between fail and success)
        mock_sleep.assert_called_once()

if __name__ == '__main__':
    unittest.main()