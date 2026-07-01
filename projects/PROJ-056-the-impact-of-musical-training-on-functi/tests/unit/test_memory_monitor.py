"""
Unit tests for the memory monitoring functionality.

These tests verify that the memory_monitor module correctly:
1. Tracks current and peak memory usage
2. Enforces the 7GB memory limit
3. Raises MemoryLimitExceeded when limits are exceeded
"""

import pytest
import gc
from unittest.mock import patch, MagicMock

from utils.memory_monitor import (
    get_current_memory_mb,
    get_peak_memory_mb,
    check_memory_limit,
    enforce_memory_limit,
    get_memory_usage_report,
    MemoryLimitExceeded,
    simulate_large_memory_usage,
    cleanup_large_memory
)

class TestMemoryFunctions:
    """Tests for basic memory monitoring functions."""
    
    def test_get_current_memory_mb_returns_positive(self):
        """Current memory usage should be a positive number."""
        current = get_current_memory_mb()
        assert isinstance(current, float)
        assert current >= 0
    
    def test_get_peak_memory_mb_returns_positive(self):
        """Peak memory usage should be a positive number."""
        peak = get_peak_memory_mb()
        assert isinstance(peak, float)
        assert peak >= 0
    
    def test_get_peak_memory_mb_ge_current(self):
        """Peak memory should always be >= current memory."""
        current = get_current_memory_mb()
        peak = get_peak_memory_mb()
        assert peak >= current
    
    def test_get_memory_usage_report_structure(self):
        """Memory usage report should contain all required fields."""
        report = get_memory_usage_report()
        
        expected_keys = [
            "current_mb", "peak_mb", "limit_mb", 
            "limit_gb", "usage_percentage", "status"
        ]
        
        for key in expected_keys:
            assert key in report, f"Missing key: {key}"
        
        assert report["status"] in ["OK", "EXCEEDED"]
        assert isinstance(report["usage_percentage"], float)
        assert report["limit_gb"] == 7.0
        assert report["limit_mb"] == 7.0 * 1024

class TestMemoryLimitEnforcement:
    """Tests for memory limit enforcement functionality."""
    
    def test_check_memory_limit_within_limit_returns_true(self):
        """check_memory_limit should return True when within limit."""
        # Use a very high limit to ensure we're within it
        result = check_memory_limit(limit_gb=100.0, raise_on_exceed=False)
        assert result is True
    
    def test_check_memory_limit_within_limit_no_exception(self):
        """check_memory_limit should not raise when within limit."""
        # This should not raise any exception
        result = check_memory_limit(limit_gb=100.0, raise_on_exceed=True)
        assert result is True
    
    def test_check_memory_limit_exceeds_limit_raises(self):
        """check_memory_limit should raise MemoryLimitExceeded when limit exceeded."""
        # Mock the current memory to be above the limit
        with patch('utils.memory_monitor.get_current_memory_mb', return_value=8000.0):
            with pytest.raises(MemoryLimitExceeded) as exc_info:
                check_memory_limit(limit_gb=7.0, raise_on_exceed=True)
            
            assert "Memory limit exceeded" in str(exc_info.value)
            assert "8000.00 MB" in str(exc_info.value)
    
    def test_check_memory_limit_exceeds_limit_returns_false_when_no_raise(self):
        """check_memory_limit should return False when limit exceeded and raise_on_exceed=False."""
        # Mock the current memory to be above the limit
        with patch('utils.memory_monitor.get_current_memory_mb', return_value=8000.0):
            result = check_memory_limit(limit_gb=7.0, raise_on_exceed=False)
            assert result is False
    
    def test_enforce_memory_limit_within_limit(self):
        """enforce_memory_limit should not raise when within limit."""
        # This should not raise any exception
        enforce_memory_limit(limit_gb=100.0)
    
    def test_enforce_memory_limit_exceeds_limit_raises(self):
        """enforce_memory_limit should raise MemoryLimitExceeded when limit exceeded."""
        # Mock the current memory to be above the limit
        with patch('utils.memory_monitor.get_current_memory_mb', return_value=8000.0):
            with pytest.raises(MemoryLimitExceeded):
                enforce_memory_limit(limit_gb=7.0)
    
    def test_enforce_memory_limit_default_is_7gb(self):
        """enforce_memory_limit should use 7GB as default limit."""
        # Mock current memory to be between 7GB and 8GB to test default
        with patch('utils.memory_monitor.get_current_memory_mb', return_value=7500.0):
            with pytest.raises(MemoryLimitExceeded):
                enforce_memory_limit()  # No limit specified, should default to 7GB

class TestMemoryLimitExceededException:
    """Tests for the MemoryLimitExceeded exception."""
    
    def test_memory_limit_exceeded_is_exception(self):
        """MemoryLimitExceeded should be a subclass of Exception."""
        assert issubclass(MemoryLimitExceeded, Exception)
    
    def test_memory_limit_exceeded_has_message(self):
        """MemoryLimitExceeded should include a descriptive message."""
        try:
            raise MemoryLimitExceeded("Test memory limit exceeded")
        except MemoryLimitExceeded as e:
            assert "Test memory limit exceeded" in str(e)

class TestMemorySimulation:
    """Tests for memory simulation functions (mocked)."""
    
    def test_cleanup_large_memory(self):
        """cleanup_large_memory should successfully clean up data."""
        # Create a small bytearray for testing
        test_data = bytearray(1000)
        
        # Cleanup should not raise
        cleanup_large_memory(test_data)
        
        # Verify the data is cleaned up (garbage collected)
        gc.collect()
    
    def test_memory_report_with_custom_limit(self):
        """get_memory_usage_report should respect custom limit."""
        report = get_memory_usage_report(limit_gb=1.0)
        assert report["limit_gb"] == 1.0
        assert report["limit_mb"] == 1024.0
    
    def test_memory_usage_percentage_calculation(self):
        """Memory usage percentage should be calculated correctly."""
        # Mock current memory to be exactly 50% of 1GB limit
        with patch('utils.memory_monitor.get_current_memory_mb', return_value=512.0):
            report = get_memory_usage_report(limit_gb=1.0)
            # 512 MB / 1024 MB = 50%
            assert abs(report["usage_percentage"] - 50.0) < 0.01
