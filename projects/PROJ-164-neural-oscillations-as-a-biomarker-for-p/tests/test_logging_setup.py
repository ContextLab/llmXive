"""
Unit tests for the logging infrastructure (T008).
"""
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to test the logic without relying on the global project path
# We will import the module directly and patch its internal path resolution if necessary,
# but primarily we test the functions' behavior.
import code.utils.logging_setup as logging_module


def test_get_logger_creation():
    """Test that get_logger returns a valid logger with handlers."""
    # Reset logger state for clean test
    test_logger = logging_module.get_logger("test_logger_creation")
    
    assert isinstance(test_logger, logging.Logger)
    assert len(test_logger.handlers) > 0
    
    # Check for RotatingFileHandler
    has_rotating_handler = any(isinstance(h, logging.handlers.RotatingFileHandler) for h in test_logger.handlers)
    assert has_rotating_handler, "RotatingFileHandler not found in logger handlers"
    
    # Check for StreamHandler
    has_stream_handler = any(isinstance(h, logging.StreamHandler) for h in test_logger.handlers)
    assert has_stream_handler, "StreamHandler not found in logger handlers"


def test_custom_log_levels_exist():
    """Test that custom log levels are defined."""
    assert hasattr(logging_module.logging, "INFO_MODE_SWITCH")
    assert hasattr(logging_module.logging, "RESOURCE_USAGE")
    assert logging_module.logging.INFO_MODE_SWITCH > logging.INFO
    assert logging_module.logging.RESOURCE_USAGE > logging.WARNING


def test_log_mode_switch():
    """Test that log_mode_switch logs the correct message."""
    # Create a temporary directory for logs to avoid writing to project logs during test
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Patch the LOG_FILE path
        original_log_file = logging_module.LOG_FILE
        logging_module.LOG_FILE = tmp_path / "test.log"
        
        try:
            # Re-initialize logger to pick up new path
            test_logger = logging_module.get_logger("test_mode_switch")
            # Clear handlers to force re-addition with new path
            test_logger.handlers.clear()
            test_logger.setLevel(logging.DEBUG)
            
            # Re-add handlers manually for the test path
            formatter = logging.Formatter("%(message)s")
            file_handler = logging.handlers.RotatingFileHandler(
                logging_module.LOG_FILE, maxBytes=1024, backupCount=1
            )
            file_handler.setFormatter(formatter)
            test_logger.addHandler(file_handler)
            
            # Call the function
            logging_module.log_mode_switch(test_logger, "Data Insufficient", "No dataset found")
            
            # Flush handlers
            test_logger.handlers[0].flush()
            
            # Verify log content
            log_file_path = logging_module.LOG_FILE
            assert log_file_path.exists()
            
            with open(log_file_path, "r") as f:
                content = f.read()
            
            assert "MODE SWITCH" in content
            assert "Data Insufficient" in content
            assert "No dataset found" in content
        finally:
            logging_module.LOG_FILE = original_log_file


def test_log_resource_usage():
    """Test that log_resource_usage logs resource metrics."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        original_log_file = logging_module.LOG_FILE
        logging_module.LOG_FILE = tmp_path / "test.log"
        
        try:
            test_logger = logging_module.get_logger("test_resource")
            test_logger.handlers.clear()
            test_logger.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter("%(message)s")
            file_handler = logging.handlers.RotatingFileHandler(
                logging_module.LOG_FILE, maxBytes=1024, backupCount=1
            )
            file_handler.setFormatter(formatter)
            test_logger.addHandler(file_handler)
            
            # Test normal usage
            logging_module.log_resource_usage(test_logger, "RAM", "4.5GB")
            test_logger.handlers[0].flush()
            
            with open(logging_module.LOG_FILE, "r") as f:
                content = f.read()
            
            assert "RESOURCE USAGE" in content
            assert "RAM" in content
            assert "4.5GB" in content
        finally:
            logging_module.LOG_FILE = original_log_file