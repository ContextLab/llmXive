"""
Unit tests for the standardized logging configuration.

Verifies that loggers are created correctly, have the expected handlers,
and produce logs to both console and file.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Adjust path to import from the project structure
# Assuming this test is run from the project root: python -m pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.src.utils import logging as project_logging


class TestLoggingConfiguration:
    """Tests for the logging module configuration."""

    def test_get_logger_creates_instance(self):
        """Test that get_logger returns a valid Logger instance."""
        logger = project_logging.get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_sets_level(self):
        """Test that get_logger sets the specified level."""
        logger = project_logging.get_logger("test.level", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

        logger_warn = project_logging.get_logger("test.level2", level=logging.WARNING)
        assert logger_warn.level == logging.WARNING

    def test_console_handler_present(self):
        """Test that a console handler is added to the logger."""
        logger = project_logging.get_logger("test.handlers")
        handlers = logger.handlers
        assert len(handlers) > 0

        # Check for StreamHandler (console)
        stream_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) > 0

    def test_file_handler_present(self):
        """Test that a file handler is added when to_file=True."""
        logger = project_logging.get_logger("test.file_handler", to_file=True)
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

    def test_file_handler_writes_to_logs_dir(self):
        """Test that file handlers write to the logs/ directory."""
        logger = project_logging.get_logger("test.write_dir", to_file=True)
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]

        assert len(file_handlers) > 0
        for handler in file_handlers:
            # The filename should be in the logs directory
            assert "logs" in handler.baseFilename
            # Should be a .log file
            assert handler.baseFilename.endswith(".log")

    def test_predefined_ingestion_logger(self):
        """Test the get_ingestion_logger convenience function."""
        logger = project_logging.get_ingestion_logger()
        assert isinstance(logger, logging.Logger)
        assert "ingestion" in logger.name
        assert len(logger.handlers) > 0

    def test_predefined_modeling_logger(self):
        """Test the get_modeling_logger convenience function."""
        logger = project_logging.get_modeling_logger()
        assert isinstance(logger, logging.Logger)
        assert "modeling" in logger.name
        assert len(logger.handlers) > 0

    def test_predefined_visualization_logger(self):
        """Test the get_visualization_logger convenience function."""
        logger = project_logging.get_visualization_logger()
        assert isinstance(logger, logging.Logger)
        assert "visualization" in logger.name
        assert len(logger.handlers) > 0

    def test_logger_formatting(self):
        """Test that loggers have the expected format string."""
        logger = project_logging.get_logger("test.format")
        # Check formatters on all handlers
        for handler in logger.handlers:
            if handler.formatter:
                fmt = handler.formatter._fmt
                assert "%(asctime)s" in fmt
                assert "%(levelname)s" in fmt
                assert "%(message)s" in fmt

    def test_no_duplicate_handlers(self):
        """Test that calling get_logger multiple times doesn't duplicate handlers."""
        logger = project_logging.get_logger("test.duplicates", to_file=True)
        initial_count = len(logger.handlers)

        # Call again with same name
        logger2 = project_logging.get_logger("test.duplicates", to_file=True)

        # Should be the same object or at least same number of handlers
        assert len(logger2.handlers) == initial_count
        assert logger is logger2  # Should be the same instance from the registry

    def test_log_output(self, caplog, tmp_path):
        """Test that logging actually produces output."""
        # Temporarily redirect log dir for this test to avoid cluttering real logs
        # We can't easily change the global _LOG_DIR, so we just check if the logger works
        logger = project_logging.get_logger("test.output", to_file=False)

        with caplog.at_level(logging.INFO):
            logger.info("Test message")
            logger.warning("Test warning")

        assert "Test message" in caplog.text
        assert "Test warning" in caplog.text

    def test_module_level_logger_exists(self):
        """Test that the module-level 'logger' variable exists and is valid."""
        assert hasattr(project_logging, "logger")
        assert isinstance(project_logging.logger, logging.Logger)
        assert project_logging.logger.name == "utils.logging"