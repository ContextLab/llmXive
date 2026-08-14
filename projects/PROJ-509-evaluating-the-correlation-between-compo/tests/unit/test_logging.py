"""
Unit tests for logging utilities in code/utils/logging.py.
"""
import pytest
import logging
import tempfile
import os
from pathlib import Path

from code.utils.logging import setup_logging, get_logger


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_console_handler_added(self):
        """Test that console handler is added."""
        logger = setup_logging(log_level=logging.INFO)
        handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(handlers) > 0

    def test_log_level_set(self):
        """Test that log level is set correctly."""
        logger = setup_logging(log_level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_file_handler_added(self):
        """Test that file handler is added when log_file is specified."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            log_path = f.name

        try:
            logger = setup_logging(log_file=log_path)
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0
        finally:
            if os.path.exists(log_path):
                os.unlink(log_path)

    def test_formatter_set(self):
        """Test that formatter is set."""
        logger = setup_logging()
        for handler in logger.handlers:
            assert handler.formatter is not None

    def test_clears_existing_handlers(self):
        """Test that existing handlers are cleared."""
        # Add a dummy handler
        root_logger = logging.getLogger()
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)

        try:
            setup_logging()
            # Check that the dummy handler is removed
            assert dummy_handler not in root_logger.handlers
        finally:
            root_logger.removeHandler(dummy_handler)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)

    def test_custom_name(self):
        """Test with custom logger name."""
        logger = get_logger(name='test_logger')
        assert logger.name == 'test_logger'

    def test_default_name(self):
        """Test with default name (module name)."""
        logger = get_logger()
        # Default should be the module name or __name__
        assert logger is not None

    def test_multiple_calls_same_logger(self):
        """Test that multiple calls with same name return same logger."""
        logger1 = get_logger('shared_logger')
        logger2 = get_logger('shared_logger')
        assert logger1 is logger2

    def test_different_names_different_loggers(self):
        """Test that different names return different logger instances."""
        logger1 = get_logger('logger_a')
        logger2 = get_logger('logger_b')
        assert logger1 is not logger2
        assert logger1.name != logger2.name