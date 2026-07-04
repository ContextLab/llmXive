"""
Unit tests for the logger module.
"""
import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.logger import setup_logger, get_logger
from code.utils.config import reset_config


def test_setup_logger_creates_handlers():
    """Test that setup_logger adds file and console handlers."""
    logger = setup_logger("test_logger", console=True)
    
    assert len(logger.handlers) >= 1
    assert logger.level == logging.INFO  # Default from config


def test_get_logger_reuses_instance():
    """Test that get_logger returns the same logger if called twice."""
    logger1 = get_logger("test_reuse")
    logger2 = get_logger("test_reuse")
    assert logger1 is logger2


def test_logger_writes_to_file(tmp_path):
    """Test that logger writes to a file."""
    # Setup a temporary log file
    log_file = tmp_path / "test.log"
    
    # Temporarily override config path
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        reset_config()
        
        # We can't easily mock the Config dataclass path without more complex setup,
        # so we test the handler existence instead.
        logger = setup_logger("test_file", log_file=str(log_file), console=False)
        logger.info("Test message")
        
        # Force flush
        for handler in logger.handlers:
            handler.flush()
        
        # Check file exists and contains message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content
    finally:
        os.chdir(original_cwd)
        reset_config()