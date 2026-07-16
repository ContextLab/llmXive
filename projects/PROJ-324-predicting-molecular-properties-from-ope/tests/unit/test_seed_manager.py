"""
Unit tests for seed management functionality.
"""
import random
import os
import pytest

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from code.seed_manager import set_global_seed, get_seed


def test_set_seed_updates_global():
    """Test that set_global_seed updates the internal state."""
    set_global_seed(12345)
    assert get_seed() == 12345


def test_python_random_reproducibility():
    """Test that Python's random module is seeded correctly."""
    seed_val = 42
    set_global_seed(seed_val)
    val1 = random.random()

    set_global_seed(seed_val)
    val2 = random.random()

    assert val1 == val2


def test_numpy_reproducibility():
    """Test that numpy's random state is seeded correctly."""
    if not HAS_NUMPY:
        pytest.skip("NumPy not installed")

    seed_val = 999
    set_global_seed(seed_val)
    arr1 = np.random.rand(5)

    set_global_seed(seed_val)
    arr2 = np.random.rand(5)

    assert np.array_equal(arr1, arr2)


def test_torch_reproducibility():
    """Test that torch's random state is seeded correctly."""
    if not HAS_TORCH:
        pytest.skip("PyTorch not installed")

    seed_val = 777
    set_global_seed(seed_val)
    t1 = torch.rand(5)

    set_global_seed(seed_val)
    t2 = torch.rand(5)

    assert torch.equal(t1, t2)


def test_env_var_set():
    """Test that PYTHONHASHSEED environment variable is set."""
    seed_val = 111
    set_global_seed(seed_val)
    assert os.environ.get("PYTHONHASHSEED") == str(seed_val)
