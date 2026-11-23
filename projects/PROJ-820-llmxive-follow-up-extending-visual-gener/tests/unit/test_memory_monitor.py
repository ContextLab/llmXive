"""
Unit tests for code/generation/memory_monitor.py
"""

import unittest
import time
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from generation.memory_monitor import (
    get_memory_usage_mb,
    check_memory_limit,
    enforce_memory_limit,
    TimeLimitEnforcer,
    MemoryLimitExceededError,
    TimeLimitExceededError
)


class TestMemoryFunctions(unittest.TestCase):
    """Tests for memory utility functions."""

    def test_get_memory_usage_mb_returns_number(self):
        """Verify that get_memory_usage_mb returns a numeric value."""
        mem = get_memory_usage_mb()
        self.assertIsInstance(mem, (int, float))
        self.assertGreater(mem, 0)

    def test_check_memory_limit_true(self):
        """Test check_memory_limit returns True when under limit."""
        # Current usage should be well under 1TB
        self.assertTrue(check_memory_limit(1000000))

    def test_check_memory_limit_false(self):
        """Test check_memory_limit returns False when over limit."""
        # Current usage is definitely over 0 MB
        self.assertFalse(check_memory_limit(0))

    def test_enforce_memory_limit_success(self):
        """Test enforce_memory_limit does not raise when under limit."""
        try:
            enforce_memory_limit(1000000)
        except MemoryLimitExceededError:
            self.fail("enforce_memory_limit raised unexpectedly")

    def test_enforce_memory_limit_failure(self):
        """Test enforce_memory_limit raises when over limit."""
        with self.assertRaises(MemoryLimitExceededError):
            enforce_memory_limit(0)


class TestTimeLimitEnforcer(unittest.TestCase):
    """Tests for TimeLimitEnforcer context manager."""

    def test_context_manager_success(self):
        """Test context manager completes successfully within limit."""
        start = time.time()
        with TimeLimitEnforcer(5.0, "Test"):
            time.sleep(0.1)
        elapsed = time.time() - start
        self.assertLess(elapsed, 1.0)

    def test_context_manager_timeout(self):
        """Test context manager raises TimeLimitExceededError on timeout."""
        with self.assertRaises(TimeLimitExceededError):
            with TimeLimitEnforcer(0.05, "Test"):
                time.sleep(0.2)

    def test_check_method_success(self):
        """Test check() method does not raise when under limit."""
        with TimeLimitEnforcer(5.0, "Test") as enforcer:
            time.sleep(0.1)
            enforcer.check()  # Should not raise

    def test_check_method_timeout(self):
        """Test check() method raises when over limit."""
        with TimeLimitEnforcer(0.05, "Test") as enforcer:
            time.sleep(0.2)
            with self.assertRaises(TimeLimitExceededError):
                enforcer.check()


if __name__ == '__main__':
    unittest.main()