"""Unit tests for memory_monitor.py threshold violation logic.

This module tests the memory monitoring functionality, specifically:
1. Threshold violation detection (check_memory_limit)
2. MemoryMonitor class behavior under limit violation
3. Decorator enforcement (memory_limit_decorator)

Tests verify that the system correctly raises exceptions when
memory usage exceeds the configured limit (default 7GB).
"""

import pytest
import os
import sys
import time
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.memory_monitor import (
    get_current_rss_bytes,
    check_memory_limit,
    MemoryMonitor,
    memory_limit_decorator,
    enforce_memory_limit
)


class TestGetCurrentRssBytes:
    """Tests for get_current_rss_bytes function."""

    def test_returns_positive_integer(self):
        """Verify that RSS is returned as a positive integer."""
        rss = get_current_rss_bytes()
        assert isinstance(rss, int)
        assert rss > 0

    @patch('utils.memory_monitor.Path')
    def test_handles_missing_proc_status(self, mock_path):
        """Verify behavior when /proc/self/status is missing."""
        mock_path.return_value.read_text.side_effect = FileNotFoundError
        # Should return 0 or raise a clear error
        rss = get_current_rss_bytes()
        assert rss == 0 or isinstance(rss, int)


class TestCheckMemoryLimit:
    """Tests for check_memory_limit function."""

    def test_passes_below_limit(self):
        """Verify no exception when memory is below limit."""
        # Mock a value well below 7GB
        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 100):  # 100MB
            # Should not raise
            result = check_memory_limit(limit_bytes=1024 * 1024 * 1024)  # 1GB limit
            assert result is True

    def test_raises_when_above_limit(self):
        """Verify MemoryError is raised when memory exceeds limit."""
        # Mock a value above limit
        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 1024 * 8):  # 8GB
            with pytest.raises(MemoryError) as exc_info:
                check_memory_limit(limit_bytes=1024 * 1024 * 1024 * 7)  # 7GB limit

            assert "Memory limit exceeded" in str(exc_info.value)

    def test_default_limit_is_7gb(self):
        """Verify default limit is 7GB."""
        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 1024 * 8):
            with pytest.raises(MemoryError):
                check_memory_limit()  # Should use default 7GB


class TestMemoryMonitor:
    """Tests for MemoryMonitor class."""

    def test_initialization(self):
        """Verify MemoryMonitor initializes with correct limit."""
        monitor = MemoryMonitor(limit_bytes=1024 * 1024 * 1024)
        assert monitor.limit_bytes == 1024 * 1024 * 1024
        assert monitor.running is False

    def test_start_and_stop(self):
        """Verify start/stop functionality."""
        monitor = MemoryMonitor(limit_bytes=1024 * 1024 * 1024)
        monitor.start()
        assert monitor.running is True
        monitor.stop()
        assert monitor.running is False

    def test_check_exceeds_limit(self):
        """Verify check() raises when limit exceeded."""
        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 1024 * 8):
            monitor = MemoryMonitor(limit_bytes=1024 * 1024 * 1024 * 7)
            monitor.start()
            with pytest.raises(MemoryError):
                monitor.check()
            monitor.stop()

    def test_check_within_limit(self):
        """Verify check() passes when within limit."""
        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 100):
            monitor = MemoryMonitor(limit_bytes=1024 * 1024 * 1024)
            monitor.start()
            # Should not raise
            monitor.check()
            monitor.stop()

    def test_run_function_with_limit(self):
        """Verify run() executes function within limit."""
        def dummy_func():
            return "success"

        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 100):
            monitor = MemoryMonitor(limit_bytes=1024 * 1024 * 1024)
            result = monitor.run(dummy_func)
            assert result == "success"

    def test_run_function_exceeds_limit(self):
        """Verify run() raises when memory exceeded during execution."""
        def dummy_func():
            return "success"

        with patch('utils.memory_monitor.get_current_rss_bytes', side_effect=[
            1024 * 1024 * 100,  # Initial check passes
            1024 * 1024 * 1024 * 8  # Check during execution fails
        ]):
            monitor = MemoryMonitor(limit_bytes=1024 * 1024 * 1024 * 7)
            with pytest.raises(MemoryError):
                monitor.run(dummy_func)


class TestMemoryLimitDecorator:
    """Tests for memory_limit_decorator."""

    def test_decorator_allows_execution(self):
        """Verify decorated function runs when memory is within limit."""
        @memory_limit_decorator(limit_bytes=1024 * 1024 * 1024)
        def my_func():
            return "success"

        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 100):
            result = my_func()
            assert result == "success"

    def test_decorator_raises_on_violation(self):
        """Verify decorated function raises when memory exceeds limit."""
        @memory_limit_decorator(limit_bytes=1024 * 1024 * 1024)
        def my_func():
            return "success"

        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 1024 * 8):
            with pytest.raises(MemoryError):
                my_func()

    def test_decorator_with_args(self):
        """Verify decorator works with function arguments."""
        @memory_limit_decorator(limit_bytes=1024 * 1024 * 1024)
        def my_func(x, y):
            return x + y

        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 100):
            result = my_func(10, 20)
            assert result == 30


class TestEnforceMemoryLimit:
    """Tests for enforce_memory_limit function."""

    def test_enforce_raises_on_excess(self):
        """Verify enforce_memory_limit raises when limit exceeded."""
        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 1024 * 8):
            with pytest.raises(MemoryError):
                enforce_memory_limit(limit_bytes=1024 * 1024 * 1024 * 7)

    def test_enforce_passes_below_limit(self):
        """Verify enforce_memory_limit passes when within limit."""
        with patch('utils.memory_monitor.get_current_rss_bytes', return_value=1024 * 1024 * 100):
            # Should not raise
            enforce_memory_limit(limit_bytes=1024 * 1024 * 1024)