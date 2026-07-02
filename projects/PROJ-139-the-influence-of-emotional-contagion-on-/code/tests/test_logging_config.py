"""
Unit tests for logging configuration.
"""
import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.logging_config import get_logger, setup_root_logger, LOG_DIR

def test_get_logger_creates_instance():
    """Test that get_logger returns a logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"

def test_get_logger_returns_same_instance():
    """Test that calling get_logger multiple times returns the same instance."""
    logger1 = get_logger("test_singleton")
    logger2 = get_logger("test_singleton")
    assert logger1 is logger2

def test_logger_has_handlers():
    """Test that logger has both console and file handlers."""
    logger = get_logger("test_handlers")
    assert len(logger.handlers) >= 2  # Console + File

def test_log_file_created():
    """Test that log files are created in the state/logs directory."""
    # Ensure directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = get_logger("test_file_creation")
    logger.info("Test message")
    
    # Check that at least one log file exists
    log_files = list(LOG_DIR.glob("test_file_creation_*.log"))
    assert len(log_files) > 0

def test_setup_root_logger():
    """Test that setup_root_logger initializes the root logger."""
    setup_root_logger()
    root_logger = logging.getLogger("llmXive")
    assert len(root_logger.handlers) >= 2

def test_logger_levels():
    """Test that log levels are configured correctly."""
    logger = get_logger("test_levels")
    assert logger.level == logging.DEBUG
    
    # Check handler levels
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            assert handler.level == logging.INFO
