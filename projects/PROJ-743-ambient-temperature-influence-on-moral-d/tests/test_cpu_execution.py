"""
Tests to verify CPU-only execution constraints.
"""
import os
import pytest

def test_cuda_visible_devices_unset():
    """
    Verify that CUDA_VISIBLE_DEVICES is set to empty string to force CPU usage.
    """
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", \
        "CUDA_VISIBLE_DEVICES must be empty to enforce CPU-only execution."

def test_no_gpu_imports_in_test_scope():
    """
    Verify that no GPU-specific libraries are imported in the test scope.
    This is a static check; actual imports happen at runtime.
    """
    # Check if torch or tensorflow are available and if they would try to use GPU
    # We rely on the conftest hook to set env vars before import
    try:
        import torch
        # If torch is available, ensure it's not using GPU
        if torch.cuda.is_available():
            # This should not happen if CUDA_VISIBLE_DEVICES is set correctly
            # But we check anyway
            assert False, "PyTorch detected GPU availability despite CPU-only enforcement."
    except ImportError:
        pass  # PyTorch not installed, which is fine for CPU-only

    try:
        import tensorflow as tf
        # If tensorflow is available, ensure it's not using GPU
        if tf.config.list_physical_devices('GPU'):
            assert False, "TensorFlow detected GPU availability despite CPU-only enforcement."
    except ImportError:
        pass  # TensorFlow not installed, which is fine for CPU-only
