"""
Unit tests for the logging configuration module.
"""
import os
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the project structure slightly or ensure imports work
# Since we are running from tests/unit, we need to ensure the parent code is importable.
# Assuming pytest is run from project root or PYTHONPATH is set correctly.

from utils.logger import setup_logging, get_logger, get_log_path, _LOGS_DIR, _CONFIGURED

# Helper to reset logger state for testing
def reset_logger_state():
    import utils.logger
    utils.logger._CONFIGURED = False
    utils.logger._LOG_FILE_NAME = None
    # Clear handlers from root logger
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)

class TestLoggerConfiguration:
    """Tests for logger setup and configuration."""

    def setup_method(self):
        """Reset logger state before each test."""
        reset_logger_state()

    def test_setup_logging_creates_file(self):
        """Test that setup_logging creates a log file in data/raw/logs/."""
        # Ensure the directory exists for the test
        _LOGS_DIR.mkdir(parents=True, exist_ok=True)

        logger = setup_logging(level=logging.INFO, enable_console=False)

        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.INFO

        # Check that a log path was generated
        log_path = get_log_path()
        assert log_path.exists(), f"Log file was not created at {log_path}"
        assert log_path.suffix == ".log"

    def test_setup_logging_adds_file_handler(self):
        """Test that a FileHandler is added to the root logger."""
        logger = setup_logging(level=logging.INFO, enable_console=False)

        handlers = logger.handlers
        file_handlers = [h for h in handlers if isinstance(h, logging.FileHandler)]

        assert len(file_handlers) > 0, "No FileHandler found in root logger"

    def test_setup_logging_adds_console_handler(self):
        """Test that a StreamHandler is added if enable_console is True."""
        logger = setup_logging(level=logging.INFO, enable_console=True)

        handlers = logger.handlers
        stream_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)]

        assert len(stream_handlers) > 0, "No StreamHandler found when enable_console=True"

    def test_get_logger_returns_configured_logger(self):
        """Test that get_logger returns a valid logger instance."""
        setup_logging(enable_console=False)
        named_logger = get_logger("test_module")

        assert named_logger is not None
        assert named_logger.name == "test_module"

    def test_write_log_message(self):
        """Test that a log message is actually written to the file."""
        setup_logging(level=logging.INFO, enable_console=False)
        logger = get_logger("test_write")

        test_msg = "Test log message for T006 verification"
        logger.info(test_msg)

        # Force flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        log_path = get_log_path()
        assert log_path.exists()

        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert test_msg in content, "Log message not found in file content"

    def test_get_log_path_raises_before_setup(self):
        """Test that get_log_path raises ValueError if not configured."""
        reset_logger_state()
        with pytest.raises(ValueError, match="Logging has not been configured"):
            get_log_path()

    def test_idempotent_setup(self):
        """Test that calling setup_logging multiple times doesn't duplicate handlers."""
        setup_logging(level=logging.INFO, enable_console=False)
        count_before = len(logging.getLogger().handlers)

        setup_logging(level=logging.INFO, enable_console=False)
        count_after = len(logging.getLogger().handlers)

        # Should remain the same because _CONFIGURED prevents re-initialization
        assert count_before == count_after, "Handlers were duplicated on second call"