"""
Unit tests for the logging infrastructure (T008).
"""

import logging
import os
import tempfile
import shutil
from pathlib import Path

import pytest

# Import the module under test
# We use a relative import style assumption or absolute based on PYTHONPATH
# Assuming code/ is in the path or we run from project root with code/ on path
try:
    from utils.logger import get_logger, setup_logging, log_exception
except ImportError:
    # Fallback for test execution context
    import sys
    sys.path.insert(0, 'code')
    from utils.logger import get_logger, setup_logging, log_exception


class TestLoggerConfiguration:
    """Tests for logger setup and configuration."""

    def test_get_logger_returns_instance(self):
        """Test that get_logger returns a valid logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_logger_has_handlers(self):
        """Test that a fresh logger gets configured with handlers."""
        logger = get_logger("test_new_logger")
        # A newly created logger via get_logger should have handlers
        # unless the global setup was skipped, but setup_logging ensures it.
        assert len(logger.handlers) > 0

    def test_log_exception_function(self, caplog):
        """Test that log_exception captures the error correctly."""
        logger = get_logger("test_exception")
        
        try:
            raise ValueError("Test error")
        except ValueError:
            log_exception(logger, "An error occurred")

        # Check that the error message is in the log
        assert "An error occurred" in caplog.text
        assert "ValueError" in caplog.text
        assert "Test error" in caplog.text

    def test_log_levels(self):
        """Test that different log levels work."""
        logger = get_logger("test_levels")
        
        # Clear existing handlers to avoid noise in test output
        logger.handlers = []
        setup_logging(name="test_levels", log_to_console=False)

        with caplog.at_level(logging.INFO):
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.debug("Debug message") # Should not appear if level is INFO

        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text
        assert "Debug message" not in caplog.text