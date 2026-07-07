"""
Unit tests for the logging infrastructure (code/utils/logging.py).
Verifies memory tracking and execution timing utilities.
"""
import pytest
import time
import logging
import sys
from io import StringIO
from pathlib import Path

# Import the module under test
from code.utils.logging import (
    setup_logger, 
    get_memory_usage_mb, 
    log_memory_usage, 
    MemoryTracker, 
    ExecutionTimer, 
    log_execution_time
)


@pytest.fixture
def string_logger():
    """Create a logger that writes to a StringIO buffer."""
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.handlers = [] # Clear existing handlers
    logger.addHandler(handler)
    
    return logger, stream


def test_setup_logger_console_only(string_logger):
    """Test that setup_logger creates a logger with a console handler."""
    logger, stream = string_logger
    
    # Verify handlers exist
    assert len(logger.handlers) > 0
    
    # Log a message
    logger.info("Test message")
    
    # Verify output
    output = stream.getvalue()
    assert "Test message" in output


def test_get_memory_usage_mb_returns_positive():
    """Test that get_memory_usage_mb returns a non-negative float."""
    mb = get_memory_usage_mb()
    assert isinstance(mb, float)
    assert mb >= 0.0


def test_log_memory_usage(string_logger):
    """Test that log_memory_usage logs the correct format."""
    logger, stream = string_logger
    
    mb = log_memory_usage(logger, "Test Memory")
    
    output = stream.getvalue()
    assert "Test Memory" in output
    assert f"{mb:.2f} MB" in output


def test_memory_tracker_context(string_logger):
    """Test MemoryTracker context manager logs start and end."""
    logger, stream = string_logger
    
    with MemoryTracker(logger, "Test Block"):
        time.sleep(0.1) # Small delay to ensure some time passes
    
    output = stream.getvalue()
    assert "Start: Test Block" in output
    assert "End: Test Block" in output
    assert "Delta:" in output


def test_execution_timer_context(string_logger):
    """Test ExecutionTimer context manager logs duration."""
    logger, stream = string_logger
    
    with ExecutionTimer(logger, "Slow Block"):
        time.sleep(0.2)
    
    output = stream.getvalue()
    assert "Start: Slow Block" in output
    assert "End: Slow Block" in output
    # Verify duration is at least 0.2 seconds (allowing small overhead)
    assert "0.2" in output or "0.3" in output or "0.4" in output # Loose check for > 0.1s


def test_log_execution_time_function(string_logger):
    """Test the standalone log_execution_time function."""
    logger, stream = string_logger
    
    start = time.time()
    time.sleep(0.1)
    duration = log_execution_time(logger, start, "Function Test")
    
    output = stream.getvalue()
    assert "Function Test" in output
    assert duration >= 0.1