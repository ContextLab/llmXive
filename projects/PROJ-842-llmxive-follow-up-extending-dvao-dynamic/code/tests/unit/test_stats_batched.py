"""
Unit tests for batched variance calculations and memory monitoring (T055).
"""
import pytest
import numpy as np
import sys
import os
from unittest.mock import patch, MagicMock
import psutil

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.analysis.stats import (
    get_memory_usage_bytes,
    check_memory_limit,
    batched_variance_generator,
    calculate_batched_variance,
    run_sensitivity_sweep,
    calculate_windowed_variance_batched
)


class TestBatchedVariance:
    """Tests for batched variance calculation functions."""
    
    def test_calculate_batched_variance_basic(self):
        """Test basic variance calculation with batched processing."""
        # Create known data with known variance
        np.random.seed(42)
        data = np.random.normal(loc=10.0, scale=2.0, size=10000)
        expected_variance = np.var(data, ddof=1)
        
        # Calculate using batched method
        batch_variance, n = calculate_batched_variance(data, batch_size=1000)
        
        assert n == len(data), f"Expected {len(data)} samples, got {n}"
        assert np.isclose(batch_variance, expected_variance, rtol=1e-5), \
            f"Batch variance {batch_variance} != expected {expected_variance}"
    
    def test_calculate_batched_variance_small_batch(self):
        """Test variance calculation with very small batch size."""
        np.random.seed(123)
        data = np.random.uniform(0, 1, size=500)
        expected_variance = np.var(data, ddof=1)
        
        batch_variance, n = calculate_batched_variance(data, batch_size=50)
        
        assert np.isclose(batch_variance, expected_variance, rtol=1e-4)
    
    def test_calculate_batched_variance_single_element(self):
        """Test variance calculation with single element (should be 0 or NaN)."""
        data = np.array([5.0])
        variance, n = calculate_batched_variance(data, batch_size=1)
        
        assert n == 1
        # Variance of single element is 0 or undefined
        assert variance == 0.0 or np.isnan(variance)
    
    def test_calculate_batched_variance_large_array(self):
        """Test with a larger array to ensure batch processing works."""
        np.random.seed(456)
        data = np.random.exponential(scale=1.0, size=50000)
        expected_variance = np.var(data, ddof=1)
        
        batch_variance, n = calculate_batched_variance(data, batch_size=5000)
        
        assert n == len(data)
        assert np.isclose(batch_variance, expected_variance, rtol=1e-4)


class TestBatchedVarianceGenerator:
    """Tests for the batched variance generator."""
    
    def test_generator_basic(self):
        """Test basic generator functionality."""
        def data_stream():
            for i in range(5):
                yield np.random.normal(0, 1, 100)
        
        results = list(batched_variance_generator(data_stream(), batch_size=100))
        
        assert len(results) == 5
        for idx, var in results:
            assert isinstance(var, float)
            assert var >= 0  # Variance is non-negative
    
    def test_generator_empty_batches(self):
        """Test generator with empty batches."""
        def data_stream():
            yield np.array([])
            yield np.array([1.0, 2.0, 3.0])
            yield np.array([])
        
        results = list(batched_variance_generator(data_stream(), batch_size=10))
        
        # Should skip empty batches
        assert len(results) == 1
        assert results[0][1] > 0  # Variance of [1,2,3] should be positive
    
    def test_generator_memory_check(self):
        """Test that generator performs memory checks."""
        def data_stream():
            for i in range(20):  # Enough batches to trigger memory check
                yield np.random.normal(0, 1, 100)
        
        # This should not raise an exception under normal conditions
        results = list(batched_variance_generator(
            data_stream(), 
            batch_size=100,
            memory_check_interval=5
        ))
        
        assert len(results) == 20


