"""
Integration test for logging setup and configuration interaction.
"""
import pytest
import logging
import sys
from pathlib import Path
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import setup_logging, get_logger, get_config


def test_logging_integration():
    """Test that logging works end-to-end."""
    logger = setup_logging()
    
    # Test that we can log at different levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Verify logger is properly configured
    assert logger.level == logging.INFO  # Default level
    
    # Verify handlers are present
    assert len(logger.handlers) >= 2


def test_log_file_creation():
    """Test that log file is created."""
    logger = setup_logging()
    log_file = get_config("LOG_FILE")
    
    # The file should exist after logging
    assert Path(log_file).exists(), f"Log file not created at {log_file}"


def test_logger_singleton():
    """Test that logger is a singleton."""
    logger1 = get_logger()
    logger2 = get_logger()
    assert logger1 is logger2
