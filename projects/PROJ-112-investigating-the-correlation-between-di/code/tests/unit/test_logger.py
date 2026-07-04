"""
Unit tests for the logging utility.
"""

import pytest
import logging
import os
from pathlib import Path
from utils.logger import get_logger, _LOG_DIR, _LOG_FILE


@pytest.fixture
def clean_loggers():
    """Fixture to reset logger cache before and after tests."""
    from utils import logger
    # Save original state
    original_cache = dict(logger._LOGGERS)
    original_handlers = {}
    
    # Clear cache
    logger._LOGGERS.clear()
    
    yield

    # Restore state (optional, but good for isolation in some runners)
    logger._LOGGERS.clear()
    logger._LOGGERS.update(original_cache)


def test_get_logger_returns_logger(clean_loggers):
    """Test that get_logger returns a valid logging.Logger instance."""
    logger_instance = get_logger("test_module")
    assert isinstance(logger_instance, logging.Logger)
    assert logger_instance.name == "test_module"


def test_get_logger_configured_handlers(clean_loggers):
    """Test that the returned logger has both file and console handlers."""
    logger_instance = get_logger("test_handlers")
    
    assert len(logger_instance.handlers) == 2, "Logger should have exactly 2 handlers"
    
    handler_types = {type(h).__name__ for h in logger_instance.handlers}
    assert "FileHandler" in handler_types, "Logger must have a FileHandler"
    assert "StreamHandler" in handler_types, "Logger must have a StreamHandler"


def test_get_logger_unique_name(clean_loggers):
    """Test that loggers with different names are distinct instances in the cache."""
    logger_a = get_logger("module_a")
    logger_b = get_logger("module_b")
    
    assert logger_a is not logger_b
    assert logger_a.name == "module_a"
    assert logger_b.name == "module_b"


def test_get_logger_caching(clean_loggers):
    """Test that calling get_logger with the same name returns the same instance."""
    logger_a = get_logger("module_cache")
    logger_b = get_logger("module_cache")
    
    assert logger_a is logger_b


def test_log_file_directory_created(clean_loggers):
    """Test that the log directory is created if it doesn't exist."""
    # Force a logger creation to trigger directory creation
    _ = get_logger("trigger_dir")
    
    assert _LOG_DIR.exists(), "Log directory should be created"
    assert _LOG_DIR.is_dir(), "Log path should be a directory"