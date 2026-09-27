import os
import sys
import logging
import pytest
from pathlib import Path
import shutil

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.logging_setup import (
    get_logger,
    log_mode_switch,
    log_resource_usage,
    LOG_DIR,
    LOG_FILE
)

@pytest.fixture(autouse=True)
def setup_logging_env():
    """Setup and teardown for logging tests."""
    # Create logs dir if not exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup handlers to avoid interference between tests
    logger = logging.getLogger("llmXive")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    # Optional: clean up log file after tests if desired
    # if LOG_FILE.exists():
    #     LOG_FILE.unlink()

def test_get_logger_creates_instance():
    """Test that get_logger returns a valid logger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"
    # Verify handlers are attached (stdout + file)
    assert len(logger.handlers) >= 1

def test_get_logger_singleton_behavior():
    """Test that calling get_logger returns the same configured instance."""
    logger1 = get_logger("llmXive")
    logger2 = get_logger("llmXive")
    assert logger1 is logger2
    # Should not have duplicated handlers
    initial_handler_count = len(logger1.handlers)
    logger3 = get_logger("llmXive")
    assert len(logger3.handlers) == initial_handler_count

def test_log_mode_switch():
    """Test that log_mode_switch writes to the logger."""
    logger = get_logger("ModeController")
    # Capture logs in memory to verify
    import io
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)

    log_mode_switch("Underpowered", "Sample size too small")

    log_contents = log_stream.getvalue()
    assert "MODE SWITCH" in log_contents
    assert "Underpowered" in log_contents
    assert "Sample size too small" in log_contents

def test_log_resource_usage():
    """Test that log_resource_usage executes without crashing."""
    # This test mainly ensures the function doesn't raise exceptions
    # Actual resource values depend on the environment
    log_resource_usage()
    # If we reach here, the function succeeded

def test_log_file_creation():
    """Test that the log file is created when logging occurs."""
    logger = get_logger("test_file_creation")
    logger.info("Test message for file creation")
    
    # Force flush to ensure file is written
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()

    assert LOG_FILE.exists(), "Log file should be created after logging"
    assert LOG_FILE.stat().st_size > 0, "Log file should contain data"

def test_log_levels():
    """Test that different log levels are handled correctly."""
    logger = get_logger("test_levels")
    
    # Verify handlers accept specific levels
    file_handler = [h for h in logger.handlers if isinstance(h, logging.FileHandler)][0]
    assert file_handler.level == logging.DEBUG
    
    console_handler = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)][0]
    assert console_handler.level == logging.INFO

def test_rotating_handler_config():
    """Test that the rotating file handler is configured correctly."""
    logger = get_logger("test_rotating")
    file_handler = [h for h in logger.handlers if isinstance(h, logging.FileHandler)][0]
    
    # Check if it's a RotatingFileHandler
    from logging.handlers import RotatingFileHandler
    assert isinstance(file_handler, RotatingFileHandler)
    
    # Check max bytes (10MB)
    assert file_handler.maxBytes == 10 * 1024 * 1024
    # Check backup count
    assert file_handler.backupCount == 5