import pytest
import logging
import os
from pathlib import Path
import sys

# Add the code directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event, LOG_FILE_PATH

def test_logger_writes_to_correct_file():
    """Test that the logger is configured to write to logs/pipeline.log"""
    logger = get_logger("test_logger")
    
    # Verify the file handler points to the correct path
    file_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler = handler
            break
    
    assert file_handler is not None, "Logger should have a FileHandler"
    assert Path(file_handler.baseFilename) == LOG_FILE_PATH, f"Log file should be {LOG_FILE_PATH}"

def test_log_exclusion_reason():
    """Test that exclusion reasons are logged correctly"""
    logger = get_logger("test_exclusion")
    
    # Clear handlers to ensure clean state for testing if needed, 
    # but here we just check the function doesn't crash and logs
    log_exclusion_reason("Missing ionic radius", {"element": "X"})
    
    # Verify the log file exists after logging
    assert LOG_FILE_PATH.exists(), "Log file should exist after logging exclusion"

def test_log_pipeline_event():
    """Test that pipeline events are logged correctly"""
    logger = get_logger("test_event")
    
    log_pipeline_event("Test Event", {"status": "success"})
    
    assert LOG_FILE_PATH.exists(), "Log file should exist after logging event"
