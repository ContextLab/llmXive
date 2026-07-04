"""
Unit tests for API retry logic in fetch_data.py
"""
import unittest
from unittest.mock import patch, MagicMock
import time
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from fetch_data import fetch_gdelt_sentiment

class TestFetchRetryLogic(unittest.TestCase):

    @patch('fetch_data.requests.get')
    def test_retry_on_timeout(self, mock_get):
        """Test that the function retries on request timeout."""
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout()
        ]
        
        # Mock the logger to avoid noise
        with patch('fetch_data.get_logger_instance') as mock_logger:
            result = fetch_gdelt_sentiment(
                start_date="20230101",
                end_date="20230102",
                output_path="/tmp/test.csv",
                max_retries=3,
                rate_limit_wait=0.1,
                backoff_factor=0.1
            )
        
        # Should have called get 3 times
        self.assertEqual(mock_get.call_count, 3)
        self.assertFalse(result)

    @patch('fetch_data.requests.get')
    def test_success_after_retry(self, mock_get):
        """Test that the function succeeds after a retry."""
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            MagicMock(status_code=200, json=lambda: {"data": {"events": []}})
        ]
        
        with patch('fetch_data.get_logger_instance'):
            result = fetch_gdelt_sentiment(
                start_date="20230101",
                end_date="20230102",
                output_path="/tmp/test.csv",
                max_retries=3,
                rate_limit_wait=0.1,
                backoff_factor=0.1
            )
        
        self.assertEqual(mock_get.call_count, 2)
        self.assertTrue(result)

    @patch('fetch_data.requests.get')
    def test_rate_limit_handling(self, mock_get):
        """Test that the function waits on 429 and retries."""
        mock_response_429 = MagicMock(status_code=429)
        mock_response_200 = MagicMock(status_code=200, json=lambda: {"data": {"events": []}})
        
        mock_get.side_effect = [
            mock_response_429,
            mock_response_200
        ]
        
        with patch('fetch_data.get_logger_instance'):
            # We need to ensure the sleep happens, but we don't want to wait too long in tests
            # The function sleeps for rate_limit_wait (0.1s)
            result = fetch_gdelt_sentiment(
                start_date="20230101",
                end_date="20230102",
                output_path="/tmp/test.csv",
                max_retries=3,
                rate_limit_wait=0.1,
                backoff_factor=0.1
            )
        
        self.assertEqual(mock_get.call_count, 2)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
