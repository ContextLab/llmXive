import logging
import os
import tempfile
from pathlib import Path

import pytest

# Mock config before importing logging_config to avoid dependency on real config path
class MockConfig:
    LOGS_DIR = tempfile.mkdtemp()

import sys
sys.modules['config'] = MockConfig()

from logging_config import setup_logger, get_logger, logger

def test_setup_logger_creates_file_handler():
    """Test that setup_logger creates a file handler when log_file is provided."""
    test_logger = setup_logger(name="test_file", log_file="test.log", console=False)
    assert isinstance(test_logger, logging.Logger)
    assert len(test_logger.handlers) == 1
    assert isinstance(test_logger.handlers[0], logging.FileHandler)

    # Verify file was created
    log_path = Path(MockConfig.LOGS_DIR) / "test.log"
    assert log_path.exists()

def test_setup_logger_creates_console_handler():
    """Test that setup_logger creates a console handler when console=True."""
    test_logger = setup_logger(name="test_console", console=True, log_file=None)
    assert isinstance(test_logger, logging.Logger)
    assert len(test_logger.handlers) == 1
    assert isinstance(test_logger.handlers[0], logging.StreamHandler)

def test_setup_logger_creates_both_handlers():
    """Test that setup_logger creates both handlers when both options are True."""
    test_logger = setup_logger(
        name="test_both", log_file="test_both.log", console=True
    )
    assert isinstance(test_logger, logging.Logger)
    assert len(test_logger.handlers) == 2

def test_get_logger_returns_existing():
    """Test that get_logger returns existing logger without re-configuring."""
    # First call configures
    logger1 = get_logger(name="test_existing")
    initial_handler_count = len(logger1.handlers)

    # Second call should return same logger with same handlers
    logger2 = get_logger(name="test_existing")
    assert logger1 is logger2
    assert len(logger2.handlers) == initial_handler_count

def test_default_logger_exists():
    """Test that the module-level default logger is configured."""
    assert isinstance(logger, logging.Logger)
    assert len(logger.handlers) > 0

def test_log_levels_respected():
    """Test that log level filtering works."""
    test_logger = setup_logger(
        name="test_level", level=logging.WARNING, log_file="test_level.log", console=False
    )

    # This should be logged
    test_logger.warning("Warning message")
    # This should not be logged
    test_logger.info("Info message")

    # Read file and verify content
    log_path = Path(MockConfig.LOGS_DIR) / "test_level.log"
    content = log_path.read_text()

    assert "Warning message" in content
    assert "Info message" not in content