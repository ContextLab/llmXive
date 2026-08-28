"""
Unit tests for memory monitoring utility.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

# Adjust path to import from code/utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.monitor import (
    get_memory_usage_mb,
    check_memory_limit,
    log_memory_snapshot,
    setup_logger,
    MemoryLimitException
)

class TestMemoryMonitoring:
    def test_get_memory_usage_mb_returns_positive_float(self):
        """Test that memory usage is returned as a positive float."""
        # Mock /proc/self/status to return a known VmRSS value
        mock_status_content = """
        Name:   python
        Umask:  0022
        State:  S (sleeping)
        ...
        VmRSS:      12345 kB
        ...
        """
        with patch('builtins.open', mock_open(read_data=mock_status_content)):
            with patch('os.path.exists', return_value=True):
                mem = get_memory_usage_mb()
                assert isinstance(mem, float)
                # 12345 kB = ~12.05 MB
                assert 12.0 < mem < 12.1

    def test_get_memory_usage_mb_raises_on_missing_file(self):
        """Test that get_memory_usage_mb raises OSError if /proc/self/status is missing."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(OSError):
                get_memory_usage_mb()

    def test_check_memory_limit_passes_when_under_limit(self):
        """Test that check_memory_limit returns value when under limit."""
        # Mock memory usage to be 100 MB
        with patch('utils.monitor.get_memory_usage_mb', return_value=100.0):
            limit = 1000000.0  # 1TB
            current = check_memory_limit(limit_mb=limit)
            assert current == 100.0

    def test_check_memory_limit_raises_when_over_limit(self):
        """Test that check_memory_limit raises MemoryLimitException when over limit."""
        # Mock memory usage to be 1000 MB
        with patch('utils.monitor.get_memory_usage_mb', return_value=1000.0):
            limit = 500.0  # 500 MB limit
            with pytest.raises(MemoryLimitException) as exc_info:
                check_memory_limit(limit_mb=limit)
            
            assert "Memory limit exceeded" in str(exc_info.value)
            assert "1000.0" in str(exc_info.value)
            assert "500.0" in str(exc_info.value)

    def test_log_memory_snapshot_returns_float(self):
        """Test that log_memory_snapshot returns a float."""
        mock_status_content = """
        Name:   python
        VmRSS:      50000 kB
        """
        with patch('builtins.open', mock_open(read_data=mock_status_content)):
            with patch('os.path.exists', return_value=True):
                result = log_memory_snapshot("Test Snapshot")
                assert isinstance(result, float)
                # 50000 kB = ~48.8 MB
                assert 48.0 < result < 49.0

    def test_setup_logger_creates_file_handler(self, tmp_path):
        """Test that setup_logger creates a file handler when log_file is provided."""
        log_file = tmp_path / "test.log"
        logger = setup_logger('test_logger_unique', str(log_file), level=logging.INFO)
        
        assert len(logger.handlers) > 0
        # Check if at least one handler is a FileHandler
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0
        assert file_handlers[0].baseFilename == str(log_file)

    def test_setup_logger_avoids_duplicates(self):
        """Test that setup_logger does not add duplicate handlers."""
        logger_name = 'duplicate_test_unique'
        logger = setup_logger(logger_name, None, level=logging.INFO)
        initial_count = len(logger.handlers)
        
        # Call again
        logger_again = setup_logger(logger_name, None, level=logging.INFO)
        
        # Should return the same logger with same number of handlers
        assert len(logger_again.handlers) == initial_count

    def test_memory_limit_exception_message(self):
        """Test that MemoryLimitException includes current and limit in message."""
        with patch('utils.monitor.get_memory_usage_mb', return_value=2048.0):
            try:
                check_memory_limit(limit_mb=1024.0)
                assert False, "Expected MemoryLimitException"
            except MemoryLimitException as e:
                assert "2048.0" in str(e)
                assert "1024.0" in str(e)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])