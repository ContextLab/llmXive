"""
Tests for the logging infrastructure.
"""
import logging
import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.logger import setup_logger

def test_setup_logger_creates_file():
    """Test that setup_logger creates the log directory and file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_file = Path(tmp_dir) / "test.log"
        
        # Call setup_logger with custom path
        returned_path = setup_logger(
            name="test_logger_unit",
            log_file=log_file
        )
        
        # Verify returned path matches
        assert returned_path == log_file
        assert log_file.exists(), "Log file was not created"

def test_setup_logger_writes_logs():
    """Test that logs are actually written to the file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_file = Path(tmp_dir) / "test_write.log"
        
        logger_name = "test_logger_write"
        setup_logger(name=logger_name, log_file=log_file)
        
        # Get the logger and write a message
        logger = logging.getLogger(logger_name)
        test_msg = "Test log message for verification"
        logger.info(test_msg)
        
        # Flush handlers to ensure write
        for handler in logger.handlers:
            handler.flush()
        
        # Read file content
        content = log_file.read_text()
        assert test_msg in content, f"Log message '{test_msg}' not found in {content}"

def test_setup_logger_console_output():
    """Test that console handler is attached."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_file = Path(tmp_dir) / "test_console.log"
        
        logger_name = "test_logger_console"
        setup_logger(name=logger_name, log_file=log_file)
        
        logger = logging.getLogger(logger_name)
        
        # Check handlers
        assert len(logger.handlers) == 2, "Expected 2 handlers (console and file)"
        
        # Check for StreamHandler (console)
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1, "Console handler not found"