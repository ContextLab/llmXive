"""
Unit tests for the logger module.
"""
import os
import json
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# We need to test the logger without triggering the global redirect in the main block
# so we import the functions directly.
# To avoid the global redirect in the test environment, we mock the setup.

import logging
import logging.handlers

# Import the module components
# We need to import from code.logger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from code import logger as logger_module

def test_json_formatter_output():
    """Test that the formatter produces valid JSON lines."""
    formatter = logger_module.get_json_formatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message %s",
        args=("arg1",),
        exc_info=None
    )
    formatted = formatter.format(record)
    
    # Verify it's valid JSON
    parsed = json.loads(formatted)
    assert "timestamp" in parsed
    assert "level" in parsed
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message arg1"
    assert parsed["logger"] == "test"

def test_rotating_file_handler_creation():
    """Test that the rotating file handler is created with correct settings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the LOG_DIR
        original_log_dir = logger_module.LOG_DIR
        logger_module.LOG_DIR = tmpdir
        
        try:
            logger = logger_module.setup_logger(name="test_rotator")
            
            # Find the file handler
            file_handler = None
            for h in logger.handlers:
                if isinstance(h, logging.handlers.RotatingFileHandler):
                    file_handler = h
                    break
            
            assert file_handler is not None, "RotatingFileHandler not found"
            assert file_handler.maxBytes == 10 * 1024 * 1024
            assert file_handler.backupCount == 5
        finally:
            logger_module.LOG_DIR = original_log_dir

def test_stdout_redirector_write():
    """Test that the redirector writes to the logger."""
    mock_logger = MagicMock(spec=logging.Logger)
    redirector = logger_module.StdoutRedirector(mock_logger)
    
    redirector.write("Some log message")
    
    mock_logger.log.assert_called_once()
    call_args = mock_logger.log.call_args
    assert call_args[0][1] == "Some log message"

def test_global_logging_configuration():
    """Test that configure_global_logging returns a logger and redirects sys.stdout."""
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    try:
        logger = logger_module.configure_global_logging()
        
        # Verify logger is returned
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmxive"
        
        # Verify stdout was replaced
        assert isinstance(sys.stdout, logger_module.StdoutRedirector)
        assert isinstance(sys.stderr, logger_module.StdoutRedirector)
        
    finally:
        # Restore stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr

def test_exception_logging():
    """Test that exceptions are formatted correctly in JSON."""
    formatter = logger_module.get_json_formatter()
    
    try:
        raise ValueError("Test exception")
    except ValueError:
        import sys
        exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=20,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "Test exception" in parsed["exception"]