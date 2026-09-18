import os
import logging
import pytest
from pathlib import Path
import tempfile
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import LOGS_DIR
from logging_config import setup_logger, get_logger, DetailedFormatter

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logs during testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_log_dir = LOGS_DIR
        # Mock the LOGS_DIR path temporarily
        import config
        config.LOGS_DIR = Path(tmpdir)
        yield Path(tmpdir)
        config.LOGS_DIR = original_log_dir

def test_setup_logger_creates_file_handler(temp_log_dir):
    """Test that setup_logger creates a file handler."""
    logger = setup_logger("test_logger")
    
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) > 0, "Logger should have a file handler"
    
    # Check if log file exists
    log_file = temp_log_dir / "pipeline.log"
    assert log_file.exists(), "Log file should be created"

def test_setup_logger_creates_console_handler(temp_log_dir):
    """Test that setup_logger creates a console handler."""
    logger = setup_logger("test_logger_2")
    
    console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(console_handlers) > 0, "Logger should have a console handler"

def test_get_logger_reuses_existing(temp_log_dir):
    """Test that get_logger returns the same instance if already configured."""
    logger1 = setup_logger("test_reuse")
    logger2 = get_logger("test_reuse")
    
    assert logger1 is logger2, "get_logger should return the same instance"
    assert len(logger1.handlers) == len(logger2.handlers), "Handler count should match"

def test_detailed_formatter_includes_level(temp_log_dir):
    """Test that the detailed formatter includes log level."""
    logger = setup_logger("test_formatter")
    
    # Log a message
    logger.info("Test message")
    
    # Read the log file
    log_file = temp_log_dir / "pipeline.log"
    with open(log_file, 'r') as f:
        content = f.read()
    
    assert "INFO" in content, "Log file should contain 'INFO' level"
    assert "Test message" in content, "Log file should contain the message"

def test_logger_level_respected(temp_log_dir):
    """Test that the logger respects the configured level."""
    # Set up a logger with WARNING level
    logger = setup_logger("test_level", level=logging.WARNING)
    
    # Log messages at different levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    
    # Read the log file
    log_file = temp_log_dir / "pipeline.log"
    with open(log_file, 'r') as f:
        content = f.read()
    
    assert "Debug message" not in content, "Debug messages should not be logged"
    assert "Info message" not in content, "Info messages should not be logged"
    assert "Warning message" in content, "Warning messages should be logged"
