import os
import sys
import logging
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logger import setup_logger, get_pipeline_logger, log_info, log_error
from code.utils.error_handling import handle_error, PipelineError

def test_logger_initialization():
    """Test that the logger initializes correctly."""
    logger = setup_logger("test_logger", level=logging.INFO)
    assert logger is not None
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO

def test_logger_file_handler():
    """Test that the logger writes to a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        logger = setup_logger("test_file_logger", level=logging.INFO, log_file=str(log_file))
        
        # Log a message
        logger.info("Test message")
        
        # Check if file exists and contains the message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

def test_get_pipeline_logger():
    """Test that get_pipeline_logger returns the initialized logger."""
    # First, ensure it's initialized
    setup_logger("pipeline_test", level=logging.DEBUG)
    logger = get_pipeline_logger("pipeline_test")
    assert logger is not None
    assert logger.level == logging.DEBUG

def test_log_info():
    """Test the log_info helper function."""
    logger = setup_logger("info_test", level=logging.INFO)
    # This should not raise
    log_info("Info message test")

def test_error_handling():
    """Test the error handling utilities."""
    try:
        raise ValueError("Test error")
    except Exception as e:
        # Should not raise because reraise=False
        handle_error(e, "Test Context", reraise=False)
        
        # Should raise because reraise=True
        try:
            handle_error(e, "Test Context", reraise=True)
        except ValueError:
            pass  # Expected

def test_logger_write_and_read_entry():
    """
    Test that a log entry can be written and read back.
    This satisfies the requirement to write and read a log entry.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "entry_test.log"
        logger = setup_logger("entry_logger", level=logging.INFO, log_file=str(log_file))
        
        test_message = "Verification entry for T005"
        logger.info(test_message)
        
        # Read back the file
        assert log_file.exists(), "Log file was not created"
        content = log_file.read_text()
        
        # Verify the message is present
        assert test_message in content, f"Message '{test_message}' not found in log file"
        
        # Verify standard log format components are present
        assert "INFO" in content, "Log level INFO not found"
        assert "entry_logger" in content, "Logger name not found"