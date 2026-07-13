"""
Unit tests for logging utilities.
"""
import pytest
import logging
from utils.logger import setup_logger, get_logger

def test_setup_logger():
    """Test logger setup."""
    logger = setup_logger("test_logger", level=logging.DEBUG)
    assert logger is not None
    assert logger.name == "test_logger"

def test_get_logger():
    """Test getting a logger."""
    logger = get_logger("test_get_logger")
    assert logger is not None
