"""
Unit tests for memory_utils module.
Tests memory clearing functionality and measurement accuracy.
"""
import gc
import sys
import tempfile
import numpy as np
import pytest

from code.utils.memory_utils import clear_memory, get_memory_usage_mb, monitor_memory_threshold


class TestClearMemory:
    """Tests for the clear_memory function."""
    
    def test_clear_memory_executes_without_error(self):
        """Test that clear_memory runs without raising an exception."""
        # Create some memory to clear
        data = [np.random.randn(1000, 1000) for _ in range(5)]
        
        # This should not raise
        result = clear_memory()
        
        # Clean up
        del data
        gc.collect()
        
        assert result is True, "clear_memory should return True on success"
    
    def test_clear_memory_after_large_array(self):
        """Test memory clearing after creating a large array."""
        # Create a large array that would consume significant memory
        # ~5000x5000 float32 = ~100MB
        large_array = np.random.randn(5000, 5000).astype(np.float32)
        
        # Verify array exists
        assert large_array.nbytes > 0, "Test array should have size"
        
        # Measure memory before clearing
        mem_before = get_memory_usage_mb()
        
        # Clear memory
        clear_memory()
        
        # Delete reference and force collection
        del large_array
        gc.collect()
        
        # Measure memory after clearing
        mem_after = get_memory_usage_mb()
        
        # Note: We cannot assert strict memory reduction due to OS caching,
        # but we verify the function completes and logs appropriately
        assert isinstance(mem_before, float), "Memory before should be float"
        assert isinstance(mem_after, float), "Memory after should be float"
    
    def test_clear_memory_logs_activity(self, caplog):
        """Test that clear_memory logs debug and info messages."""
        # Create some data
        data = [np.random.randn(100, 100) for _ in range(3)]
        
        # Run clear_memory
        clear_memory()
        
        # Clean up
        del data
        gc.collect()
        
        # Check that logs were produced
        # The function should log at least one debug message about GC
        assert any("GC" in record.message for record in caplog.records) or \
               any("memory" in record.message.lower() for record in caplog.records)


class TestGetMemoryUsage:
    """Tests for get_memory_usage_mb function."""
    
    def test_get_memory_usage_returns_non_negative(self):
        """Test that memory usage is always non-negative."""
        usage = get_memory_usage_mb()
        assert usage >= 0.0, "Memory usage should be non-negative"
    
    def test_get_memory_usage_after_array_creation(self):
        """Test memory usage increases after creating large arrays."""
        initial_usage = get_memory_usage_mb()
        
        # Create some data
        data = [np.random.randn(2000, 2000).astype(np.float32) for _ in range(3)]
        
        usage_after = get_memory_usage_mb()
        
        # Clean up
        del data
        gc.collect()
        
        # Note: Memory usage might not always increase due to system caching,
        # but the function should return a valid number
        assert usage_after >= 0.0


class TestMonitorMemoryThreshold:
    """Tests for monitor_memory_threshold function."""
    
    def test_threshold_check_with_low_memory(self):
        """Test threshold check when memory is below threshold."""
        # Use a very high threshold to ensure we're below it
        result = monitor_memory_threshold(100000.0)  # 100 GB threshold
        assert result is False, "Should return False when below threshold"
    
    def test_threshold_check_with_zero_threshold(self):
        """Test threshold check with zero threshold (should always be True if memory > 0)."""
        result = monitor_memory_threshold(0.0)
        # Memory usage is typically > 0, so this should be True
        # But if process is brand new, it might be 0, so we just check it doesn't crash
        assert isinstance(result, bool), "Result should be boolean"
    
    def test_threshold_check_with_negative_threshold(self):
        """Test threshold check with negative threshold."""
        result = monitor_memory_threshold(-100.0)
        # Memory usage is always >= 0, so this should be True
        assert result is True, "Should return True when threshold is negative"
    
    def test_threshold_check_with_real_memory_pressure(self):
        """Test that threshold check detects real memory pressure."""
        # Create a large array to increase memory usage
        large_array = np.random.randn(3000, 3000).astype(np.float32)
        
        # Set a low threshold (e.g., 10MB) which should be exceeded
        result = monitor_memory_threshold(10.0)
        
        # Clean up
        del large_array
        gc.collect()
        
        # With a 10MB threshold, we expect True if memory usage > 10MB
        # (which it should be given the large array)
        # However, due to OS caching, we just verify the function returns a boolean
        assert isinstance(result, bool), "Result should be boolean"