"""
Unit tests for the centralized logging module.
"""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure src is in path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logging import setup_logging, get_logger, set_log_level, LOG_DIR


class TestLoggingSetup:
    """Tests for logging configuration and initialization."""

    def test_setup_logging_creates_file_handler(self, tmp_path):
        """Verify that setup_logging creates a rotating file handler."""
        test_log_dir = tmp_path / "test_logs"
        test_log_file = test_log_dir / "test.log"

        with patch("src.utils.logging.LOG_DIR", test_log_dir):
            # Re-run setup with a fresh logger state
            logging.getLogger().handlers.clear()
            setup_logging(log_file=str(test_log_file), log_level=logging.DEBUG)

            root_logger = logging.getLogger()
            handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]

            assert len(handlers) > 0, "File handler should be created"
            assert any(isinstance(h, logging.handlers.RotatingFileHandler) for h in root_logger.handlers)

    def test_setup_logging_creates_stream_handler(self):
        """Verify that setup_logging creates a stream handler for stderr."""
        root_logger = logging.getLogger()
        # Clear to test fresh setup
        root_logger.handlers.clear()
        setup_logging()

        stream_handlers = [
            h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(stream_handlers) > 0, "Stream handler should be created"

    def test_log_file_directory_created(self):
        """Verify that the log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_log_dir = Path(tmp_dir) / "nonexistent" / "logs"
            test_log_file = test_log_dir / "test.log"

            with patch("src.utils.logging.LOG_DIR", test_log_dir):
                logging.getLogger().handlers.clear()
                setup_logging(log_file=str(test_log_file), log_level=logging.INFO)

                assert test_log_dir.exists(), "Log directory should be created"
                # File might not exist if no logs written, but dir must exist

    def test_get_logger_returns_configured_instance(self):
        """Verify that get_logger returns a properly configured logger."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
        # Check that it inherits handlers from root
        assert len(logger.handlers) == 0  # Loggers usually don't have direct handlers unless added
        assert len(logging.getLogger().handlers) > 0

    def test_get_logger_without_name(self):
        """Verify get_logger returns root logger when name is None."""
        logger = get_logger()
        assert logger.name == "root"

    def test_set_log_level_updates_all_handlers(self):
        """Verify that set_log_level updates the level for root and handlers."""
        initial_level = logging.getLogger().level
        new_level = logging.DEBUG

        set_log_level(new_level)

        assert logging.getLogger().level == new_level
        for handler in logging.getLogger().handlers:
            assert handler.level == new_level

    def test_log_formatting(self, tmp_path, caplog):
        """Verify that log messages are formatted correctly."""
        test_log_dir = tmp_path / "format_test"
        test_log_file = test_log_dir / "format.log"

        with patch("src.utils.logging.LOG_DIR", test_log_dir):
            logging.getLogger().handlers.clear()
            setup_logging(log_file=str(test_log_file), log_level=logging.DEBUG)

            logger = get_logger("test_formatter")
            logger.info("Test message")

            # Check caplog for formatted output
            assert any("test_formatter" in msg for msg in caplog.messages)
            # The actual formatting is verified by the presence of the module name in the log