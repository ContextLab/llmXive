"""
Unit tests for the logging infrastructure (T006).
"""
import os
import logging
import pytest
from pathlib import Path
import sys

# Ensure the code directory is in the path
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from logging_config import get_logger, LOG_FILE, setup_logging, LOG_DIR

def test_log_file_exists():
    """Test that the log file path is correctly defined and the directory exists."""
    assert LOG_DIR.exists(), f"Log directory {LOG_DIR} does not exist."
    # The file might not exist until logging happens, but the directory must be ready.
    assert LOG_DIR.is_dir()

def test_logger_creation():
    """Test that a logger can be created and configured."""
    setup_logging()
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "proj268.test_module"
    assert logger.level == logging.DEBUG  # Inherited from root

def test_logger_output():
    """Test that logging actually writes to the file."""
    test_logger = get_logger("test_output")
    test_msg = "Test log message for T006 verification"
    
    # Clear previous logs for this specific test message if needed, 
    # but since we append, we just check the file exists and has content.
    test_logger.info(test_msg)
    
    # Force flush
    for handler in test_logger.handlers:
        handler.flush()
    
    assert LOG_FILE.exists(), "Log file was not created."
    
    content = LOG_FILE.read_text()
    assert test_msg in content, f"Log message '{test_msg}' not found in {LOG_FILE}"
    assert "INFO" in content, "Log level not recorded correctly."
    assert "test_output" in content, "Logger name not recorded correctly."

def test_multiple_loggers():
    """Test that child loggers propagate correctly."""
    parent_logger = get_logger("parent")
    child_logger = get_logger("parent.child")
    
    assert child_logger.name == "proj268.parent.child"
    # Verify they share handlers (propagation)
    # In our config, handlers are on the root 'proj268' logger.
    # Child loggers propagate to root by default.
    assert child_logger.propagate is True