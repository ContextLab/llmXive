"""
Unit tests for the logging infrastructure.
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest

# We need to ensure config is set up before importing logging
# Since config uses absolute paths based on __file__, we assume the test runs from project root
# or we mock the config if necessary. For now, assume standard execution context.

def test_logger_creation():
    """Test that get_logger returns a valid logger instance."""
    from utils.logging import get_logger

    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"

def test_logging_output_format(tmp_path):
    """Test that logging output matches the expected format."""
    import sys
    from unittest.mock import patch
    
    # We need to temporarily override the config values to use our tmp_path
    # This is a bit tricky because config is imported at module level in logging.py
    # A cleaner approach is to test the formatter directly
    
    from utils.logging import LOG_FORMAT
    
    # Create a logger and handler to test the format
    logger = logging.getLogger("test_format")
    logger.handlers = [] # Clear any existing handlers
    
    # Create a temporary file for the log
    log_file = tmp_path / "test.log"
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Log a test message
    test_msg = "Test message"
    logger.info(test_msg)
    
    # Read the file and check format
    with open(log_file, 'r') as f:
        content = f.read()
    
    # The format is: %(asctime)s - %(levelname)s - %(message)s
    # We can't easily check the exact timestamp, but we can check the structure
    assert f"INFO - {test_msg}" in content
    assert " - " in content # Check for the separators

def test_log_file_creation(tmp_path):
    """Test that the log file is created in the specified directory."""
    # This test is a bit hard to run in isolation because setup_logging()
    # uses the global LOGS_DIR from config. We'll assume the config is correct
    # and just verify that the function doesn't crash and creates a file.
    
    from utils.logging import setup_logging
    from config import LOGS_DIR
    
    # Ensure the directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Call setup_logging
    setup_logging()
    
    # Check if the log file exists
    log_file = LOGS_DIR / "pipeline.log"
    assert log_file.exists()