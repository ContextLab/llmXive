"""
Unit tests for the Global Attempt Counter Logic (T090).
"""
import unittest
import sys
import os

# Add the project root to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pipeline.attempt_tracker import check_attempt_limit, AttemptLimitExceeded


class TestAttemptTracker(unittest.TestCase):
    """Tests for the attempt tracker logic."""

    def test_attempt_within_limit(self):
        """Test that no exception is raised when below the limit."""
        # Default max_attempts is 3
        check_attempt_limit(1)
        check_attempt_limit(2)
        check_attempt_limit(3, max_attempts=5)
        check_attempt_limit(4, max_attempts=5)
        # Should not raise
        self.assertTrue(True)

    def test_attempt_at_limit_raises(self):
        """Test that exception is raised when current_attempt >= max_attempts."""
        with self.assertRaises(AttemptLimitExceeded) as context:
            # Default max is 3, so 3 should raise
            check_attempt_limit(3)
        
        self.assertIn("Attempt limit exceeded", str(context.exception))
        self.assertEqual(context.exception.current_attempt, 3)
        self.assertEqual(context.exception.max_attempts, 3)

    def test_attempt_exceeds_limit_raises(self):
        """Test that exception is raised when current_attempt > max_attempts."""
        with self.assertRaises(AttemptLimitExceeded) as context:
            check_attempt_limit(4)
        
        self.assertIn("Attempt limit exceeded", str(context.exception))
        self.assertEqual(context.exception.current_attempt, 4)
        self.assertEqual(context.exception.max_attempts, 3)

    def test_custom_max_attempts(self):
        """Test with a custom max_attempts value."""
        # Should pass for 2 with max 3
        check_attempt_limit(2, max_attempts=3)
        
        # Should raise for 3 with max 3
        with self.assertRaises(AttemptLimitExceeded):
            check_attempt_limit(3, max_attempts=3)

    def test_4th_attempt_raises_exception(self):
        """
        Verification: Assert exception is raised on 4th attempt.
        This specifically tests the scenario described in T090 requirements.
        """
        # If max_attempts is 3, the 4th attempt (index 4) must fail
        with self.assertRaises(AttemptLimitExceeded):
            check_attempt_limit(4, max_attempts=3)

    def test_message_generation(self):
        """Test the helper function for generating status messages."""
        # Import here to avoid circular if needed, though it's in same file
        from pipeline.attempt_tracker import get_attempt_message

        self.assertEqual(get_attempt_message(1, 3), "Attempt 1/3.")
        self.assertEqual(get_attempt_message(2, 3), "Attempt 2/3.")
        self.assertEqual(get_attempt_message(3, 3), "Attempt limit reached (3/3). Terminating.")
        self.assertEqual(get_attempt_message(2, 3), "Final attempt allowed (2/3).") # Logic check: 2 is max-1