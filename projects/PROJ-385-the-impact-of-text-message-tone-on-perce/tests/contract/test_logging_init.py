"""
Test that logging infrastructure initializes correctly and writes to file.
"""
import os
import pytest
from pathlib import Path

# Ensure we can import from the code directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_processed_data_dir
from logging_config import setup_logging, get_logger

def test_logging_creates_file():
    """Test that importing and calling setup_logging creates the log file."""
    log_file = get_processed_data_dir() / "pipeline.log"
    
    # Remove existing log file if present to ensure fresh creation
    if log_file.exists():
        log_file.unlink()
    
    # Setup logging (this should create the file)
    logger = setup_logging()
    
    # Verify file exists
    assert log_file.exists(), f"Log file {log_file} was not created by setup_logging()"
    
    # Verify file is not empty (should contain startup message)
    content = log_file.read_text()
    assert len(content) > 0, "Log file is empty after initialization"
    assert "Pipeline logging initialized" in content, "Startup message not found in log"

def test_logger_retrieval():
    """Test that get_logger returns a valid logger instance."""
    logger = get_logger("test_module")
    assert logger is not None
    assert logger.name == "test_module"

def test_logging_functions_exist():
    """Test that helper functions are callable."""
    logger = get_logger("test")
    # These should not raise
    from logging_config import log_pipeline_step, log_exclusion
    log_pipeline_step("test_step", logger)
    log_exclusion("test_reason", "test_id", logger)