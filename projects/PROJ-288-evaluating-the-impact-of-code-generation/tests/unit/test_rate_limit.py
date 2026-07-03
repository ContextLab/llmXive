"""
Unit tests for the Token Bucket rate limiter.

This module explicitly tests the exponential backoff logic with specific parameters:
- Initial backoff: 1 second
- Maximum backoff: 60 seconds

These parameters are defined in code/config.py (FR-007).
"""
import time
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.config import BACKOFF_INITIAL, BACKOFF_MAX, RATE_LIMIT_HOURLY
from code.data.rate_limiter import TokenBucketRateLimiter


class TestTokenBucketRateLimiter(unittest.TestCase):
    """Test cases for the TokenBucketRateLimiter class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a limiter with a high capacity for testing logic without waiting
        self.limiter = TokenBucketRateLimiter(
            capacity=100,
            refill_rate=100,
            initial_backoff=BACKOFF_INITIAL,
            max_backoff=BACKOFF_MAX
        )

    def test_initial_capacity(self):
        """Test that the bucket starts with full capacity."""
        self.assertEqual(self.limiter.tokens, 100)

    def test_consume_success(self):
        """Test successful token consumption."""
        result = self.limiter.consume(1)
        self.assertTrue(result)
        self.assertEqual(self.limiter.tokens, 99)

    def test_consume_failure(self):
        """Test token consumption when bucket is empty."""
        # Drain the bucket
        self.limiter.tokens = 0
        result = self.limiter.consume(1)
        self.assertFalse(result)

    def test_backoff_calculation_initial(self):
        """Test that initial backoff matches FR-007 specification (1 second)."""
        # Simulate a retry attempt (attempt 1)
        backoff = self.limiter._calculate_backoff(1)
        # Formula: min(initial * (2 ** (attempt - 1)), max)
        expected = min(BACKOFF_INITIAL * (2 ** 0), BACKOFF_MAX)
        self.assertEqual(backoff, expected)
        self.assertEqual(backoff, 1.0)

    def test_backoff_calculation_exponential_growth(self):
        """Test exponential growth of backoff time."""
        # Attempt 2: 1 * 2^1 = 2
        self.assertEqual(self.limiter._calculate_backoff(2), 2.0)
        # Attempt 3: 1 * 2^2 = 4
        self.assertEqual(self.limiter._calculate_backoff(3), 4.0)
        # Attempt 4: 1 * 2^3 = 8
        self.assertEqual(self.limiter._calculate_backoff(4), 8.0)

    def test_backoff_capped_at_maximum(self):
        """Test that backoff does not exceed the maximum defined in FR-007 (60 seconds)."""
        # Calculate for a high attempt number where 2^attempt > 60
        # 2^6 = 64, so attempt 7 should be capped
        backoff_attempt_7 = self.limiter._calculate_backoff(7)
        self.assertEqual(backoff_attempt_7, BACKOFF_MAX)
        self.assertEqual(backoff_attempt_7, 60.0)

        # Verify subsequent attempts also stay at max
        self.assertEqual(self.limiter._calculate_backoff(10), 60.0)
        self.assertEqual(self.limiter._calculate_backoff(20), 60.0)

    def test_wait_logic_with_mock_time(self):
        """Test that the wait method actually sleeps for the calculated duration."""
        # Mock time.sleep to avoid actual waiting during tests
        with patch('code.data.rate_limiter.time.sleep') as mock_sleep:
            # Force a state where we need to wait (empty bucket)
            self.limiter.tokens = 0
            
            # Simulate a wait for attempt 3 (should be 4 seconds)
            self.limiter.wait(3)
            
            # Verify sleep was called with the correct duration
            mock_sleep.assert_called_once_with(4.0)

    def test_config_parameters_match_fr007(self):
        """Verify that config constants match the FR-007 requirements."""
        self.assertEqual(BACKOFF_INITIAL, 1, "FR-007 requires initial backoff of 1 second")
        self.assertEqual(BACKOFF_MAX, 60, "FR-007 requires maximum backoff of 60 seconds")
        self.assertIsInstance(RATE_LIMIT_HOURLY, int, "Rate limit must be an integer")


if __name__ == '__main__':
    unittest.main()