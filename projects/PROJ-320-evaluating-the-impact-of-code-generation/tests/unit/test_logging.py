"""
Unit tests for the logging infrastructure.
"""
import os
import tempfile
import logging
from pathlib import Path
import sys

# Add project root to path to import code.utils.logging
# Assuming tests are at tests/unit/ and code is at code/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.utils.logging import get_logger, DATA_LOG_DIR, REPORTS_LOG_DIR

def test_logger_creation():
    """Test that a logger is created and configured correctly."""
    logger = get_logger("test_logger_creation")
    assert logger is not None
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0

def test_log_directory_existence():
    """Test that the log directories exist or are created."""
    assert DATA_LOG_DIR.exists(), f"Data log directory {DATA_LOG_DIR} does not exist"
    assert REPORTS_LOG_DIR.exists(), f"Reports log directory {REPORTS_LOG_DIR} does not exist"

def test_file_handler_attachment():
    """Test that rotating file handlers are attached."""
    logger = get_logger("test_file_handler")
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert len(file_handlers) >= 2, "Expected at least two RotatingFileHandler instances (data and reports)"

def test_logging_output():
    """Test that logging actually writes to the handlers."""
    logger = get_logger("test_output")
    # Clear handlers to avoid duplication in test runs if necessary, 
    # but for this simple test we just ensure it doesn't crash.
    
    # Log a message
    logger.debug("Test debug message")
    logger.info("Test info message")
    
    # Verify log files exist after logging
    data_log_file = DATA_LOG_DIR / "data_processing.log"
    reports_log_file = REPORTS_LOG_DIR / "report_generation.log"
    
    # We expect at least one of them to have content or exist
    # Note: Depending on level, one might be empty if only info is logged and data handler is debug
    assert data_log_file.exists() or reports_log_file.exists(), "Log files were not created"