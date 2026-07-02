"""
Tests for the logging and monitoring infrastructure.
"""
import pytest
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: Adjust import path based on actual project structure
try:
    from utils.logging_config import (
        setup_logging,
        get_logger,
        get_memory_usage_gb,
        get_disk_usage_gb,
        check_memory_limit,
        check_disk_limit,
        start_resource_monitor,
        stop_resource_monitor,
        resource_monitor_context,
        timed_operation,
        log_resource_snapshot
    )
except ImportError:
    # Fallback for direct execution if path is not set
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from utils.logging_config import (
        setup_logging,
        get_logger,
        get_memory_usage_gb,
        get_disk_usage_gb,
        check_memory_limit,
        check_disk_limit,
        start_resource_monitor,
        stop_resource_monitor,
        resource_monitor_context,
        timed_operation,
        log_resource_snapshot
    )


class TestLoggingSetup:
    def test_setup_logging_creates_file_handler(self, tmp_path):
        """Test that setup_logging creates a file handler."""
        log_dir = tmp_path / "logs"
        log_file = "test.log"
        logger = setup_logging(log_dir=log_dir, log_file=log_file, console=False)

        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.FileHandler)
        assert logger.handlers[0].baseFilename == str(log_dir / log_file)

    def test_setup_logging_creates_console_handler(self):
        """Test that setup_logging creates a console handler when requested."""
        logger = setup_logging(console=True)
        has_console = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_console

    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns the configured logger."""
        logger1 = setup_logging(console=False)
        logger2 = get_logger()
        assert logger1 is logger2


class TestResourceMonitoring:
    def test_get_memory_usage_gb_returns_positive(self):
        """Test that memory usage is a positive number."""
        mem = get_memory_usage_gb()
        assert mem >= 0.0

    def test_get_disk_usage_gb_returns_positive(self):
        """Test that disk usage is a positive number."""
        disk = get_disk_usage_gb()
        assert disk >= 0.0

    def test_check_memory_limit_passes_under_limit(self):
        """Test that check_memory_limit returns True when under limit."""
        # Current usage is definitely under 100GB
        assert check_memory_limit(limit_gb=100.0) is True

    def test_check_memory_limit_fails_over_limit(self):
        """Test that check_memory_limit returns False when over limit."""
        # Use a very small limit that is definitely exceeded
        with patch('utils.logging_config.get_memory_usage_gb', return_value=100.0):
            assert check_memory_limit(limit_gb=1.0) is False

    def test_check_disk_limit_passes_under_limit(self):
        """Test that check_disk_limit returns True when under limit."""
        assert check_disk_limit(limit_gb=100.0) is True

    def test_check_disk_limit_fails_over_limit(self):
        """Test that check_disk_limit returns False when over limit."""
        with patch('utils.logging_config.get_disk_usage_gb', return_value=100.0):
            assert check_disk_limit(limit_gb=1.0) is False


class TestResourceMonitorContext:
    def test_context_manager_starts_and_stops(self):
        """Test that the context manager starts and stops the monitor."""
        # Mock the start/stop functions to avoid actual threading
        with patch('utils.logging_config.start_resource_monitor') as mock_start, \
             patch('utils.logging_config.stop_resource_monitor') as mock_stop:

            with resource_monitor_context():
                mock_start.assert_called_once()
                mock_stop.assert_not_called()

            mock_stop.assert_called_once()

    def test_context_manager_handles_exception(self):
        """Test that the monitor stops even if an exception occurs."""
        with patch('utils.logging_config.start_resource_monitor'), \
             patch('utils.logging_config.stop_resource_monitor') as mock_stop:

            try:
                with resource_monitor_context():
                    raise ValueError("Test exception")
            except ValueError:
                pass

            mock_stop.assert_called_once()


class TestTimedOperation:
    def test_timed_operation_logs_duration(self, caplog):
        """Test that timed_operation logs start and end messages."""
        logger = setup_logging(console=True)
        with caplog.at_level(logging.INFO):
            with timed_operation("Test Op"):
                time.sleep(0.1)

        # Check that log messages contain the operation name
        assert any("Starting operation: Test Op" in msg for msg in caplog.messages)
        assert any("Completed operation: Test Op" in msg for msg in caplog.messages)
