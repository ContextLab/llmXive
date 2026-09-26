"""
Unit tests for logging configuration.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import setup_logging, get_logger
from utils import log_setup

def test_setup_logging_creates_handler():
    """Test that setup_logging adds a handler to the root logger."""
    logger = logging.getLogger()
    initial_count = len(logger.handlers)
    
    setup_logging()
    
    assert len(logger.handlers) > initial_count
    assert isinstance(logger.handlers[-1], logging.StreamHandler)

def test_get_logger_returns_instance():
    """Test that get_logger returns a valid logger instance."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    
    named_logger = get_logger("test_module")
    assert isinstance(named_logger, logging.Logger)
    assert named_logger.name == "test_module"

def test_log_setup_function():
    """Test the log_setup helper function."""
    logger = log_setup()
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO

def test_log_formatting():
    """Test that log messages are formatted correctly."""
    logger = get_logger()
    # We can't easily assert the exact format string, but we can ensure
    # the handler exists and is configured
    assert len(logger.handlers) > 0
    handler = logger.handlers[0]
    assert handler.formatter is not None
    assert '%(asctime)s' in handler.formatter._fmt