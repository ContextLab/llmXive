"""
Unit tests for the logging configuration utilities.
"""
import pytest
import logging
import os
import sys
from pathlib import Path
from utils.logging_config import setup_logging, get_logger
from config import get_log_level


def test_setup_logging_console():
    """Test that setup_logging configures a console handler."""
    logger = setup_logging()
    assert logger.handlers is not None
    assert len(logger.handlers) > 0
    
    # Check for StreamHandler
    has_stream_handler = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    assert has_stream_handler, "Console handler (StreamHandler) not found"


def test_setup_logging_file(tmp_path):
    """Test that setup_logging configures a file handler when log_file is provided."""
    log_file = str(tmp_path / "test.log")
    logger = setup_logging(log_file)
    
    # Check for FileHandler
    has_file_handler = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    assert has_file_handler, "File handler not found"
    
    # Verify file exists
    assert os.path.exists(log_file), "Log file was not created"


def test_get_logger_returns_instance():
    """Test that get_logger returns a logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_get_logger_root():
    """Test that get_logger returns root logger when name is None."""
    logger = get_logger()
    assert logger.name == "root"


def test_logger_level_configured():
    """Test that logger level is configured correctly."""
    expected_level = get_log_level()
    logger = setup_logging()
    assert logger.level == expected_level or logger.level == logging.NOTSET, \
        f"Logger level {logger.level} does not match expected {expected_level} (or NOTSET inheriting from root)"
    
    # Check handlers
    for handler in logger.handlers:
        if handler.level == logging.NOTSET:
            assert handler.level == expected_level or handler.level == logging.NOTSET
        else:
            assert handler.level == expected_level