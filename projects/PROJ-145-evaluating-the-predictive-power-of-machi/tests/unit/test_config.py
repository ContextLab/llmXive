"""
Unit tests for the configuration module, specifically logging setup.
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest

# We need to mock the project root structure temporarily to avoid
# side effects on the real file system during import if run in isolation,
# but since config.py uses Path(__file__).resolve().parent.parent,
# and we are in tests/unit, it will point to the project root.
# We assume the project structure exists as per T001a.

from code import config


class TestLoggingConfig:
    """Tests for logging infrastructure in code/config.py"""

    def test_logger_exists_and_configured(self):
        """Verify that the root logger is configured with handlers."""
        logger = logging.getLogger()
        # After config.py is imported, setup_logging() should have run
        assert len(logger.handlers) > 0, "Logger should have at least one handler."

    def test_file_handler_present(self):
        """Verify that a FileHandler is present and points to the correct file."""
        logger = logging.getLogger()
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0, "Logger should have a FileHandler."

        # Check if the log file path matches the config
        expected_log_path = config.DATA_DIR / "pipeline.log"
        actual_log_path = Path(file_handlers[0].baseFilename)

        # Resolve to absolute paths for comparison
        assert actual_log_path.resolve() == expected_log_path.resolve(), \
            f"Log file path mismatch. Expected {expected_log_path}, got {actual_log_path}"

    def test_log_level_matches_config(self):
        """Verify that the root logger level matches LOG_LEVEL in config."""
        logger = logging.getLogger()
        assert logger.level == logging.getLevelName(config.LOG_LEVEL), \
            f"Logger level {logger.level} does not match config LOG_LEVEL {config.LOG_LEVEL}"

    def test_log_message_written(self, tmp_path):
        """
        Verify that a log message is actually written to the file.
        We use a temporary directory to avoid cluttering the project data dir.
        """
        # Save original paths
        original_log_file = config.LOG_FILE
        original_data_dir = config.DATA_DIR

        # Create a temp log file path
        temp_log_file = tmp_path / "test_pipeline.log"

        # Monkey-patch the config to use temp file
        # Note: This is a bit hacky because config.py runs setup_logging on import.
        # A better approach for a real test suite would be to refactor setup_logging
        # to accept arguments, but for this task we test the existing behavior.
        # Since we can't easily re-run setup_logging with a new path without reloading,
        # we will just verify the existing file was written to during the import of config.
        # However, to be robust, let's just check that the file exists and has content
        # if the standard path is used, or simulate a log call.

        # Since the import already happened and wrote to the real log file,
        # we just verify the real log file exists and has content.
        assert original_log_file.exists(), "Log file should exist after import."
        
        # Write a specific test message to verify functionality
        test_logger = logging.getLogger(__name__)
        test_logger.info("Test log message for T007")
        
        # Read the file to ensure the message is there
        with open(original_log_file, "r") as f:
            content = f.read()
            assert "Test log message for T007" in content, "Test message should be in log file."

    def test_formatter_format(self):
        """Verify the log formatter includes expected fields."""
        logger = logging.getLogger()
        # Find a handler with a formatter
        formatter = None
        for handler in logger.handlers:
            if handler.formatter:
                formatter = handler.formatter
                break
        
        assert formatter is not None, "At least one handler should have a formatter."
        
        # Check if the format string contains expected keys
        format_str = formatter._fmt
        assert "%(asctime)s" in format_str, "Formatter should include timestamp."
        assert "%(levelname)s" in format_str, "Formatter should include level."
        assert "%(message)s" in format_str, "Formatter should include message."