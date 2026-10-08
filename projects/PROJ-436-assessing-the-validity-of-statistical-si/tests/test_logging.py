"""
Unit tests for logging infrastructure in code/__init__.py
"""
import os
import logging
import tempfile
import pytest
import sys
from io import StringIO

# Import the function under test
from code import setup_logging

def test_setup_logging_console_only():
    """Test that setup_logging configures console handler correctly."""
    # Capture stdout
    log_capture = StringIO()
    original_stdout = sys.stdout
    sys.stdout = log_capture

    try:
        logger = setup_logging(level=logging.INFO, log_file=None)
        
        # Verify root logger level
        assert logger.level == logging.INFO
        
        # Verify handler count
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        
        # Test logging
        logger.info("Test message")
        
        # Restore stdout and check output
        sys.stdout = original_stdout
        output = log_capture.getvalue()
        assert "Test message" in output
        assert "INFO" in output
    finally:
        sys.stdout = original_stdout

def test_setup_logging_with_file():
    """Test that setup_logging creates a file handler when log_file is provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        
        logger = setup_logging(level=logging.DEBUG, log_file=log_path)
        
        # Verify handler count (console + file)
        assert len(logger.handlers) == 2
        
        # Verify file handler exists
        file_handler = next((h for h in logger.handlers if isinstance(h, logging.FileHandler)), None)
        assert file_handler is not None
        assert file_handler.baseFilename == log_path
        
        # Log a message
        logger.debug("Debug message for file")
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Check file content
        assert os.path.exists(log_path)
        with open(log_path, 'r') as f:
            content = f.read()
        assert "Debug message for file" in content
        assert "DEBUG" in content

def test_setup_logging_custom_format():
    """Test that custom format string is applied."""
    custom_format = "[CUSTOM] %(levelname)s: %(message)s"
    logger = setup_logging(level=logging.WARNING, format_str=custom_format)
    
    # Verify handler formatter
    assert logger.handlers[0].formatter._fmt == custom_format

def test_setup_logging_clears_handlers():
    """Test that setup_logging clears existing handlers to avoid duplicates."""
    # Add a dummy handler
    root = logging.getLogger()
    dummy_handler = logging.StreamHandler()
    root.addHandler(dummy_handler)
    
    # Run setup_logging
    logger = setup_logging(level=logging.INFO)
    
    # The dummy handler should be gone
    assert dummy_handler not in logger.handlers
    # Only the new handlers should remain
    assert len(logger.handlers) >= 1

def test_setup_logging_directory_creation():
    """Test that setup_logging creates directories for log file if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_path = os.path.join(tmpdir, "subdir", "nested", "app.log")
        
        # This should not raise an error even if subdir/nested doesn't exist
        logger = setup_logging(level=logging.INFO, log_file=nested_path)
        
        assert os.path.exists(nested_path)
