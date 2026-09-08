"""
Tests for the logging configuration and error handling utilities.
"""
import os
import logging
import tempfile
from pathlib import Path
import pytest

# We need to import the module. Since the task creates code/logging_config.py,
# we assume the test runner adds 'code' to sys.path or we import relative to project root.
# For the purpose of this artifact, we assume the import path is correct in the test environment.
try:
    from logging_config import (
        logger,
        configure_logging,
        get_logger,
        raise_on_missing_data,
        verify_log_environment,
        LOG_FILE
    )
except ImportError:
    # Fallback for local execution if 'code' is not in path
    import sys
    sys.path.insert(0, 'code')
    from logging_config import (
        logger,
        configure_logging,
        get_logger,
        raise_on_missing_data,
        verify_log_environment,
        LOG_FILE
    )

def test_logger_initialization():
    """Test that the logger is initialized with INFO level."""
    assert logger.level == logging.INFO
    assert len(logger.handlers) >= 2  # File and Console

def test_get_logger_child():
    """Test that get_logger returns a child logger."""
    child = get_logger("test_child")
    assert child.name == "llmXive_pipeline.test_child"
    assert child.level == logging.INFO

def test_configure_logging():
    """Test that configure_logging updates the level."""
    configure_logging(logging.DEBUG)
    assert logger.level == logging.DEBUG
    # Reset to INFO
    configure_logging(logging.INFO)
    assert logger.level == logging.INFO

def test_raise_on_missing_data():
    """Test that raise_on_missing_data raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        raise_on_missing_data("http://fake-url.com/data.csv", "Connection timeout")
    
    assert "CRITICAL" in str(excinfo.value)
    assert "http://fake-url.com/data.csv" in str(excinfo.value)
    assert "Connection timeout" in str(excinfo.value)

def test_verify_log_environment(tmp_path):
    """Test that verify_log_environment works correctly."""
    # Temporarily override the LOG_DIR logic by mocking or just testing the function's logic
    # Since verify_log_environment relies on global LOG_DIR, we test the happy path
    # assuming the standard directory structure exists (created by T001).
    # If logs/ doesn't exist, T001 should have created it.
    # We can't easily mock the global LOG_DIR in this simple test without altering the module.
    # Instead, we rely on the fact that T001 created the directories.
    
    # Just ensure it returns True if the environment is standard
    # If logs/ is missing, it should create it and return True
    result = verify_log_environment()
    assert result is True
    assert LOG_FILE.exists() or LOG_FILE.parent.exists()

def test_log_file_creation():
    """Test that the log file is created if it doesn't exist."""
    # The logger initialization creates the file on first write or check.
    # We can trigger a log write to ensure the file exists.
    logger.info("Test log entry")
    assert LOG_FILE.exists()

def test_no_synthetic_fallback_logic():
    """
    Verify that the module does not contain any synthetic fallback logic.
    This is a code inspection test.
    """
    import inspect
    source = inspect.getsource(sys.modules[__name__].__dict__.get('raise_on_missing_data', None) or raise_on_missing_data)
    # Check that the function raises ValueError and does not return a mock object
    assert "raise ValueError" in source
    assert "return" not in source.split("raise ValueError")[0] # Ensure no return before raise