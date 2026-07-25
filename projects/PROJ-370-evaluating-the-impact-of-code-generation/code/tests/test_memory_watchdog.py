"""
Tests for the memory watchdog utility.
"""

import pytest
import time
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.src.utils.memory_watchdog import (
    get_memory_usage_bytes,
    check_memory_limit,
    setup_memory_logging,
    MemoryMonitor,
    MemoryLimitExceeded,
    enforce_memory_limit,
    MEMORY_THRESHOLD_BYTES
)


class TestGetMemoryUsageBytes:
    """Tests for get_memory_usage_bytes function."""

    def test_get_memory_usage_returns_positive_value(self):
        """Memory usage should always be a non-negative integer."""
        memory = get_memory_usage_bytes()
        assert isinstance(memory, int)
        assert memory >= 0

    @patch('builtins.open')
    def test_get_memory_from_proc_status(self, mock_open):
        """Test parsing memory from /proc/self/status."""
        mock_open.return_value.__enter__.return_value = [
            "VmRSS:     12345 kB\n",
            "other_line: value\n"
        ]
        memory = get_memory_usage_bytes()
        assert memory == 12345 * 1024  # Convert kB to bytes


class TestCheckMemoryLimit:
    """Tests for check_memory_limit function."""

    def test_below_threshold_returns_false(self):
        """Should return False when memory is below threshold."""
        # Mock get_memory_usage_bytes to return a small value
        with patch(
            'code.src.utils.memory_watchdog.get_memory_usage_bytes',
            return_value=1024  # 1KB
        ):
            result = check_memory_limit(threshold_bytes=MEMORY_THRESHOLD_BYTES)
            assert result is False

    def test_above_threshold_returns_true(self):
        """Should return True when memory exceeds threshold."""
        # Mock get_memory_usage_bytes to return a large value (8GB)
        with patch(
            'code.src.utils.memory_watchdog.get_memory_usage_bytes',
            return_value=8 * 1024 * 1024 * 1024
        ):
            result = check_memory_limit(threshold_bytes=MEMORY_THRESHOLD_BYTES)
            assert result is True

    def test_custom_threshold(self):
        """Should respect custom threshold values."""
        with patch(
            'code.src.utils.memory_watchdog.get_memory_usage_bytes',
            return_value=5 * 1024 * 1024 * 1024  # 5GB
        ):
            # 4GB threshold
            result = check_memory_limit(threshold_bytes=4 * 1024 * 1024 * 1024)
            assert result is True

            # 6GB threshold
            result = check_memory_limit(threshold_bytes=6 * 1024 * 1024 * 1024)
            assert result is False


class TestMemoryMonitor:
    """Tests for MemoryMonitor class."""

    def test_monitor_context_manager(self):
        """Test that MemoryMonitor context manager works."""
        with patch(
            'code.src.utils.memory_watchdog.get_memory_usage_bytes',
            return_value=1024  # Always below threshold
        ):
            with MemoryMonitor.threshold_bytes(
                MEMORY_THRESHOLD_BYTES,
                check_interval_seconds=0.1
            ):
                time.sleep(0.2)  # Give monitor time to run

    def test_monitor_raises_on_exceed(self):
        """Test that MemoryMonitor raises exception when limit exceeded."""
        call_count = [0]

        def mock_memory():
            call_count[0] += 1
            # Return low memory first, then high memory
            if call_count[0] > 2:
                return 8 * 1024 * 1024 * 1024  # 8GB
            return 1024  # 1KB

        with patch(
            'code.src.utils.memory_watchdog.get_memory_usage_bytes',
            side_effect=mock_memory
        ):
            with pytest.raises(MemoryLimitExceeded):
                with MemoryMonitor.watch(
                    threshold_bytes=MEMORY_THRESHOLD_BYTES,
                    check_interval_seconds=0.05
                ):
                    time.sleep(0.5)  # Run long enough to trigger check

    def test_monitor_with_custom_logger(self):
        """Test MemoryMonitor with a custom logger."""
        mock_logger = MagicMock()
        with patch(
            'code.src.utils.memory_watchdog.get_memory_usage_bytes',
            return_value=1024
        ):
            monitor = MemoryMonitor(
                threshold_bytes=MEMORY_THRESHOLD_BYTES,
                logger=mock_logger
            )
            with monitor:
                time.sleep(0.1)
            assert mock_logger is not None


class TestEnforceMemoryLimitDecorator:
    """Tests for enforce_memory_limit decorator."""

    def test_decorator_allows_normal_execution(self):
        """Test that decorator allows normal execution when memory is low."""
        with patch(
            'code.src.utils.memory_watchdog.get_memory_usage_bytes',
            return_value=1024
        ):
            @enforce_memory_limit
            def my_function():
                return "success"

            result = my_function()
            assert result == "success"

    def test_decorator_raises_on_memory_exceeded(self):
        """Test that decorator raises exception when memory exceeded."""
        call_count = [0]

        def mock_memory():
            call_count[0] += 1
            if call_count[0] > 2:
                return 8 * 1024 * 1024 * 1024
            return 1024

        with patch(
            'code.src.utils.memory_watchdog.get_memory_usage_bytes',
            side_effect=mock_memory
        ):
            @enforce_memory_limit
            def my_function():
                time.sleep(0.5)
                return "success"

            with pytest.raises(MemoryLimitExceeded):
                my_function()


class TestSetupMemoryLogging:
    """Tests for setup_memory_logging function."""

    def test_logger_created(self):
        """Test that a logger is created successfully."""
        logger = setup_memory_logging()
        assert logger is not None
        assert logger.name == 'memory_watchdog'
        assert logger.level == logging.WARNING

    def test_log_file_created(self, tmp_path):
        """Test that log file is created in specified directory."""
        log_dir = tmp_path / "logs"
        logger = setup_memory_logging(log_dir=log_dir)

        log_file = log_dir / 'memory_warning.log'
        assert log_file.exists()

    def test_logger_handles_warnings(self, tmp_path):
        """Test that logger can handle warning messages."""
        log_dir = tmp_path / "logs"
        logger = setup_memory_logging(log_dir=log_dir)

        logger.warning("Test warning message")

        log_file = log_dir / 'memory_warning.log'
        assert log_file.exists()

        content = log_file.read_text()
        assert "Test warning message" in content