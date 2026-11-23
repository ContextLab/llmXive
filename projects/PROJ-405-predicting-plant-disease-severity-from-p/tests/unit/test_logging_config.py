"""
Unit tests for code/utils/logging_config.py
"""
import pytest
import logging
from utils.logging_config import setup_logging, get_logger, ColoredFormatter

def test_setup_logging_creates_logger():
    """Test that setup_logging initializes the root logger."""
    logger = setup_logging(level="DEBUG")
    assert logger is not None
    assert logger.level == logging.DEBUG

def test_get_logger_returns_singleton():
    """Test that get_logger returns the same instance for the same name."""
    logger1 = get_logger("test_singleton")
    logger2 = get_logger("test_singleton")
    assert logger1 is logger2

def test_colored_formatter_has_styles():
    """Test that ColoredFormatter has color codes defined."""
    formatter = ColoredFormatter()
    # Just checking instantiation and basic attributes
    assert hasattr(formatter, 'format')
