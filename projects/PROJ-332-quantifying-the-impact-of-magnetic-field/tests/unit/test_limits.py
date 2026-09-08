"""
Unit tests for resource limits and guards (T006).
"""
import pytest
import time
import signal
import os
from unittest.mock import patch, MagicMock

# Import the module under test
from utils.limits import (
    timeout_guard, 
    timeout_context, 
    memory_guard, 
    TimeoutError, 
    MemoryLimitError,
    get_memory_usage_mb,
    check_memory_usage
)

class TestTimeoutGuard:
    def test_timeout_guard_success(self):
        """Test that a function completing within the limit runs successfully."""
        @timeout_guard(5)
        def fast_function():
            return "success"

        result = fast_function()
        assert result == "success"

    def test_timeout_guard_failure(self):
        """Test that a function exceeding the limit raises TimeoutError."""
        @timeout_guard(1)
        def slow_function():
            time.sleep(3)
            return "should not reach here"

        with pytest.raises(TimeoutError):
            slow_function()

    def test_timeout_context_success(self):
        """Test context manager for successful execution."""
        def operation():
            return "done"

        with timeout_context(5):
            result = operation()
            assert result == "done"

    def test_timeout_context_failure(self):
        """Test context manager for timeout."""
        def slow_operation():
            time.sleep(3)

        with pytest.raises(TimeoutError):
            with timeout_context(1):
                slow_operation()

class TestMemoryGuard:
    @patch('utils.limits.get_memory_usage_mb')
    def test_memory_guard_success(self, mock_mem_usage):
        """Test memory guard passes when usage is low."""
        mock_mem_usage.return_value = 100.0  # 100MB
        
        @memory_guard(1000)
        def func():
            return "ok"

        result = func()
        assert result == "ok"

    @patch('utils.limits.get_memory_usage_mb')
    def test_memory_guard_failure_before(self, mock_mem_usage):
        """Test memory guard fails immediately if usage is high."""
        mock_mem_usage.return_value = 2000.0  # 2000MB

        @memory_guard(1000)
        def func():
            return "should not run"

        with pytest.raises(MemoryLimitError):
            func()

    @patch('utils.limits.get_memory_usage_mb')
    def test_memory_guard_failure_after(self, mock_mem_usage):
        """Test memory guard fails if usage spikes after start."""
        # First call (check before) returns low, second call (check after) returns high
        mock_mem_usage.side_effect = [100.0, 2000.0]

        @memory_guard(1000)
        def func():
            return "executed"

        with pytest.raises(MemoryLimitError):
            func()

class TestMemoryUtils:
    def test_get_memory_usage_mb(self):
        """Test that memory usage is a positive number."""
        usage = get_memory_usage_mb()
        assert isinstance(usage, float)
        assert usage >= 0

    def test_check_memory_usage(self):
        """Test check_memory_usage logic."""
        # Should be within a very large limit
        assert check_memory_usage(100000.0) is True
        # Should be outside a very small limit (unless running in tiny env, but unlikely < 1MB)
        # We assume standard env has > 1MB usage
        assert check_memory_usage(0.001) is False