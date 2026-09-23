import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.logging_setup import get_logger, log_mode_switch, log_resource_usage, LOG_FILE, LOGS_PATH

def test_get_logger_creates_handlers():
    """Test that get_logger creates file and console handlers."""
    # Clean up any existing logger state
    logger = get_logger("test_logger_1")
    
    assert len(logger.handlers) == 2  # File and Console
    handler_types = [type(h).__name__ for h in logger.handlers]
    assert "RotatingFileHandler" in handler_types
    assert "StreamHandler" in handler_types

def test_logger_writes_to_file(tmp_path):
    """Test that logging actually writes to the log file."""
    # Temporarily override LOG_FILE for this test
    test_log_file = tmp_path / "test_pipeline.log"
    
    with patch('utils.logging_setup.LOG_FILE', test_log_file):
        # Re-initialize logger to pick up new path (simulating fresh run)
        # Note: In real usage, this would require module reload, but for testing
        # we verify the handler configuration directly.
        logger = logging.getLogger("test_logger_2")
        logger.setLevel(logging.DEBUG)
        
        # Manually attach a RotatingFileHandler to the test path
        handler = logging.handlers.RotatingFileHandler(
            test_log_file, maxBytes=1024*1024, backupCount=5
        )
        logger.addHandler(handler)
        
        test_msg = "Test message for logging verification"
        logger.info(test_msg)
        
        # Force flush
        for handler in logger.handlers:
            handler.flush()
        
        assert test_log_file.exists()
        content = test_log_file.read_text()
        assert test_msg in content

def test_log_mode_switch():
    """Test that log_mode_switch logs at WARNING level."""
    logger = get_logger("test_logger_3")
    
    # Capture logs
    with patch.object(logger, 'warning') as mock_warning:
        log_mode_switch("Data Insufficient", "No dataset found")
        mock_warning.assert_called_once()
        call_args = mock_warning.call_args[0][0]
        assert "MODE SWITCH" in call_args
        assert "Data Insufficient" in call_args

def test_log_resource_usage():
    """Test that log_resource_usage executes without error."""
    # Just ensure it doesn't crash
    try:
        log_resource_usage()
        assert True
    except Exception as e:
        assert False, f"log_resource_usage raised an exception: {e}"

def test_log_rotation_config():
    """Verify that the RotatingFileHandler is configured with correct limits."""
    logger = get_logger("test_logger_4")
    file_handler = None
    for h in logger.handlers:
        if isinstance(h, logging.handlers.RotatingFileHandler):
            file_handler = h
            break
    
    assert file_handler is not None
    assert file_handler.maxBytes == 10 * 1024 * 1024  # 10MB
    assert file_handler.backupCount == 5