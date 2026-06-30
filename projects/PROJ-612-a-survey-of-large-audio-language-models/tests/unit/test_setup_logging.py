import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_logging import (
    get_logger,
    init_logging,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
    LOGS_DIR,
    LOG_FILE_PATH
)

def test_logger_creation():
    """Test that a logger is created and configured correctly."""
    logger = get_logger("test_unit_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_unit_logger"
    assert logger.level == logging.DEBUG
    # Check that handlers are added
    assert len(logger.handlers) > 0

def test_log_file_creation():
    """Test that the log file is created upon logging."""
    test_logger = get_logger("test_file_creation")
    test_logger.info("Test message for file creation")
    
    # Force flush to ensure file is written
    for handler in test_logger.handlers:
        handler.flush()
    
    assert LOG_FILE_PATH.exists(), f"Log file {LOG_FILE_PATH} was not created."

def test_log_content_format():
    """Test that log messages contain expected format components."""
    test_logger = get_logger("test_format")
    test_logger.info("Test format message")
    
    for handler in test_logger.handlers:
        handler.flush()
    
    with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for timestamp and level
    assert "20" in content  # Basic check for year
    assert "INFO" in content
    assert "Test format message" in content

def test_log_error_function():
    """Test the log_error utility function."""
    test_logger = get_logger("test_error_func")
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_error(e, "Unit Test Context")
    
    for handler in test_logger.handlers:
        handler.flush()

def test_pipeline_start_end_logging():
    """Test start and end logging functions."""
    test_logger = get_logger("test_lifecycle")
    log_pipeline_start()
    log_pipeline_end()
    
    for handler in test_logger.handlers:
        handler.flush()
    
    with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "Pipeline run started" in content
    assert "Pipeline run completed successfully" in content