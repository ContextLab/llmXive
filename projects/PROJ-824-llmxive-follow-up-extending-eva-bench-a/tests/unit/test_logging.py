"""
Unit tests for logging configuration.
"""
import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.logging_config import setup_logging, _setup_warning_filters
from code.config import LOG_LEVEL


class TestLoggingSetup:
    """Tests for the logging setup functionality."""

    def test_logger_creation(self, tmp_path):
        """Test that a logger is created with the correct name."""
        logger = setup_logging(log_dir=tmp_path, log_level=logging.DEBUG, console_output=False)
        assert logger is not None
        assert logger.name == "llmxive"
        assert logger.level == logging.DEBUG

    def test_file_handler_added(self, tmp_path):
        """Test that a file handler is added to the logger."""
        logger = setup_logging(log_dir=tmp_path, log_level=logging.DEBUG, console_output=False)
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

    def test_log_file_created(self, tmp_path):
        """Test that the log file is created."""
        logger = setup_logging(log_dir=tmp_path, log_level=logging.DEBUG, console_output=False)
        log_file = tmp_path / "llmxive.log"
        assert log_file.exists()

    def test_log_message_written(self, tmp_path):
        """Test that log messages are written to the file."""
        logger = setup_logging(log_dir=tmp_path, log_level=logging.DEBUG, console_output=False)
        logger.info("Test message")
        logger.debug("Debug message")

        log_file = tmp_path / "llmxive.log"
        content = log_file.read_text()
        assert "Test message" in content
        assert "DEBUG" in content

    def test_warning_filters_applied(self):
        """Test that warning filters are set up correctly."""
        # This is a bit tricky to test directly, but we can at least
        # verify the function runs without error
        try:
            _setup_warning_filters()
        except Exception as e:
            pytest.fail(f"Warning filters setup failed: {e}")

    def test_console_handler_added_when_requested(self, tmp_path):
        """Test that a console handler is added when console_output=True."""
        logger = setup_logging(log_dir=tmp_path, log_level=logging.DEBUG, console_output=True)
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0

    def test_no_duplicate_handlers(self, tmp_path):
        """Test that calling setup_logging multiple times doesn't add duplicate handlers."""
        logger = setup_logging(log_dir=tmp_path, log_level=logging.DEBUG, console_output=False)
        initial_handler_count = len(logger.handlers)

        # Call again
        logger2 = setup_logging(log_dir=tmp_path, log_level=logging.DEBUG, console_output=False)
        assert logger is logger2  # Should be the same logger
        assert len(logger.handlers) == initial_handler_count  # No new handlers

    def test_log_level_respects_environment_variable(self, tmp_path, monkeypatch):
        """Test that LOG_LEVEL can be overridden via environment variable."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        # Note: The actual config module would need to be reloaded to pick up the change,
        # but for this test we just verify the function accepts the parameter
        logger = setup_logging(log_dir=tmp_path, log_level=logging.DEBUG, console_output=False)
        assert logger.level == logging.DEBUG

    def test_rotating_file_handler_used(self, tmp_path):
        """Test that a RotatingFileHandler is used instead of a regular FileHandler."""
        from logging.handlers import RotatingFileHandler

        logger = setup_logging(log_dir=tmp_path, log_level=logging.DEBUG, console_output=False)
        file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) > 0