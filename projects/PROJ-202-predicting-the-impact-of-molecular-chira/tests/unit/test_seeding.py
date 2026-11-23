"""
Unit tests for the seeding utility.

These tests verify that the `set_seed` function correctly initializes
random states for available libraries and raises appropriate errors
for invalid inputs.
"""

import os
import random
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# Assuming the project root is in sys.path or installed
from code.utils.seeding import set_seed, get_seed_info, HAS_NUMPY, HAS_TORCH, HAS_TF


def test_set_seed_invalid_type():
    """Test that set_seed raises ValueError for non-integer seeds."""
    with pytest.raises(ValueError):
        set_seed("42")
    with pytest.raises(ValueError):
        set_seed(-1)
    with pytest.raises(ValueError):
        set_seed(3.14)


def test_set_seed_valid_int():
    """Test that set_seed accepts valid non-negative integers."""
    # Should not raise
    set_seed(0)
    set_seed(12345)
    set_seed(999999999)


def test_set_seed_python_random():
    """Test that Python's random module is seeded correctly."""
    seed_val = 42
    set_seed(seed_val)
    val1 = random.random()

    set_seed(seed_val)
    val2 = random.random()

    assert val1 == val2, "Python random state should be reproducible with same seed"


def test_set_seed_numpy():
    """Test that NumPy is seeded correctly if available."""
    if not HAS_NUMPY:
        pytest.skip("NumPy not installed")

    import numpy as np

    seed_val = 123
    set_seed(seed_val)
    arr1 = np.random.rand(5)

    set_seed(seed_val)
    arr2 = np.random.rand(5)

    assert np.array_equal(arr1, arr2), "NumPy random state should be reproducible"


def test_set_seed_torch():
    """Test that PyTorch is seeded correctly if available."""
    if not HAS_TORCH:
        pytest.skip("PyTorch not installed")

    import torch

    seed_val = 456
    set_seed(seed_val)
    t1 = torch.rand(5)

    set_seed(seed_val)
    t2 = torch.rand(5)

    assert torch.equal(t1, t2), "PyTorch random state should be reproducible"


def test_set_seed_tensorflow():
    """Test that TensorFlow is seeded correctly if available."""
    if not HAS_TF:
        pytest.skip("TensorFlow not installed")

    import tensorflow as tf

    seed_val = 789
    set_seed(seed_val)
    t1 = tf.random.uniform([5])

    set_seed(seed_val)
    t2 = tf.random.uniform([5])

    # TensorFlow tensors need to be compared via numpy
    assert (t1.numpy() == t2.numpy()).all(), "TensorFlow random state should be reproducible"


def test_set_seed_env_var():
    """Test that PYTHONHASHSEED environment variable is set."""
    seed_val = 111
    set_seed(seed_val)
    assert os.environ.get("PYTHONHASHSEED") == str(seed_val)


def test_get_seed_info():
    """Test that get_seed_info returns expected structure."""
    info = get_seed_info()
    assert "seed" in info
    assert "libraries" in info
    assert isinstance(info["libraries"], dict)
    assert "random" in info["libraries"]
    assert "numpy" in info["libraries"]
    assert "torch" in info["libraries"]
    assert "tensorflow" in info["libraries"]