class TestMemoryMonitoring:
    """Tests for memory monitoring functions."""
    
    def test_get_memory_usage_bytes(self):
        """Test that memory usage is returned as a positive integer."""
        memory = get_memory_usage_bytes()
        
        assert isinstance(memory, int)
        assert memory > 0
        assert memory < 100 * 1024 * 1024 * 1024  # Less than 100GB
    
    def test_check_memory_limit_pass(self):
        """Test that check_memory_limit passes when under limit."""
        # This should not raise an exception
        check_memory_limit(limit_gb=7.0)
    
    def test_check_memory_limit_fail(self):
        """Test that check_memory_limit raises MemoryError when over limit."""
        # Mock psutil to simulate high memory usage
        with patch('psutil.Process') as mock_process:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=10 * 1024**3)  # 10GB
            mock_process.return_value = mock_instance
            
            with pytest.raises(MemoryError):
                check_memory_limit(limit_gb=7.0)
    
    def test_check_memory_limit_exact_boundary(self):
        """Test memory check at exact boundary."""
        # Mock exactly at the limit
        with patch('psutil.Process') as mock_process:
            limit_bytes = 7.0 * 1024**3
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=limit_bytes)
            mock_process.return_value = mock_instance
            
            # Should pass (not exceed)
            check_memory_limit(limit_gb=7.0)
    
    def test_check_memory_limit_just_over(self):
        """Test memory check just over the limit."""
        with patch('psutil.Process') as mock_process:
            limit_bytes = 7.0 * 1024**3
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=limit_bytes + 1)
            mock_process.return_value = mock_instance
            
            with pytest.raises(MemoryError):
                check_memory_limit(limit_gb=7.0)


class TestWindowedVarianceBatched:
    """Tests for windowed variance with batch processing."""
    
    def test_calculate_windowed_variance_batched_basic(self):
        """Test basic windowed variance calculation."""
        np.random.seed(789)
        data = np.random.normal(0, 1, size=1000)
        window_size = 100
        
        variance = calculate_windowed_variance_batched(data, window_size, batch_size=50)
        
        expected_variance = np.var(data[-window_size:], ddof=1)
        assert np.isclose(variance, expected_variance, rtol=1e-5)
    
    def test_calculate_windowed_variance_batched_small_window(self):
        """Test with small window size."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        window_size = 3
        
        variance = calculate_windowed_variance_batched(data, window_size, batch_size=2)
        
        expected_variance = np.var(data[-3:], ddof=1)
        assert np.isclose(variance, expected_variance)
    
    def test_calculate_windowed_variance_batched_invalid_window(self):
        """Test with window size >= data length."""
        data = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError):
            calculate_windowed_variance_batched(data, window_size=3, batch_size=1)
    
    def test_calculate_windowed_variance_batched_memory_efficient(self):
        """Test that large window uses batch processing efficiently."""
        np.random.seed(101112)
        data = np.random.normal(0, 1, size=10000)
        window_size = 5000
        
        variance = calculate_windowed_variance_batched(data, window_size, batch_size=1000)
        
        expected_variance = np.var(data[-window_size:], ddof=1)
        assert np.isclose(variance, expected_variance, rtol=1e-4)


class TestIntegration:
    """Integration tests for batched variance pipeline."""
    
    def test_full_pipeline_memory_constrained(self):
        """Test full variance calculation pipeline under memory constraints."""
        np.random.seed(131415)
        
        # Create moderately large dataset
        data = np.random.normal(0, 1, size=20000)
        
        # Run batched variance with small batches
        variance, n = calculate_batched_variance(data, batch_size=1000)
        
        expected = np.var(data, ddof=1)
        assert np.isclose(variance, expected, rtol=1e-4)
        assert n == len(data)
        
        # Verify memory check passes
        check_memory_limit(limit_gb=7.0)
    
    def test_sensitivity_sweep_batched(self):
        """Test sensitivity sweep with batched processing."""
        np.random.seed(161718)
        data = np.random.normal(0, 1, size=5000)
        window_sizes = [10, 50, 100, 200]
        
        results = run_sensitivity_sweep(data, window_sizes, batch_size=1000)
        
        assert 'results' in results
        assert len(results['results']) == len(window_sizes)
        
        for k_str, result in results['results'].items():
            assert 'variance' in result
            assert 'n_samples' in result
            assert result['n_samples'] == int(k_str)
    
    def test_memory_check_during_batched_calculation(self):
        """Test that memory checks occur during batched calculations."""
        np.random.seed(192021)
        data = np.random.normal(0, 1, size=100000)
        
        # This should complete without memory errors and perform periodic checks
        variance, n = calculate_batched_variance(data, batch_size=10000)
        
        assert n == len(data)
        assert variance > 0
        check_memory_limit(limit_gb=7.0)