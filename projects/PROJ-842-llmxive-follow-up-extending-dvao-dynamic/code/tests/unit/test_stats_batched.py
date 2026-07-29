"""
Unit tests for batched variance calculations in stats.py.
"""
import pytest
import numpy as np
import sys
import os
from src.analysis.stats import (
    get_memory_usage_bytes,
    check_memory_limit,
    batched_variance_generator,
    calculate_batched_variance,
    run_sensitivity_sweep,
    calculate_windowed_variance_batched
)


class TestBatchedVariance:
    """Tests for calculate_batched_variance function."""

    def test_small_array(self):
        """Test variance calculation on a small array."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        expected_var = np.var(data, ddof=1)
        result = calculate_batched_variance(data)
        assert np.isclose(result, expected_var)

    def test_large_array(self):
        """Test variance calculation on a large array (triggers batching)."""
        # Create a large array that exceeds typical batch size
        data = np.random.randn(200000)
        expected_var = np.var(data, ddof=1)
        result = calculate_batched_variance(data, batch_size=10000)
        assert np.isclose(result, expected_var, rtol=1e-5)

    def test_list_of_arrays(self):
        """Test variance calculation on a list of arrays."""
        arr1 = np.array([1.0, 2.0, 3.0])
        arr2 = np.array([4.0, 5.0, 6.0])
        combined = np.concatenate([arr1, arr2])
        expected_var = np.var(combined, ddof=1)
        result = calculate_batched_variance([arr1, arr2])
        assert np.isclose(result, expected_var)

    def test_empty_array_raises(self):
        """Test that empty array raises ValueError."""
        with pytest.raises(ValueError):
            calculate_batched_variance(np.array([]))

    def test_empty_list_raises(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError):
            calculate_batched_variance([])

    def test_single_value(self):
        """Test variance with a single value (should be 0 or NaN depending on ddof)."""
        data = np.array([5.0])
        # With ddof=1, variance of single value is undefined (NaN)
        result = calculate_batched_variance(data)
        assert np.isnan(result) or result == 0.0  # Handle both cases


class TestBatchedVarianceGenerator:
    """Tests for batched_variance_generator function."""

    def test_generator_output(self):
        """Test that generator yields correct variances."""
        def data_gen():
            yield np.array([1.0, 2.0, 3.0])
            yield np.array([4.0, 5.0, 6.0])

        results = list(batched_variance_generator(data_gen()))
        assert len(results) == 2
        
        # Check first batch variance
        idx1, var1 = results[0]
        assert idx1 == 0
        expected_var1 = np.var([1.0, 2.0, 3.0], ddof=1)
        assert np.isclose(var1, expected_var1)
        
        # Check second batch variance
        idx2, var2 = results[1]
        assert idx2 == 1
        expected_var2 = np.var([4.0, 5.0, 6.0], ddof=1)
        assert np.isclose(var2, expected_var2)

    def test_empty_batch_handling(self):
        """Test that empty batches are handled with a warning."""
        def data_gen():
            yield np.array([])
            yield np.array([1.0, 2.0])

        with pytest.warns(UserWarning):
            results = list(batched_variance_generator(data_gen()))
        
        # Should have one valid result (second batch)
        assert len(results) == 1


class TestMemoryMonitoring:
    """Tests for memory monitoring functions."""

    def test_get_memory_usage_bytes(self):
        """Test that get_memory_usage_bytes returns a positive integer."""
        mem = get_memory_usage_bytes()
        assert isinstance(mem, int)
        assert mem > 0

    def test_check_memory_limit_pass(self):
        """Test check_memory_limit passes when under limit."""
        # Use a very high limit to ensure we pass
        assert check_memory_limit(limit_bytes=10**12) is True

    def test_check_memory_limit_fail(self):
        """Test check_memory_limit raises MemoryError when over limit."""
        with pytest.raises(MemoryError):
            check_memory_limit(limit_bytes=1)  # 1 byte limit


class TestWindowedVarianceBatched:
    """Tests for calculate_windowed_variance_batched function."""

    def test_basic_window(self):
        """Test basic sliding window variance calculation."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        window_size = 3
        
        result = calculate_windowed_variance_batched(data, window_size)
        
        # Expected: variance of [1,2,3], [2,3,4], [3,4,5]
        expected = [
            np.var([1.0, 2.0, 3.0], ddof=1),
            np.var([2.0, 3.0, 4.0], ddof=1),
            np.var([3.0, 4.0, 5.0], ddof=1)
        ]
        
        assert len(result) == len(expected)
        for r, e in zip(result, expected):
            assert np.isclose(r, e)

    def test_window_size_larger_than_data_raises(self):
        """Test that window_size > len(data) raises ValueError."""
        data = np.array([1.0, 2.0])
        with pytest.raises(ValueError):
            calculate_windowed_variance_batched(data, window_size=5)

    def test_single_window(self):
        """Test with window_size equal to data length."""
        data = np.array([1.0, 2.0, 3.0])
        result = calculate_windowed_variance_batched(data, window_size=3)
        assert len(result) == 1
        assert np.isclose(result[0], np.var(data, ddof=1))