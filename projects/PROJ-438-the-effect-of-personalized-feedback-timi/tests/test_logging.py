"""
Unit tests for the logging infrastructure (code/logging_config.py).
Validates that the logger is set up correctly and logs to the expected location.
"""
import os
import tempfile
import pytest
from pathlib import Path

from code.logging_config import setup_logger, get_logger, info, warning, error


class TestLoggingSetup:
    """Tests for logging_config.py functionality."""

    def test_setup_logger_creates_file(self):
        """Ensure setup_logger creates the log file in the specified directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_dir = Path(tmp_dir) / "logs"
            logger = setup_logger("test_logger", str(log_dir))

            assert log_dir.exists()
            # Check that a log file was created or will be created on first log
            info("Test message")
            
            # List files to ensure a log file exists
            log_files = list(log_dir.glob("*.log"))
            assert len(log_files) > 0, "No log files found after logging a message."

    def test_logger_levels(self):
        """Ensure different log levels are accepted."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_dir = Path(tmp_dir) / "logs"
            logger = setup_logger("test_levels", str(log_dir))

            # These should not raise exceptions
            info("Info message")
            warning("Warning message")
            error("Error message")

    def test_get_logger_singleton(self):
        """Ensure get_logger returns the same instance for the same name."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_dir = Path(tmp_dir) / "logs"
            setup_logger("singleton_test", str(log_dir))
            
            logger1 = get_logger("singleton_test")
            logger2 = get_logger("singleton_test")
            
            assert logger1 is logger2
