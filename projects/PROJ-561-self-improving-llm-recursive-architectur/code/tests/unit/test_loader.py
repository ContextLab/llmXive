import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pipeline.loader import with_exponential_backoff, HFTransientError, load_local_dataset

class TestDatasetLoaders(unittest.TestCase):

    def test_fail_fast_missing_file(self):
        """
        Verify that loading a non-existent dataset raises FileNotFoundError
        with the exact message and does NOT fallback to synthetic data.
        """
        non_existent_path = "data/raw/missing.json"
        
        with self.assertRaises(FileNotFoundError) as context:
            load_local_dataset(non_existent_path)
        
        self.assertEqual(str(context.exception), f"Dataset file not found: {non_existent_path}")

    @patch('time.sleep')
    def test_retry_logic_on_network_error(self, mock_sleep):
        """
        Verify that simulated network errors trigger retry logic.
        """
        call_count = 0
        max_calls = 3

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < max_calls:
                raise ConnectionError("Simulated network error")
            return "Success"

        decorated_func = with_exponential_backoff(failing_func)

        # Reset mock to count calls
        mock_sleep.reset_mock()

        result = decorated_func()
        
        self.assertEqual(result, "Success")
        # Should have retried 2 times (failed 1, 2, succeeded 3)
        self.assertEqual(call_count, max_calls)
        # Should have slept 2 times (after 1st and 2nd failure)
        self.assertEqual(mock_sleep.call_count, 2)
        # Verify exponential backoff delays (30s, 60s)
        mock_sleep.assert_any_call(30)
        mock_sleep.assert_any_call(60)

    def test_immediate_failure_after_max_retries(self):
        """
        Verify that if all retries fail, the exception is raised.
        """
        def always_fails():
            raise HFTransientError("Always fails")

        decorated_func = with_exponential_backoff(always_fails)

        with self.assertRaises(HFTransientError):
            decorated_func()
