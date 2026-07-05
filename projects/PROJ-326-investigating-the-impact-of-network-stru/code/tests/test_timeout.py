"""
Tests for the timeout utility in code/src/generators/timeout.py.
"""
import pytest
import time
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.generators.timeout import timeout, TimeoutError

class TestTimeoutUtility:
    """Test cases for the timeout decorator and logic."""

    def test_timeout_decorator_success(self):
        """Verify that a function completing within the limit returns normally."""
        @timeout(seconds=5, retries=0)
        def quick_task():
            time.sleep(0.1)
            return "success"

        result = quick_task()
        assert result == "success"

    def test_timeout_decorator_triggers(self):
        """Verify that a function exceeding the limit raises TimeoutError or returns fallback."""
        # Note: On Windows, the signal-based timeout might not kill the thread,
        # so the fallback mechanism relies on the cooperative check or the decorator logic.
        # We expect the decorator to return the fallback value if retries are exhausted.
        
        @timeout(seconds=1, retries=0, fallback_value="fallback")
        def slow_task():
            time.sleep(3)
            return "should_not_return"

        start = time.time()
        result = slow_task()
        duration = time.time() - start

        # On Unix, it might raise, but our wrapper catches and returns fallback if retries=0
        # The wrapper logic: attempt=0, timeout -> attempt=1 (which is > retries=0) -> return fallback
        assert result == "fallback"
        # Should have taken roughly 1 second (the timeout duration) before returning fallback
        assert 0.9 < duration < 4.0, f"Execution time {duration} is outside expected range"

    def test_timeout_retry_logic(self):
        """Verify that the function retries on timeout before giving up."""
        attempt_count = 0

        @timeout(seconds=1, retries=1, fallback_value="final_fallback")
        def flaky_task():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                time.sleep(2)  # Force timeout twice
            return "success"

        # First call: attempt 0 -> timeout (1s)
        # Second call: attempt 1 -> timeout (1s)
        # Third call: attempt 2 -> success (returns immediately)
        # Total attempts: 3. Retries allowed: 1. So we expect 2 timeouts then success?
        # Wait, logic: while attempt <= retries (0 <= 1, 1 <= 1).
        # Attempt 0: Timeout -> attempt becomes 1.
        # Attempt 1: Timeout -> attempt becomes 2.
        # Loop ends (2 > 1). Return fallback.
        
        # Let's adjust the test to ensure it succeeds on the retry.
        # We need the function to succeed on the 2nd attempt.
        
        attempt_count = 0
        
        @timeout(seconds=1, retries=1, fallback_value="fallback")
        def conditional_task():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                time.sleep(2) # Timeout first time
            return "success"

        result = conditional_task()
        
        # Expected flow:
        # Attempt 0: Timeout (1s) -> retry
        # Attempt 1: Success (returns)
        # Total attempts = 2.
        
        assert result == "success"
        assert attempt_count == 2

    def test_timeout_fallback_exhaustion(self):
        """Verify fallback is returned when retries are exhausted."""
        attempt_count = 0

        @timeout(seconds=0.5, retries=1, fallback_value="exhausted")
        def always_slow():
            nonlocal attempt_count
            attempt_count += 1
            time.sleep(2)
            return "never"

        result = always_slow()
        
        # Attempt 0: Timeout
        # Attempt 1: Timeout
        # Exhausted -> return fallback
        assert result == "exhausted"
        assert attempt_count == 2

    def test_timeout_signature_preservation(self):
        """Verify functools.wraps preserves function metadata."""
        @timeout(seconds=1)
        def my_func(x, y):
            """My docstring."""
            pass

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "My docstring."