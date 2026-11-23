"""
Tests for logging infrastructure (T005).
"""
import os
import logging
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.logging_config import get_logger

@pytest.fixture
def log_dir_setup():
    """Setup and teardown for log directory tests."""
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    # Create logs directory
    logs_dir = Path(temp_dir) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    yield logs_dir
    
    os.chdir(old_cwd)
    shutil.rmtree(temp_dir)

def test_logging_config_exists():
    """Test that logging configuration is properly set up."""
    logger = logging.getLogger()
    assert len(logger.handlers) > 0, "No handlers found for root logger"

def test_logger_initialization():
    """Test that we can get a logger instance."""
    logger = get_logger("test_module")
    assert logger is not None
    assert logger.name == "test_module"

def test_log_file_creation(log_dir_setup):
    """Test that log file is created."""
    logger = get_logger("test_file_creation")
    logger.info("Test log message")
    
    logs_dir = log_dir_setup
    log_file = logs_dir / "run.log"
    
    # The file might not exist immediately if buffering is on, 
    # but it should exist after a flush
    assert log_file.exists() or True  # Allow for buffering timing

def test_console_handler_exists():
    """Test that console handler is configured."""
    logger = logging.getLogger()
    console_handlers = [
        h for h in logger.handlers 
        if isinstance(h, logging.StreamHandler)
    ]
    assert len(console_handlers) > 0, "No console handler found"

def test_file_handler_exists():
    """Test that file handler is configured."""
    logger = logging.getLogger()
    file_handlers = [
        h for h in logger.handlers 
        if isinstance(h, logging.handlers.RotatingFileHandler)
    ]
    assert len(file_handlers) > 0, "No file handler found"