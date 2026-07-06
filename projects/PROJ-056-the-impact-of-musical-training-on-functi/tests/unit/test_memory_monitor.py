"""
Unit tests for the memory monitoring utilities.

These tests verify that the memory monitor correctly detects when
memory usage exceeds the configured limit and raises MemoryLimitExceeded.
"""

import pytest
from unittest.mock import patch
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.memory_monitor import (
    MemoryLimitExceeded,
    get_current_memory_mb,
    check_memory_limit,
    enforce_memory_limit,
    simulate_large_memory_usage
)


class TestMemoryLimitExceeded:
    """Tests for the MemoryLimitExceeded exception."""
    
    def test_exception_inherits_from_exception(self):
        """Verify that MemoryLimitExceeded is a subclass of Exception."""
        assert issubclass(MemoryLimitExceeded, Exception)
    
    def test_exception_message(self):
        """Verify that the exception carries a meaningful message."""
        with pytest.raises(MemoryLimitExceeded) as exc_info:
            raise MemoryLimitExceeded("Test message")
        
        assert "Test message" in str(exc_info.value)


class TestGetCurrentMemoryMb:
    """Tests for get_current_memory_mb function."""
    
    def test_returns_positive_float(self):
        """Verify that get_current_memory_mb returns a positive float."""
        memory_mb = get_current_memory_mb()
        assert isinstance(memory_mb, float)
        assert memory_mb >= 0


class TestCheckMemoryLimit:
    """Tests for check_memory_limit function."""
    
    @patch('utils.memory_monitor.get_current_memory_mb')
    def test_within_limit_returns_true(self, mock_get_memory):
        """Verify that check_memory_limit returns True when under limit."""
        mock_get_memory.return_value = 1000.0  # 1000 MB
        
        result = check_memory_limit(limit_gb=7.0, raise_on_exceed=False)
        
        assert result is True
        mock_get_memory.assert_called_once()
    
    @patch('utils.memory_monitor.get_current_memory_mb')
    def test_exceeds_limit_raises_exception(self, mock_get_memory):
        """Verify that check_memory_limit raises MemoryLimitExceeded when over limit."""
        mock_get_memory.return_value = 8000.0  # 8000 MB > 7GB
        
        with pytest.raises(MemoryLimitExceeded) as exc_info:
            check_memory_limit(limit_gb=7.0, raise_on_exceed=True)
        
        assert "Memory limit exceeded" in str(exc_info.value)
        mock_get_memory.assert_called_once()
    
    @patch('utils.memory_monitor.get_current_memory_mb')
    def test_exceeds_limit_returns_false_when_not_raising(self, mock_get_memory):
        """Verify that check_memory_limit returns False when over limit and raise_on_exceed=False."""
        mock_get_memory.return_value = 8000.0  # 8000 MB > 7GB
        
        result = check_memory_limit(limit_gb=7.0, raise_on_exceed=False)
        
        assert result is False
        mock_get_memory.assert_called_once()
    
    @patch('utils.memory_monitor.get_current_memory_mb')
    def test_custom_limit(self, mock_get_memory):
        """Verify that check_memory_limit respects custom limits."""
        mock_get_memory.return_value = 1500.0  # 1500 MB
        
        # Should pass with 2GB limit
        result = check_memory_limit(limit_gb=2.0, raise_on_exceed=False)
        assert result is True
        
        # Should fail with 1GB limit
        with pytest.raises(MemoryLimitExceeded):
            check_memory_limit(limit_gb=1.0, raise_on_exceed=True)
    
    @patch('utils.memory_monitor.get_current_memory_mb')
    def test_exactly_at_limit(self, mock_get_memory):
        """Verify behavior when memory is exactly at the limit."""
        limit_gb = 7.0
        limit_mb = limit_gb * 1024.0
        mock_get_memory.return_value = limit_mb
        
        # Should pass when exactly at limit
        result = check_memory_limit(limit_gb=limit_gb, raise_on_exceed=False)
        assert result is True
        
        # Should fail when slightly over limit
        mock_get_memory.return_value = limit_mb + 1
        with pytest.raises(MemoryLimitExceeded):
            check_memory_limit(limit_gb=limit_gb, raise_on_exceed=True)

class TestEnforceMemoryLimit:
    """Tests for enforce_memory_limit function."""
    
    @patch('utils.memory_monitor.get_current_memory_mb')
    def test_enforce_raises_on_exceed(self, mock_get_memory):
        """Verify that enforce_memory_limit raises exception when over limit."""
        mock_get_memory.return_value = 8000.0  # 8000 MB > 7GB
        
        with pytest.raises(MemoryLimitExceeded):
            enforce_memory_limit(limit_gb=7.0)
    
    @patch('utils.memory_monitor.get_current_memory_mb')
    def test_enforce_does_not_raise_under_limit(self, mock_get_memory):
        """Verify that enforce_memory_limit does not raise when under limit."""
        mock_get_memory.return_value = 1000.0  # 1000 MB < 7GB
        
        # Should not raise
        enforce_memory_limit(limit_gb=7.0)

class TestMockDatasetMemoryExceed:
    """Tests simulating a mock dataset that exceeds 7GB memory limit."""
    
    @patch('utils.memory_monitor.get_current_memory_mb')
    def test_mock_dataset_exceeds_limit(self, mock_get_memory):
        """
        Simulate a mock dataset > 7GB and verify that MemoryLimitExceeded is raised.
        
        This test uses monkeypatching to simulate a scenario where a large dataset
        would cause memory usage to exceed the 7GB limit.
        """
        # Simulate memory usage of a mock dataset > 7GB
        mock_get_memory.return_value = 7500.0  # 7500 MB > 7GB
        
        # Verify that check_memory_limit raises the exception
        with pytest.raises(MemoryLimitExceeded) as exc_info:
            check_memory_limit(limit_gb=7.0, raise_on_exceed=True)
        
        # Verify the error message contains relevant information
        assert "Memory limit exceeded" in str(exc_info.value)
        assert "7500.00" in str(exc_info.value)
        assert "7168.00" in str(exc_info.value)  # 7 * 1024
    
    @patch('utils.memory_monitor.get_current_memory_mb')
    def test_multiple_datasets_cumulative_exceed(self, mock_get_memory):
        """
        Simulate multiple mock datasets that cumulatively exceed 7GB.
        
        This test verifies that the memory monitor can detect when
        cumulative memory usage from multiple data sources exceeds the limit.
        """
        # Simulate cumulative memory usage
        mock_get_memory.return_value = 8500.0  # 8500 MB > 7GB
        
        # First check should fail
        with pytest.raises(MemoryLimitExceeded):
            check_memory_limit(limit_gb=7.0, raise_on_exceed=True)
        
        # Verify the exception message
        with pytest.raises(MemoryLimitExceeded) as exc_info:
            check_memory_limit(limit_gb=7.0, raise_on_exceed=True)
        
        assert "Memory limit exceeded" in str(exc_info.value)