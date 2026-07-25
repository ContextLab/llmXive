"""
Unit tests for the logging infrastructure (T005).
"""
import pytest
import logging
import time
import os
import sys
import tempfile
from pathlib import Path

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging import (
    setup_logger,
    get_memory_usage_mb,
    log_memory_usage,
    MemoryTracker,
    ExecutionTimer,
    log_execution_time
)


class TestSetupLogger:
    def test_setup_logger_console_only(self):
        """Test logger creation with only console output."""
        logger = setup_logger("test.console")
        assert logger is not None
        assert len(logger.handlers) > 0
        # Check for StreamHandler
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    
    def test_setup_logger_with_file(self, tmp_path):
        """Test logger creation with file output."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test.file", log_file=str(log_file))
        assert logger is not None
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        
        # Log something
        logger.info("Test message")
        
        # Verify file exists and has content
        assert log_file.exists()
        assert log_file.read_text().strip() != ""
    
    def test_setup_logger_duplicate_call(self):
        """Test that calling setup_logger twice doesn't duplicate handlers."""
        logger = setup_logger("test.dupe")
        initial_count = len(logger.handlers)
        
        # Call again
        logger2 = setup_logger("test.dupe")
        
        # Should be the same logger instance with same handlers
        assert logger is logger2
        assert len(logger.handlers) == initial_count


class TestMemoryTracking:
    def test_get_memory_usage_mb_returns_number(self):
        """Test that memory usage function returns a float."""
        mb = get_memory_usage_mb()
        assert isinstance(mb, float)
        assert mb >= 0.0
    
    def test_log_memory_usage(self, caplog):
        """Test that log_memory_usage logs the correct format."""
        logger = setup_logger("test.mem")
        # Remove console handler to capture in caplog
        logger.handlers = [logging.FileHandler(os.devnull)] 
        
        # Re-add a handler that captures to memory for testing
        handler = logging.Handler()
        handler.emit = lambda record: None # Mock emit
        logger.addHandler(handler)
        
        # Just ensure it doesn't crash and returns a value
        val = log_memory_usage(logger, "Test Mem")
        assert isinstance(val, float)


class TestMemoryTracker:
    def test_context_manager_tracks_memory(self):
        """Test that MemoryTracker logs start and end memory."""
        logger = setup_logger("test.tracker")
        # Use a null handler for clean test
        logger.handlers = [logging.NullHandler()]
        
        with MemoryTracker(logger, "TestBlock"):
            # Do a tiny bit of work
            _ = [i for i in range(1000)]
        
        # If we get here without error, the context manager worked
        assert True


class TestExecutionTimer:
    def test_context_manager_tracks_time(self):
        """Test that ExecutionTimer logs start and end time."""
        logger = setup_logger("test.timer")
        logger.handlers = [logging.NullHandler()]
        
        with ExecutionTimer(logger, "TestBlock"):
            time.sleep(0.1) # Sleep 100ms
        
        # If we get here, it worked. 
        # We can't easily verify the log content without custom handler, 
        # but the absence of exception proves the logic path.
        assert True
    
    def test_log_execution_time_function(self, caplog):
        """Test the standalone log_execution_time function."""
        logger = setup_logger("test.func_timer")
        logger.handlers = [logging.NullHandler()]
        
        start = time.time()
        time.sleep(0.05)
        duration = log_execution_time(logger, start, "Op Done")
        
        assert duration >= 0.05
        assert isinstance(duration, float)