"""
Unit tests for data ingestion module, specifically focusing on API rate limit handling.
"""
import time
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os

# Add the code directory to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data_ingestion import exponential_backoff


class TestExponentialBackoff(unittest.TestCase):
    """Tests for the exponential backoff mechanism in data ingestion."""

    def setUp(self):
        """Set up test fixtures."""
        self.max_retries = 3
        self.base_delay = 0.1  # Short delay for testing

    @patch('data_ingestion.time.sleep')
    def test_api_backoff_retries_on_rate_limit(self, mock_sleep):
        """
        Test that exponential_backoff correctly retries on rate limit errors (429).
        
        Verifies:
        1. The function retries up to max_retries times when 429 is returned.
        2. The delay between retries follows exponential backoff (base * 2^attempt).
        3. The function raises the final error after exhausting retries.
        """
        attempt_counter = 0

        def failing_side_effect(*args, **kwargs):
            nonlocal attempt_counter
            attempt_counter += 1
            if attempt_counter <= self.max_retries:
                # Simulate a 429 Rate Limit error
                error = Exception("429 Client Error: Too Many Requests")
                error.response = MagicMock()
                error.response.status_code = 429
                raise error
            return "Success"

        mock_response_func = MagicMock(side_effect=failing_side_effect)

        with self.assertRaises(Exception) as context:
            exponential_backoff(
                mock_response_func,
                max_retries=self.max_retries,
                base_delay=self.base_delay
            )

        # Verify the error was a 429
        self.assertEqual(context.exception.response.status_code, 429)

        # Verify the function was called max_retries + 1 times (initial + retries)
        self.assertEqual(mock_response_func.call_count, self.max_retries + 1)

        # Verify sleep was called with exponential delays: 0.1, 0.2, 0.4
        expected_delays = [
            self.base_delay * (2 ** 0),
            self.base_delay * (2 ** 1),
            self.base_delay * (2 ** 2)
        ]
        # Extract the actual sleep calls
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]

        self.assertEqual(actual_delays, expected_delays)

    @patch('data_ingestion.time.sleep')
    def test_backoff_stops_on_success(self, mock_sleep):
        """
        Test that backoff stops immediately if the function succeeds before max retries.
        """
        call_count = 0

        def eventually_succeeds(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                error = Exception("500 Server Error")
                error.response = MagicMock()
                error.response.status_code = 500
                raise error
            return "Success"

        mock_response_func = MagicMock(side_effect=eventually_succeeds)

        result = exponential_backoff(
            mock_response_func,
            max_retries=self.max_retries,
            base_delay=self.base_delay
        )

        self.assertEqual(result, "Success")
        # Should have retried twice (fail, fail, success)
        self.assertEqual(mock_response_func.call_count, 3)
        # Sleep should only have been called twice (after 1st and 2nd failure)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('data_ingestion.time.sleep')
    def test_non_retryable_error_raises_immediately(self, mock_sleep):
        """
        Test that non-429/5xx errors are raised immediately without retrying.
        """
        def value_error(*args, **kwargs):
            raise ValueError("Invalid input")

        mock_response_func = MagicMock(side_effect=value_error)

        with self.assertRaises(ValueError):
            exponential_backoff(
                mock_response_func,
                max_retries=self.max_retries,
                base_delay=self.base_delay
            )

        # Should only be called once
        self.assertEqual(mock_response_func.call_count, 1)
        # Sleep should never be called
        self.assertEqual(mock_sleep.call_count, 0)


if __name__ == '__main__':
    unittest.main()