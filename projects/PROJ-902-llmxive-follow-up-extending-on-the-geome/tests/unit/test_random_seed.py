"""Unit tests for the deterministic RNG seeding helper.

This module verifies that `src.utils.random_seed.set_seed` correctly
propagates seed values to Python's built-in `random`, `numpy`, and `torch`.
"""

import random
import os

import numpy as np

# Conditionally import torch if available; skip tests if not present
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

import pytest

# Import the function under test
from code.utils.random_seed import set_seed


def test_set_seed_updates_python_random():
    """Verify that set_seed changes the state of Python's random module."""
    seed_value = 42
    set_seed(seed_value)

    val1 = random.random()

    # Reset and verify reproducibility
    set_seed(seed_value)
    val2 = random.random()

    assert val1 == val2, "Python random state was not reproducible with the same seed."


def test_set_seed_updates_numpy():
    """Verify that set_seed changes the state of numpy's random generator."""
    seed_value = 123
    set_seed(seed_value)

    arr1 = np.random.rand(5)

    # Reset and verify reproducibility
    set_seed(seed_value)
    arr2 = np.random.rand(5)

    np.testing.assert_array_equal(arr1, arr2, "NumPy random state was not reproducible.")


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not installed")
def test_set_seed_updates_torch_cpu():
    """Verify that set_seed changes the state of torch's CPU random generator."""
    seed_value = 999
    set_seed(seed_value)

    tensor1 = torch.rand(5)

    # Reset and verify reproducibility
    set_seed(seed_value)
    tensor2 = torch.rand(5)

    torch.testing.assert_close(tensor1, tensor2, "Torch CPU random state was not reproducible.")


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not installed")
def test_set_seed_updates_torch_cuda():
    """Verify that set_seed changes the state of torch's CUDA random generator if available."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")

    seed_value = 777
    set_seed(seed_value)

    tensor1 = torch.rand(5, device='cuda')

    # Reset and verify reproducibility
    set_seed(seed_value)
    tensor2 = torch.rand(5, device='cuda')

    torch.testing.assert_close(tensor1, tensor2, "Torch CUDA random state was not reproducible.")


def test_set_seed_deterministic_across_modules():
    """Verify that a single seed call produces consistent sequences across all three modules."""
    seed_value = 101010
    set_seed(seed_value)

    # Generate a sequence from each module
    py_rand = [random.random() for _ in range(3)]
    np_rand = [np.random.rand() for _ in range(3)]

    if TORCH_AVAILABLE:
        torch_rand = torch.rand(3).tolist()

    # Reset and regenerate
    set_seed(seed_value)
    py_rand_2 = [random.random() for _ in range(3)]
    np_rand_2 = [np.random.rand() for _ in range(3)]

    if TORCH_AVAILABLE:
        torch_rand_2 = torch.rand(3).tolist()

    # Verify consistency
    assert py_rand == py_rand_2, "Python random sequence mismatch."
    np.testing.assert_array_almost_equal(np_rand, np_rand_2)

    if TORCH_AVAILABLE:
        assert torch_rand == torch_rand_2, "Torch random sequence mismatch."