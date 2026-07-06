import os
import logging
import pytest
from pathlib import Path
from code.logging_config import setup_logging, get_logger

def test_setup_logging_creates_file():
    """Test that setup_logging creates the log directory and file."""
    # Clean up any existing test log first
    log_path = Path("data/logs/pipeline.log")
    if log_path.exists():
        os.remove(log_path)
    
    # Setup
    logger = setup_logging(log_level="INFO", log_file="pipeline.log")
    
    # Assertions
    assert logger is not None
    assert isinstance(logger, logging.Logger)
    assert logger.name == "crack_propagation_ml"
    assert log_path.exists(), "Log file should be created by setup_logging"
    
    # Check file is not empty (should have the initialization message)
    assert log_path.stat().st_size > 0, "Log file should contain initialization message"

def test_get_logger_returns_instance():
    """Test that get_logger returns a valid logger instance."""
    logger = get_logger("test_module")
    assert logger is not None
    assert logger.name == "test_module"
    assert isinstance(logger, logging.Logger)

def test_logging_levels():
    """Test that different log levels work."""
    # Reset root logger handlers for a clean test if needed, 
    # but here we just verify the logger accepts the level.
    logger = setup_logging(log_level="DEBUG", log_file="pipeline.log")
    
    # Verify we can call methods without error
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    # Verify file size increased
    log_path = Path("data/logs/pipeline.log")
    assert log_path.stat().st_size > 0