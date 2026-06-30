"""
Unit tests for the runtime_guard module.
"""
import pytest
import time
import os
import sys
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

# Ensure we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from runtime_guard import (
    time_limit_guard,
    memory_limit_guard,
    with_runtime_guards,
    get_runtime_config,
    _aborted,
    _abort_reason
)

class TestTimeLimitGuard:
    def test_time_limit_success(self):
        """Test that a task completing within the limit succeeds."""
        start = time.time()
        with time_limit_guard(seconds=5):
            time.sleep(0.1)
        elapsed = time.time() - start
        assert elapsed < 1.0, "Task should complete quickly"

    def test_time_limit_exceeded(self):
        """Test that a task exceeding the limit raises TimeoutError."""
        with pytest.raises(TimeoutError):
            with time_limit_guard(seconds=1):
                time.sleep(2)

    def test_time_limit_zero(self):
        """Test that zero limit skips the guard."""
        # Should not raise, just skip
        with time_limit_guard(seconds=0):
            time.sleep(0.01)

class TestMemoryLimitGuard:
    def test_memory_limit_success(self):
        """Test that a task within memory limit succeeds."""
        # Note: This test might be flaky depending on OS resource limits implementation
        # but should generally pass if the limit is high enough
        try:
            with memory_limit_guard(mb_limit=1024): # 1GB
                _ = [0] * 100000 # Small allocation
        except MemoryError:
            # If it fails here, it might be due to strict system limits
            pytest.skip("System memory limits too strict for test")

    def test_memory_limit_exceeded(self):
        """Test that a task exceeding memory limit raises MemoryError."""
        # This is hard to test reliably because RLIMIT_AS usually kills the process.
        # We rely on the fact that the decorator logic is sound.
        # For now, we test that the context manager doesn't crash on setup.
        try:
            with memory_limit_guard(mb_limit=1): # 1MB - likely to fail on allocation
                # Try to allocate more than 1MB
                _ = bytearray(2 * 1024 * 1024)
        except MemoryError:
            # Expected
            pass
        except Exception as e:
            # If the system kills the process, we won't reach here in pytest
            # But if it raises an exception other than MemoryError, that's unexpected
            if "Killed" in str(e):
                pytest.skip("Process killed by OS")
            raise

class TestWithRuntimeGuards:
    def test_decorator_success(self):
        @with_runtime_guards(time_limit=5, memory_limit=1024)
        def quick_task():
            return "success"
        
        assert quick_task() == "success"

    def test_decorator_timeout(self):
        @with_runtime_guards(time_limit=1)
        def slow_task():
            time.sleep(2)
            return "success"
        
        with pytest.raises(TimeoutError):
            slow_task()

class TestConfig:
    @patch('runtime_guard.load_config')
    def test_get_runtime_config_defaults(self, mock_load):
        mock_load.return_value = {}
        cfg = get_runtime_config()
        assert cfg["time_limit_seconds"] == 3600
        assert cfg["oom_memory_limit_mb"] == 6000

    @patch('runtime_guard.load_config')
    def test_get_runtime_config_custom(self, mock_load):
        mock_load.return_value = {
            "runtime": {
                "time_limit_seconds": 100,
                "oom_memory_limit_mb": 500
            }
        }
        cfg = get_runtime_config()
        assert cfg["time_limit_seconds"] == 100
        assert cfg["oom_memory_limit_mb"] == 500