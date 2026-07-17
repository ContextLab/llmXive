"""
Unit tests for the global timeout utility (T016a).
"""
import time
import pytest
import logging
from code.src.generators.timeout import timeout, TimeoutError, TimeoutHandler

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

class TestTimeoutDecorator:
    """Tests for the @timeout decorator."""

    def test_successful_execution_within_timeout(self):
        """Verify function completes successfully if it finishes before timeout."""
        @timeout(seconds=2, retries=0, fallback_value="fallback")
        def quick_func():
            time.sleep(0.1)
            return "success"

        result = quick_func()
        assert result == "success"

    def test_timeout_triggers_after_x_seconds(self):
        """Verify timeout triggers after X seconds and retries."""
        call_count = 0

        @timeout(seconds=1, retries=2, fallback_value="timeout_hit")
        def slow_func():
            nonlocal call_count
            call_count += 1
            time.sleep(3)  # Sleep longer than timeout
            return "should_not_reach"

        result = slow_func()
        
        # Verify fallback was returned
        assert result == "timeout_hit"
        # Verify retries happened (initial + 2 retries = 3 attempts)
        assert call_count == 3

    def test_no_retry_on_non_timeout_exception(self):
        """Verify non-timeout exceptions are raised immediately without retry."""
        @timeout(seconds=5, retries=3, fallback_value="fallback")
        def failing_func():
            raise ValueError("Intentional error")

        with pytest.raises(ValueError):
            failing_func()

    def test_fallback_value_returned_on_exhausted_retries(self):
        """Verify specific fallback value is returned when retries are exhausted."""
        @timeout(seconds=1, retries=1, fallback_value=42)
        def timed_out_func():
            time.sleep(2)
            return 0

        result = timed_out_func()
        assert result == 42

    def test_default_fallback_is_none(self):
        """Verify default fallback value is None if not specified."""
        @timeout(seconds=1, retries=0)
        def timed_out_func():
            time.sleep(2)
            return 0

        result = timed_out_func()
        assert result is None

class TestTimeoutHandlerContextManager:
    """Tests for the TimeoutHandler context manager."""

    def test_context_manager_raises_timeout(self):
        """Verify context manager raises TimeoutError after seconds."""
        handler = TimeoutHandler(seconds=1)
        
        with pytest.raises(TimeoutError):
            with handler:
                time.sleep(2)

    def test_context_manager_success(self):
        """Verify context manager allows completion if fast enough."""
        handler = TimeoutHandler(seconds=2)
        
        with handler:
            time.sleep(0.5)
        
        # If we reach here, no exception was raised
        assert True

class TestEnforceTimeout:
    """Tests for the enforce_timeout helper function."""

    def test_enforce_timeout_returns_decorator(self):
        """Verify enforce_timeout returns a valid decorator."""
        decorator = enforce_timeout(seconds=1, retries=0, fallback_value="err")
        
        @decorator
        def test_func():
            return "ok"

        assert test_func() == "ok"