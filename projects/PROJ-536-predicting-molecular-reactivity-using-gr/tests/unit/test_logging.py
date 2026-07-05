"""
Unit tests for the logging infrastructure.
"""

import logging
import os
import tempfile
import shutil
from pathlib import Path

import pytest

# Import the module under test
# Note: We need to adjust the import path based on the project structure
# Assuming src/utils/logging.py is the target
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.logging import get_logger, setup_root_logger, LOG_DIR


class TestLoggingInfrastructure:
    """Tests for the logging module."""

    def setup_method(self):
        """Set up test fixtures."""
        # Ensure results directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up after tests."""
        # Remove any test log files
        test_log_files = list(LOG_DIR.glob("test_*.log"))
        for f in test_log_files:
            f.unlink()

        # Clear configured loggers to avoid side effects
        from src.utils.logging import _configured_loggers
        _configured_loggers.clear()

        # Reset root logger handlers
        logging.getLogger().handlers.clear()

    def test_get_logger_creates_logger(self):
        """Test that get_logger returns a valid Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_sets_level(self):
        """Test that get_logger sets the correct log level."""
        logger = get_logger("test_level", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_get_logger_adds_console_handler(self):
        """Test that get_logger adds a console handler."""
        logger = get_logger("test_console")
        # Should have at least one handler (console)
        assert len(logger.handlers) >= 1
        # Check that one of them is a StreamHandler (console)
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1

    def test_get_logger_adds_file_handler(self):
        """Test that get_logger adds a file handler when log_file is provided."""
        test_log_file = "test_get_logger_file.log"
        logger = get_logger("test_file", log_file=test_log_file)

        # Should have a file handler
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1

        # Verify the file was created
        log_path = LOG_DIR / test_log_file
        assert log_path.exists()

    def test_get_logger_prevents_duplicate_handlers(self):
        """Test that calling get_logger multiple times doesn't add duplicate handlers."""
        logger = get_logger("test_duplicate")
        initial_handler_count = len(logger.handlers)

        # Call again with same name
        logger_again = get_logger("test_duplicate")

        # Handler count should be the same
        assert len(logger_again.handlers) == initial_handler_count

    def test_setup_root_logger(self):
        """Test that setup_root_logger configures the root logger."""
        setup_root_logger(level=logging.WARNING)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

        # Should have at least a console handler
        assert len(root_logger.handlers) >= 1

    def test_get_pipeline_logger(self):
        """Test that get_pipeline_logger returns a configured logger."""
        from src.utils.logging import get_pipeline_logger
        logger = get_pipeline_logger()

        assert logger.name == "llmXive.pipeline"
        assert isinstance(logger, logging.Logger)

    def test_log_output_to_file(self):
        """Test that log messages are written to the file."""
        test_log_file = "test_log_output.log"
        logger = get_logger("test_output", log_file=test_log_file, level=logging.INFO)

        test_message = "Test log message"
        logger.info(test_message)

        # Read the file and check for the message
        log_path = LOG_DIR / test_log_file
        with open(log_path, "r") as f:
            content = f.read()

        assert test_message in content

    def test_rotating_file_handler(self):
        """Test that RotatingFileHandler is used for file logging."""
        test_log_file = "test_rotating.log"
        logger = get_logger("test_rotating", log_file=test_log_file)

        file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) >= 1