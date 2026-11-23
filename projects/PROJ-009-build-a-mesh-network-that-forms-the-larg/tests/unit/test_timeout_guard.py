"""
Unit tests for the timeout enforcement mechanism.
"""
import time
import pytest
from unittest.mock import patch, MagicMock

from orchestrator.timeout_guard import (
    enforce_pipeline_timeout,
    run_with_timeout,
    PipelineTimeoutError,
    calculate_remaining_budget,
    check_budget_remaining
)

class TestTimeoutGuard:
    """Tests for the timeout guard functionality."""

    def test_enforce_timeout_success(self):
        """Test that a function completing within timeout returns normally."""
        @enforce_pipeline_timeout(10)
        def fast_task():
            time.sleep(0.1)
            return "success"

        result = fast_task()
        assert result == "success"

    def test_enforce_timeout_exceeded(self):
        """Test that a function exceeding timeout raises PipelineTimeoutError."""
        @enforce_pipeline_timeout(0.1)
        def slow_task():
            time.sleep(1.0)
            return "should not reach here"

        with pytest.raises(PipelineTimeoutError) as exc_info:
            slow_task()
        
        assert "exceeded hard timeout" in str(exc_info.value).lower()

    def test_run_with_timeout_success(self):
        """Test run_with_timeout with a function that completes in time."""
        def quick_func():
            time.sleep(0.05)
            return 42

        result = run_with_timeout(quick_func, 5)
        assert result == 42

    def test_run_with_timeout_exceeded(self):
        """Test run_with_timeout raises on timeout."""
        def slow_func():
            time.sleep(10)
            return 0

        with pytest.raises(PipelineTimeoutError):
            run_with_timeout(slow_func, 0.1)

    def test_run_with_timeout_propagates_exception(self):
        """Test that exceptions within the function are propagated."""
        def failing_func():
            raise ValueError("Intentional failure")

        with pytest.raises(ValueError, match="Intentional failure"):
            run_with_timeout(failing_func, 10)

    def test_calculate_remaining_budget_positive(self):
        """Test budget calculation when time remains."""
        remaining = calculate_remaining_budget(100, 300)
        assert remaining == 200

    def test_calculate_remaining_budget_negative(self):
        """Test budget calculation returns 0 when over budget."""
        remaining = calculate_remaining_budget(350, 300)
        assert remaining == 0

    def test_check_budget_remaining_true(self):
        """Test budget check returns True when time remains."""
        assert check_budget_remaining(100, 300) is True

    def test_check_budget_remaining_false(self):
        """Test budget check returns False when over budget."""
        assert check_budget_remaining(350, 300) is False

    def test_nested_timeout_handling(self):
        """Test that nested timeout decorators work correctly (outer wins)."""
        @enforce_pipeline_timeout(10)
        def outer_task():
            @enforce_pipeline_timeout(100)
            def inner_task():
                time.sleep(0.2)
                return "inner done"
            return inner_task()

        result = outer_task()
        assert result == "inner done"

    def test_timeout_with_exception_in_thread(self):
        """Test timeout behavior when inner function raises."""
        def raise_func():
            time.sleep(0.05)
            raise RuntimeError("Inner error")

        with pytest.raises(RuntimeError, match="Inner error"):
            run_with_timeout(raise_func, 10)