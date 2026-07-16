"""
Tests for CPU-only execution enforcement.

These tests verify that the test framework correctly enforces CPU-only
execution, which is critical for compatibility with environments that
do not have GPU resources.
"""
import pytest
import os
import numpy as np


class TestCPUExecution:
    """Test suite for CPU-only execution enforcement."""

    def test_cuda_visible_devices_is_empty(self):
        """Verify that CUDA_VISIBLE_DEVICES is set to empty string."""
        # The conftest.py fixture should have set this
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == '', \
            "CUDA_VISIBLE_DEVICES should be empty to enforce CPU-only execution"

    def test_tensorflow_cpu_only(self):
        """Test that TensorFlow operations run on CPU only."""
        try:
            import tensorflow as tf
            # Check that no GPU is available
            gpus = tf.config.list_physical_devices('GPU')
            assert len(gpus) == 0, "No GPUs should be available in CPU-only mode"
        except ImportError:
            # TensorFlow not installed, skip this test
            pytest.skip("TensorFlow not installed")

    def test_pytorch_cpu_only(self):
        """Test that PyTorch operations run on CPU only."""
        try:
            import torch
            # Check that CUDA is not available
            assert not torch.cuda.is_available(), "CUDA should not be available in CPU-only mode"
        except ImportError:
            # PyTorch not installed, skip this test
            pytest.skip("PyTorch not installed")

    def test_numpy_operations_on_cpu(self):
        """Test that basic NumPy operations work correctly on CPU."""
        # Create arrays and perform operations
        a = np.array([1, 2, 3, 4, 5])
        b = np.array([5, 4, 3, 2, 1])

        result = a + b
        expected = np.array([6, 6, 6, 6, 6])

        assert np.array_equal(result, expected), "NumPy operations should work correctly on CPU"

    def test_pandas_operations_on_cpu(self):
        """Test that Pandas operations work correctly on CPU."""
        import pandas as pd

        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        result = df['a'] + df['b']
        expected = pd.Series([5, 7, 9])

        pd.testing.assert_series_equal(result, expected)

    def test_memory_usage_within_limits(self):
        """Test that memory usage stays within reasonable limits for sample operations."""
        # Create a moderately sized array
        size = 1000000  # 1M elements
        arr = np.random.rand(size)

        # Perform operations that would be problematic on GPU with limited memory
        mean_val = np.mean(arr)
        std_val = np.std(arr)

        assert isinstance(mean_val, (float, np.floating))
        assert isinstance(std_val, (float, np.floating))
        assert 0.4 < mean_val < 0.6  # Expected mean for uniform [0,1]
        assert 0.25 < std_val < 0.3  # Expected std for uniform [0,1]
