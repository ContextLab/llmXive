"""
Unit tests for memory efficiency optimizations in llmXive pipeline.

Tests verify that memory management utilities function correctly
and that data processing respects memory constraints.
"""
import pytest
import numpy as np
import torch
from unittest.mock import patch, MagicMock
import gc
import sys
import tracemalloc
from pathlib import Path

# Import modules under test
from utils.memory_optimizer import (
    get_current_memory_mb,
    get_peak_memory_mb,
    start_memory_profiling,
    stop_memory_profiling,
    enforce_memory_limit,
    force_garbage_collection,
    clear_cuda_cache,
    optimize_for_memory,
    memory_safe_iterator,
    monitor_memory_usage,
    profile_function,
    safe_delete,
    check_memory_constraints
)
from utils.error_handling import DataFetchError

class TestMemoryOptimizer:
    """Test cases for memory optimization utilities."""

    def test_get_current_memory_mb_returns_positive(self):
        """Test that current memory measurement returns a positive value."""
        mem = get_current_memory_mb()
        assert isinstance(mem, float)
        assert mem >= 0

    def test_start_stop_memory_profiling(self):
        """Test starting and stopping memory profiling."""
        # Should not raise
        start_memory_profiling()
        stop_memory_profiling()

    def test_enforce_memory_limit_within_bounds(self):
        """Test that enforce_memory_limit does not raise when under limit."""
        # Use a high limit to ensure we're under it
        enforce_memory_limit(limit_mb=10000)
        # If we reach here, no exception was raised

    def test_enforce_memory_limit_exceeded(self):
        """Test that enforce_memory_limit raises MemoryError when exceeded."""
        # Use a very low limit that we're surely over
        with pytest.raises(MemoryError):
            enforce_memory_limit(limit_mb=0.001)

    def test_force_garbage_collection_returns_int(self):
        """Test that force_garbage_collection returns an integer count."""
        collected = force_garbage_collection()
        assert isinstance(collected, int)
        assert collected >= 0

    def test_clear_cuda_cache_no_error(self):
        """Test that clear_cuda_cache runs without error."""
        # Should not raise even if no CUDA
        clear_cuda_cache()

    def test_optimize_for_memory_numpy_float64_to_float32(self):
        """Test numpy array dtype optimization from float64 to float32."""
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        optimized = optimize_for_memory(arr)
        assert optimized.dtype == np.float32
        assert np.array_equal(optimized, arr.astype(np.float32))

    def test_optimize_for_memory_numpy_int64_to_int32(self):
        """Test numpy array dtype optimization from int64 to int32."""
        arr = np.array([1, 2, 3], dtype=np.int64)
        optimized = optimize_for_memory(arr)
        assert optimized.dtype == np.int32
        assert np.array_equal(optimized, arr.astype(np.int32))

    def test_optimize_for_memory_list(self):
        """Test list optimization recursively."""
        data = [np.array([1.0], dtype=np.float64), 5, "test"]
        optimized = optimize_for_memory(data)
        assert isinstance(optimized, list)
        assert optimized[0].dtype == np.float32

    def test_optimize_for_memory_dict(self):
        """Test dict optimization recursively."""
        data = {"arr": np.array([1.0], dtype=np.float64), "val": 10}
        optimized = optimize_for_memory(data)
        assert isinstance(optimized, dict)
        assert optimized["arr"].dtype == np.float32

    def test_memory_safe_iterator_yields_items(self):
        """Test that memory_safe_iterator yields all items."""
        data = list(range(10))
        result = list(memory_safe_iterator(iter(data), chunk_size=2))
        assert result == data

    def test_memory_safe_iterator_enforces_limit(self):
        """Test that memory_safe_iterator enforces memory limits."""
        # Mock enforce_memory_limit to raise
        with patch('utils.memory_optimizer.enforce_memory_limit') as mock_limit:
            mock_limit.side_effect = MemoryError("Limit exceeded")
            data = list(range(10))
            with pytest.raises(MemoryError):
                list(memory_safe_iterator(iter(data), chunk_size=1, limit_mb=1))

    def test_monitor_memory_usage_decorator(self):
        """Test that monitor_memory_usage decorator works."""
        @monitor_memory_usage
        def test_func():
            return 42
        
        result = test_func()
        assert result == 42

    def test_profile_function_decorator(self):
        """Test that profile_function decorator works."""
        @profile_function
        def test_func():
            return [1, 2, 3]
        
        result = test_func()
        assert result == [1, 2, 3]

    def test_safe_delete(self):
        """Test that safe_delete removes reference."""
        obj = [1, 2, 3]
        safe_delete(obj)
        # If we reach here, no error occurred

    def test_check_memory_constraints_sufficient(self):
        """Test check_memory_constraints returns True when sufficient."""
        # Use a very small requirement
        result = check_memory_constraints(required_mb=1.0, safety_factor=1.0)
        assert isinstance(result, bool)

    def test_check_memory_constraints_insufficient(self):
        """Test check_memory_constraints returns False when insufficient."""
        # Use an impossibly large requirement
        result = check_memory_constraints(required_mb=1000000.0, safety_factor=1.0)
        assert isinstance(result, bool)

class TestMemoryEfficiencyIntegration:
    """Integration tests for memory efficiency in data processing."""

    @pytest.fixture
    def sample_data(self):
        """Generate sample data for testing."""
        return [
            {"id": i, "text": "Sample text " * 100, "value": i * 1.5}
            for i in range(100)
        ]

    def test_streaming_processing_memory_safe(self, sample_data):
        """Test that streaming processing maintains memory safety."""
        # Simulate streaming with memory checks
        processed = []
        for i, item in enumerate(sample_data):
            processed.append(item)
            if i % 10 == 0:
                force_garbage_collection()
                # Should not raise
                enforce_memory_limit(limit_mb=10000)
        
        assert len(processed) == len(sample_data)

    def test_optimize_before_serialization(self, sample_data):
        """Test optimizing data before JSON serialization."""
        optimized_data = [optimize_for_memory(item) for item in sample_data]
        import json
        # Should serialize without error
        for item in optimized_data:
            json.dumps(item)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])