"""
Unit tests for logging utility functionality.
"""
import logging
import tempfile
import os
from pathlib import Path

from code.logging_utils import setup_logger


def test_logger_creation():
    """Test that a logger is created successfully."""
    logger = setup_logger(name="test_logger")
    assert logger is not None
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO


def test_logger_handlers():
    """Test that the logger has the expected handlers."""
    logger = setup_logger(name="test_logger_handlers")
    # Should have at least one handler (console)
    assert len(logger.handlers) >= 1
    # Check for StreamHandler
    has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    assert has_stream


def test_file_handler_creation():
    """Test that a file handler is created when a log file is specified."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = os.path.join(tmp_dir, "test.log")
        logger = setup_logger(name="test_file_logger", log_file=log_path)

        # Check for FileHandler
        has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert has_file

        # Ensure file exists and is not empty after a log
        logger.info("Test message")
        assert os.path.exists(log_path)
        assert os.path.getsize(log_path) > 0
