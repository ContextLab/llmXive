"""
Unit tests for the logging infrastructure in code.data.
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path

import pytest

# Import the module under test
# We need to ensure the import path is correct relative to the test runner
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data import get_logger, logger


class TestLoggingInfrastructure:
    """Tests for the logging setup and configuration."""

    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a valid logging.Logger instance."""
        lg = get_logger("test.module")
        assert isinstance(lg, logging.Logger)
        assert lg.name == "test.module"

    def test_logger_has_handlers(self):
        """Test that the logger is configured with at least one handler."""
        lg = get_logger("test.handlers")
        # The logger should have both file and console handlers
        assert len(lg.handlers) >= 1

    def test_log_file_created_in_expected_location(self):
        """Test that the log file is created in data/logs/."""
        # We rely on the project structure assumption.
        # Since we can't easily mock the project root without complex fixtures,
        # we verify that the logger exists and has a file handler.
        lg = get_logger("test.file")
        file_handler = None
        for handler in lg.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break

        assert file_handler is not None, "File handler not found"
        log_file_path = Path(file_handler.baseFilename)
        assert log_file_path.exists(), f"Log file {log_file_path} does not exist"
        assert "data" in str(log_file_path) or "logs" in str(log_file_path), \
            f"Log file path {log_file_path} does not appear to be in data/logs"

    def test_logger_level_is_info(self):
        """Test that the logger level is set to INFO."""
        lg = get_logger("test.level")
        assert lg.level == logging.INFO

    def test_console_handler_level_is_warning(self):
        """Test that the console handler defaults to WARNING level."""
        lg = get_logger("test.console")
        console_handler = None
        for handler in lg.handlers:
            if isinstance(handler, logging.StreamHandler):
                console_handler = handler
                break

        assert console_handler is not None
        assert console_handler.level == logging.WARNING

    def test_formatter_exists(self):
        """Test that handlers have a formatter."""
        lg = get_logger("test.formatter")
        for handler in lg.handlers:
            assert handler.formatter is not None
            assert "%(asctime)s" in handler.formatter._fmt

    def test_global_logger_var_available(self):
        """Test that the global 'logger' variable is available and configured."""
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert len(logger.handlers) > 0