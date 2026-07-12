"""
Tests for the logging configuration infrastructure.
"""
import logging
import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# We need to mock the PROJECT_ROOT logic because tests might run from a different directory
# or we need to ensure the logs directory is created in a temp location for isolation.
# However, since the implementation uses absolute paths relative to the file,
# we will test the behavior of the logger creation and handler attachment.

from src.utils.logging_config import (
    get_logger,
    _setup_global_logger,
    configure_logging_level,
    LOGGER_NAME,
    LOGS_DIR
)


class TestLoggingConfig:
    """Tests for the global logging configuration."""

    def test_logger_creation(self):
        """Test that a logger is created and configured correctly."""
        logger = get_logger()

        assert isinstance(logger, logging.Logger)
        assert logger.name == LOGGER_NAME
        assert logger.level == logging.DEBUG

        # Check handlers
        assert len(logger.handlers) == 2

        # Identify handlers
        handlers = logger.handlers
        console_handler = None
        file_handler = None

        for h in handlers:
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler):
                console_handler = h
            elif isinstance(h, logging.FileHandler):
                file_handler = h

        assert console_handler is not None, "Console handler not found"
        assert file_handler is not None, "File handler not found"

        # Check levels
        assert console_handler.level == logging.INFO
        assert file_handler.level == logging.DEBUG

    def test_logger_singleton(self):
        """Test that get_logger returns the same instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2

    def test_module_logger(self):
        """Test that module-specific loggers are children of the global logger."""
        from src.utils.logging_config import get_module_logger

        module_logger = get_module_logger("data.embed")
        assert module_logger.name == f"{LOGGER_NAME}.data.embed"
        assert module_logger.parent.name == LOGGER_NAME

    def test_configure_logging_level(self):
        """Test updating handler levels."""
        # Reset logger to ensure clean state for this specific test logic
        # (In a real scenario, we might reset the global _logger, but here we just check the function works)
        logger = get_logger()

        # Change levels
        configure_logging_level(console_level=logging.WARNING, file_level=logging.CRITICAL)

        # Verify
        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler):
                assert h.level == logging.WARNING
            elif isinstance(h, logging.FileHandler):
                assert h.level == logging.CRITICAL

    def test_logs_directory_exists(self):
        """Test that the logs directory is created if it doesn't exist."""
        # The setup logic runs on import/first call, so this should already exist
        # But we verify the path type and existence
        assert isinstance(LOGS_DIR, Path)
        assert LOGS_DIR.exists()

    def test_file_handler_writes(self, tmp_path):
        """Test that the file handler actually writes to a file."""
        # Note: Since the implementation hardcodes LOGS_DIR based on __file__,
        # we can't easily redirect to tmp_path without refactoring the implementation to accept a path.
        # Instead, we verify the file exists after a log call.
        logger = get_logger()
        test_msg = "Test log message for file handler"
        logger.info(test_msg)

        # Check if the log file exists
        # The implementation uses LOGS_DIR from the module scope
        log_file = LOGS_DIR / "pipeline.log"
        assert log_file.exists()

        # Read back and check content
        with open(log_file, 'r') as f:
            content = f.read()
            assert test_msg in content