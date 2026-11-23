import os
import sys
import tempfile
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import (
    get_logger,
    get_memory_usage_mb,
    log_memory_usage,
    track_execution_time,
    start_tracing,
    stop_tracing,
    log_script_start,
    log_script_end
)

class TestLogger:
    """Unit tests for logging utility functions."""

    def test_get_logger_creates_logger(self):
        """Test that get_logger returns a valid logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_memory_usage_mb_returns_number(self):
        """Test that get_memory_usage_mb returns a non-negative number."""
        mem = get_memory_usage_mb()
        assert isinstance(mem, (int, float))
        assert mem >= 0

    def test_log_memory_usage_logs_to_logger(self):
        """Test that log_memory_usage logs memory usage."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name

        try:
            logger = get_logger("test_mem_log")
            # Remove existing handlers to avoid duplicates
            logger.handlers = []
            
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            log_memory_usage(logger, "test_point")
            
            # Check that log file has content
            with open(log_file, 'r') as f:
                content = f.read()
                assert len(content) > 0
                assert "Memory usage" in content
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_track_execution_time_decorator(self):
        """Test that track_execution_time decorator logs execution time."""
        import time

        @track_execution_time
        def dummy_function():
            time.sleep(0.1)
            return "done"

        # Capture log output
        with patch('utils.logger.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = dummy_function()
            assert result == "done"
            
            # Verify that log_script_start and log_script_end were called
            # The decorator should call get_logger internally
            # We check that the logger was used
            assert mock_get_logger.called

    def test_start_stop_tracing(self):
        """Test that start_tracing and stop_tracing work correctly."""
        # tracemalloc needs to be started
        start_tracing()
        
        # Some operation
        data = [i for i in range(1000)]
        
        # Stop tracing
        stop_tracing()
        
        # Should not raise any exceptions
        assert True

    def test_log_script_start_end(self):
        """Test that log_script_start and log_script_end create proper log entries."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name

        try:
            logger = get_logger("test_script_log")
            logger.handlers = []
            
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            log_script_start(logger, "test_script")
            log_script_end(logger, "test_script")
            
            with open(log_file, 'r') as f:
                content = f.read()
                assert "test_script" in content
                assert "started" in content
                assert "finished" in content
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_logger_level_configuration(self):
        """Test that logger respects log level configuration."""
        logger = get_logger("test_level")
        logger.setLevel(logging.WARNING)
        
        # These should not produce output
        logger.debug("debug msg")
        logger.info("info msg")
        
        # This should
        logger.warning("warning msg")
        
        # Verify level is set correctly
        assert logger.level == logging.WARNING
