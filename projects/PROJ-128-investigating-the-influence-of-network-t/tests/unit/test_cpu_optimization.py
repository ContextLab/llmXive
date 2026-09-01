"""
Unit tests for CPU optimization utilities.
"""
import os
import sys
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.cpu_optimization import (
    validate_no_gpu_acceleration,
    optimize_memory_usage,
    set_random_seed,
    ensure_numpy_arrays_contiguous,
    force_gc_collect,
    chunked_dataframe_iterator
)


class TestValidateNoGpu:
    def test_validate_no_gpu_acceleration_no_imports(self):
        """Test when no GPU libraries are installed."""
        # Mock the absence of torch, tensorflow, jax
        with patch.dict(sys.modules, {
            'torch': None,
            'tensorflow': None,
            'jax': None
        }, clear=False):
            # This will raise ImportError in the function, which is caught
            # and returns True (CPU only)
            result = validate_no_gpu_acceleration()
            assert result is True


class TestOptimizeMemoryUsage:
    def test_optimize_memory_usage_dataframe(self):
        """Test memory optimization on a DataFrame."""
        df = pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'object_col': ['a', 'b', 'c', 'd', 'e']
        })

        optimized_df = optimize_memory_usage(df)

        # Check that downcasting happened
        assert optimized_df['int_col'].dtype in ['int8', 'int16', 'int32', 'int64']
        # Float64 might stay if values are large, but we check it's a numeric type
        assert np.issubdtype(optimized_df['float_col'].dtype, np.floating)

    def test_optimize_memory_usage_numpy_array(self):
        """Test memory optimization on a numpy array."""
        arr = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
        # Make it non-contiguous
        arr = arr.T

        optimized_arr = optimize_memory_usage(arr)

        assert optimized_arr.flags['C_CONTIGUOUS']
        assert optimized_arr.dtype == arr.dtype


class TestSetRandomSeed:
    def test_set_random_seed(self):
        """Test that random seed is set."""
        set_random_seed(123)
        assert np.random.get_state()[1][0] == 123


class TestEnsureContiguous:
    def test_ensure_contiguous(self):
        """Test ensuring arrays are contiguous."""
        arr1 = np.array([[1.0, 2.0], [3.0, 4.0]]).T  # Non-contiguous
        arr2 = np.array([[5.0, 6.0], [7.0, 8.0]])    # Contiguous

        result = ensure_numpy_arrays_contiguous([arr1, arr2])

        assert result[0].flags['C_CONTIGUOUS']
        assert result[1].flags['C_CONTIGUOUS']


class TestForceGcCollect:
    def test_force_gc_collect(self):
        """Test garbage collection."""
        result = force_gc_collect()
        assert isinstance(result, int)
        assert result >= 0


class TestChunkedIterator:
    def test_chunked_dataframe_iterator(self):
        """Test chunked iteration over a DataFrame."""
        df = pd.DataFrame({'a': range(10), 'b': range(10, 20)})

        chunks = list(chunked_dataframe_iterator(df, chunk_size=3))

        assert len(chunks) == 4  # 10 / 3 -> 4 chunks
        assert len(chunks[0]) == 3
        assert len(chunks[1]) == 3
        assert len(chunks[2]) == 3
        assert len(chunks[3]) == 1

        # Check data integrity
        pd.testing.assert_frame_equal(
            pd.concat(chunks).reset_index(drop=True),
            df.reset_index(drop=True)
        )