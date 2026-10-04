"""
Unit tests for CPU optimization utilities.

These tests verify that the optimization functions work correctly and
that the pipeline properly enforces CPU-only execution.
"""
import os
import sys
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from utils.cpu_optimization import (
    validate_no_gpu_acceleration,
    optimize_memory_usage,
    chunked_dataframe_iterator,
    set_random_seed,
    ensure_numpy_arrays_contiguous,
    force_gc_collect,
    convert_to_low_precision,
    limit_pandas_cache,
    monitor_memory_usage,
    validate_cpu_only_environment
)

class TestValidateNoGPU:
    """Tests for GPU validation functions."""

    def test_validate_no_gpu_with_no_gpu(self):
        """Test that validation passes when no GPU is available."""
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
            result = validate_no_gpu_acceleration()
            assert result is True

    def test_validate_no_gpu_with_cuda_env(self):
        """Test that warning is issued when CUDA_VISIBLE_DEVICES is set."""
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '0'}):
            with pytest.warns(UserWarning, match="CUDA_VISIBLE_DEVICES is set"):
                validate_no_gpu_acceleration()

    @patch('utils.cpu_optimization.torch')
    def test_validate_no_gpu_with_pytorch_gpu(self, mock_torch):
        """Test that error is raised when PyTorch GPU is available."""
        mock_torch.cuda.is_available.return_value = True
        
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
            with pytest.raises(RuntimeError, match="PyTorch GPU is available"):
                validate_no_gpu_acceleration()

    @patch('utils.cpu_optimization.tf')
    def test_validate_no_gpu_with_tensorflow_gpu(self, mock_tf):
        """Test that error is raised when TensorFlow GPU is available."""
        mock_tf.config.list_physical_devices.return_value = ['GPU']
        
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
            with pytest.raises(RuntimeError, match="TensorFlow GPU devices detected"):
                validate_no_gpu_acceleration()

class TestOptimizeMemoryUsage:
    """Tests for memory optimization functions."""

    def test_optimize_memory_usage_downcast(self):
        """Test that numeric columns are downcast correctly."""
        df = pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        optimized = optimize_memory_usage(df, low_precision=True)
        
        # Check that columns are downcast
        assert optimized['int_col'].dtype in ['int8', 'int16', 'int32']
        assert optimized['float_col'].dtype in ['float32']

    def test_optimize_memory_usage_category(self):
        """Test that low-cardinality object columns are converted to category."""
        df = pd.DataFrame({
            'low_cardinality': ['a', 'b', 'a', 'b', 'a'],
            'high_cardinality': ['x1', 'x2', 'x3', 'x4', 'x5']
        })
        
        optimized = optimize_memory_usage(df, low_precision=True)
        
        # Check that low-cardinality column is category
        assert optimized['low_cardinality'].dtype.name == 'category'

    def test_optimize_memory_usage_empty_df(self):
        """Test that empty DataFrame is handled correctly."""
        df = pd.DataFrame()
        optimized = optimize_memory_usage(df)
        assert optimized.empty

    def test_optimize_memory_usage_none_input(self):
        """Test that None input is handled correctly."""
        result = optimize_memory_usage(None)
        assert result is None

class TestChunkedIterator:
    """Tests for chunked dataframe iteration."""

    def test_chunked_iterator_basic(self):
        """Test basic chunked iteration."""
        df = pd.DataFrame({'col': range(25)})
        
        chunks = list(chunked_dataframe_iterator(df, chunk_size=10))
        
        assert len(chunks) == 3  # 25 rows / 10 = 3 chunks
        assert len(chunks[0]) == 10
        assert len(chunks[1]) == 10
        assert len(chunks[2]) == 5

    def test_chunked_iterator_empty(self):
        """Test chunked iteration with empty DataFrame."""
        df = pd.DataFrame()
        chunks = list(chunked_dataframe_iterator(df))
        assert len(chunks) == 0

    def test_chunked_iterator_none(self):
        """Test chunked iteration with None input."""
        result = list(chunked_dataframe_iterator(None))
        assert len(result) == 0

class TestRandomSeed:
    """Tests for random seed setting."""

    def test_set_random_seed(self):
        """Test that random seeds are set correctly."""
        set_random_seed(42)
        
        # Verify numpy seed
        assert np.random.get_state()[1][0] == 42

    def test_set_random_seed_default(self):
        """Test that default seed is 42."""
        set_random_seed()
        
        # Verify numpy seed
        assert np.random.get_state()[1][0] == 42

class TestEnsureContiguous:
    """Tests for ensuring numpy array contiguity."""

    def test_ensure_contiguous_already_contiguous(self):
        """Test that already contiguous arrays are not modified."""
        arr = np.array([1, 2, 3, 4, 5])
        assert arr.flags['C_CONTIGUOUS']
        
        result = ensure_numpy_arrays_contiguous(arr)
        assert result[0].flags['C_CONTIGUOUS']

    def test_ensure_contiguous_non_contiguous(self):
        """Test that non-contiguous arrays are made contiguous."""
        arr = np.array([[1, 2, 3], [4, 5, 6]]).T  # Non-contiguous
        assert not arr.flags['C_CONTIGUOUS']
        
        result = ensure_numpy_arrays_contiguous(arr)
        assert result[0].flags['C_CONTIGUOUS']

class TestConvertLowPrecision:
    """Tests for low precision conversion."""

    def test_convert_float64_to_float32(self):
        """Test conversion from float64 to float32."""
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        
        result = convert_to_low_precision(arr)
        
        assert result.dtype == np.float32

    def test_convert_int64_to_int32(self):
        """Test conversion from int64 to int32."""
        arr = np.array([1, 2, 3], dtype=np.int64)
        
        result = convert_to_low_precision(arr)
        
        assert result.dtype == np.int32

    def test_convert_already_correct_dtype(self):
        """Test that arrays with correct dtype are not modified."""
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        
        result = convert_to_low_precision(arr)
        
        assert result.dtype == np.float32
        assert result is arr  # Should return same object

class TestMemoryMonitoring:
    """Tests for memory monitoring functions."""

    def test_monitor_memory_usage(self):
        """Test that memory usage monitoring returns valid data."""
        mem_stats = monitor_memory_usage()
        
        assert isinstance(mem_stats, dict)
        assert len(mem_stats) > 0

    def test_force_gc_collect(self):
        """Test that garbage collection returns a count."""
        count = force_gc_collect()
        assert isinstance(count, int)
        assert count >= 0

class TestValidateCPUOnlyEnvironment:
    """Tests for comprehensive CPU environment validation."""

    def test_validate_cpu_only_success(self):
        """Test that validation passes in CPU-only environment."""
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
            result = validate_cpu_only_environment()
            assert result is True

    def test_validate_cpu_only_memory_limit(self):
        """Test that validation fails when memory usage is too high."""
        with patch('utils.cpu_optimization.monitor_memory_usage') as mock_mem:
            mock_mem.return_value = {'max_rss_mb': 15000}  # Over 14GB limit
            
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
                with pytest.raises(RuntimeError, match="Memory usage"):
                    validate_cpu_only_environment()