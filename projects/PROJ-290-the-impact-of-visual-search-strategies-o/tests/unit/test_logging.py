"""
Unit tests for the logging infrastructure (T004).
"""
import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.logging import get_logger, setup_logging


class TestLoggingSetup:
    """Tests for setup_logging function."""

    def test_setup_creates_log_file(self, tmp_path):
        """Verify that setup_logging creates the log directory and file."""
        log_dir = tmp_path / "logs"
        log_file = "test.log"

        setup_logging(
            level=logging.INFO,
            log_dir=log_dir,
            log_file=log_file,
            console=False,
        )

        log_path = log_dir / log_file
        assert log_path.exists(), "Log file should be created"

    def test_setup_writes_message(self, tmp_path):
        """Verify that setup_logging writes an initialization message."""
        log_dir = tmp_path / "logs"
        log_file = "test.log"

        setup_logging(
            level=logging.INFO,
            log_dir=log_dir,
            log_file=log_file,
            console=False,
        )

        log_path = log_dir / log_file
        content = log_path.read_text()

        assert "Logging initialized" in content, "Should contain initialization message"

    def test_get_logger_returns_configured_logger(self, tmp_path):
        """Verify that get_logger returns a logger with handlers."""
        log_dir = tmp_path / "logs"
        log_file = "test.log"

        setup_logging(
            level=logging.INFO,
            log_dir=log_dir,
            log_file=log_file,
            console=False,
        )

        logger = get_logger("test_module")

        assert logger is not None, "Logger should not be None"
        assert len(logger.handlers) > 0, "Logger should have handlers"
        assert logger.level == logging.INFO, "Logger level should be INFO"

    def test_logger_writes_messages(self, tmp_path):
        """Verify that logger writes messages to file."""
        log_dir = tmp_path / "logs"
        log_file = "test.log"

        setup_logging(
            level=logging.DEBUG,
            log_dir=log_dir,
            log_file=log_file,
            console=False,
        )

        logger = get_logger("test_write")
        test_message = "Test message for verification"
        logger.info(test_message)

        log_path = log_dir / log_file
        content = log_path.read_text()

        assert test_message in content, f"Log should contain: {test_message}"

    def test_multiple_calls_dont_duplicate_handlers(self, tmp_path):
        """Verify that calling setup_logging multiple times doesn't duplicate handlers."""
        log_dir = tmp_path / "logs"
        log_file = "test.log"

        setup_logging(
            level=logging.INFO,
            log_dir=log_dir,
            log_file=log_file,
            console=False,
        )

        # Get initial handler count
        initial_count = len(logging.getLogger().handlers)

        # Call setup again
        setup_logging(
            level=logging.INFO,
            log_dir=log_dir,
            log_file=log_file,
            console=False,
        )

        final_count = len(logging.getLogger().handlers)

        assert initial_count == final_count, "Handler count should not increase on re-setup"
