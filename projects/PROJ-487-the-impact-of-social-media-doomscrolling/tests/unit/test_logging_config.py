"""
Unit tests for the logging infrastructure.
"""
import os
import tempfile
from pathlib import Path
import logging
import pytest

# We need to add the code directory to the path if not already done
# Assuming this test runs from the project root or code directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from logging_config import setup_logging, get_logger, LOG_DIR

def test_setup_logging_creates_files():
    """Test that setup_logging creates the log files and directory."""
    # Ensure the directory exists (it should be created by setup_logging if missing)
    # We use a temporary directory for safety in testing if needed, 
    # but the task specifies output/logs/
    
    # Call setup_logging
    logger = setup_logging(log_level=logging.DEBUG)
    
    # Check that the log directory exists
    assert LOG_DIR.exists(), f"Log directory {LOG_DIR} was not created."
    
    # Check that log files exist (or at least the handler is configured)
    # The files might not be created immediately if no logs are written, 
    # but the handler should point to them.
    # Let's force a log write to ensure file creation
    test_logger = get_logger("test_file_creation")
    test_logger.info("Forcing log creation")
    
    assert (LOG_DIR / "pipeline.log").exists(), "pipeline.log was not created."
    assert (LOG_DIR / "errors.log").exists(), "errors.log was not created."

def test_get_logger_returns_instance():
    """Test that get_logger returns a valid Logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"

def test_error_handler_catches_exceptions():
    """Test that errors are logged to the error log file."""
    # Use a temporary file for error log to isolate test
    with tempfile.TemporaryDirectory() as tmpdir:
        error_log_path = Path(tmpdir) / "test_errors.log"
        
        logger = setup_logging(error_log_file=error_log_path)
        test_logger = get_logger("test_error")
        
        # Trigger an error
        try:
            raise ValueError("Test exception for logging")
        except Exception:
            test_logger.exception("Caught an exception")
        
        # Verify error log file exists and contains the error
        assert error_log_path.exists(), "Error log file was not created."
        
        with open(error_log_path, "r") as f:
            content = f.read()
            assert "Test exception for logging" in content
            assert "ValueError" in content

def test_console_handler_exists():
    """Test that a console handler is attached to the root logger."""
    logger = setup_logging()
    # The root logger should have a StreamHandler
    stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) > 0, "No console handler found."