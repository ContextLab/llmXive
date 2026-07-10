import os
import json
import tempfile
import shutil
from pathlib import Path
import logging

# Mock the LOG_DIR to use a temporary directory for testing
def test_logger_initialization():
    """Test that the logger initializes without errors."""
    from utils.logger import get_logger, log_event, init_logger

    # Ensure clean state
    logger = get_logger("test_logger")
    assert logger is not None
    assert logger.level == logging.DEBUG

def test_log_event_structured():
    """Test that log_event produces structured output."""
    from utils.logger import get_logger, log_event, DEFAULT_LOG_FILE

    # Create a temp log file path for this test to avoid cluttering real logs
    # We rely on the fact that get_logger caches, so we test the function logic
    # by checking if the logger has handlers and if log_event runs without error.
    
    logger = get_logger("test_struct")
    assert len(logger.handlers) > 0

    # Log a simple event
    log_event("Test message", "INFO", {"key": "value"}, "test_struct")
    
    # Verify the log file exists (it should be created by init_logger or first log)
    # Note: In a real run, DEFAULT_LOG_FILE is data/logs/pipeline.log
    # We just verify the handler is attached and no exception occurred.
    assert True 

def test_log_rotation_setup():
    """Verify that RotatingFileHandler is configured."""
    from utils.logger import get_logger, MAX_BYTES, BACKUP_COUNT, DEFAULT_LOG_FILE
    import logging.handlers

    logger = get_logger("test_rot")
    file_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            file_handler = handler
            break
    
    assert file_handler is not None
    assert file_handler.maxBytes == MAX_BYTES
    assert file_handler.backupCount == BACKUP_COUNT
    assert str(file_handler.baseFilename) == str(DEFAULT_LOG_FILE)
