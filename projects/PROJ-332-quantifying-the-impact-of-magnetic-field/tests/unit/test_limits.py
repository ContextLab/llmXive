"""
Unit tests for the limits module (T006).
"""
import pytest
import time
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path if running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.utils.limits import timeout_guard, MemoryLimitError, get_memory_usage_mb, check_memory_usage

class TestTimeoutGuard:
    def test_timeout_guard_completes_in_time(self):
        """Test that a function completing within the limit runs successfully."""
        def quick_func():
            return "done"
        
        with timeout_guard(5, "Too slow"):
            result = quick_func()
        assert result == "done"

    def test_timeout_guard_raises_on_timeout(self):
        """Test that a function taking too long raises TimeoutError."""
        # This test might be flaky on Windows if SIGALRM is not supported.
        # We skip it if not supported.
        if not hasattr(__import__('signal'), 'SIGALRM'):
            pytest.skip("SIGALRM not available on this platform")

        def slow_func():
            time.sleep(10)
            return "done"

        with pytest.raises(Exception) as exc_info:
            with timeout_guard(1, "Too slow"):
                slow_func()
        
        assert "timeout" in str(exc_info.value).lower() or "Too slow" in str(exc_info.value)

class TestMemoryGuard:
    def test_check_memory_usage_below_limit(self):
        """Test that check_memory_usage passes when under limit."""
        # Get current usage, add a buffer
        current = get_memory_usage_mb()
        # Limit should be higher than current
        limit = current + 1000 
        try:
            check_memory_usage(limit)
            # Should not raise
        except MemoryLimitError:
            pytest.fail("check_memory_usage raised unexpectedly")

    def test_check_memory_usage_raises_on_exceed(self):
        """Test that check_memory_usage raises when over limit."""
        # Set a very low limit that current usage surely exceeds
        with pytest.raises(MemoryLimitError):
            check_memory_usage(0.001) # 1KB limit

    def test_memory_usage_is_positive(self):
        """Sanity check that memory usage is positive."""
        usage = get_memory_usage_mb()
        assert usage > 0
        assert usage < 100000 # Sanity upper bound