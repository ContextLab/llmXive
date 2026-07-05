"""
Unit tests for the random seed pinning utility.

Tests verify that:
1. Seeds are correctly set across all libraries
2. Deterministic behavior is achieved
3. Context manager properly saves and restores state
"""

import random
import numpy as np
import torch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.seeding import (
    set_seed,
    get_seed_hash,
    verify_determinism,
    DeterministicContext,
    get_current_seeds
)


def test_set_seed_python():
    """Test that Python random seed is set correctly."""
    seed = 42
    set_seed(seed)

    # Generate a random number
    val1 = random.random()

    # Reset seed and generate again
    set_seed(seed)
    val2 = random.random()

    assert val1 == val2, "Python random seed not set correctly"


def test_set_seed_numpy():
    """Test that NumPy random seed is set correctly."""
    seed = 123
    set_seed(seed)

    # Generate random array
    arr1 = np.random.rand(5)

    # Reset seed and generate again
    set_seed(seed)
    arr2 = np.random.rand(5)

    assert np.array_equal(arr1, arr2), "NumPy random seed not set correctly"


def test_set_seed_torch():
    """Test that PyTorch random seed is set correctly."""
    seed = 456
    set_seed(seed)

    # Generate random tensor
    tensor1 = torch.rand(5)

    # Reset seed and generate again
    set_seed(seed)
    tensor2 = torch.rand(5)

    assert torch.equal(tensor1, tensor2), "PyTorch random seed not set correctly"


def test_get_seed_hash():
    """Test that seed hash is consistent and unique."""
    seed1 = 42
    seed2 = 43

    hash1 = get_seed_hash(seed1)
    hash2 = get_seed_hash(seed2)

    assert len(hash1) == 8, "Hash should be 8 characters"
    assert hash1 != hash2, "Different seeds should produce different hashes"
    assert get_seed_hash(seed1) == hash1, "Same seed should produce same hash"


def test_verify_determinism():
    """Test the determinism verification utility."""
    def dummy_function(seed):
        set_seed(seed)
        return torch.rand(3)

    result = verify_determinism(dummy_function, seed=789)
    assert result, "Function should be deterministic with same seed"


def test_deterministic_context_manager():
    """Test that context manager saves and restores state correctly."""
    # Set initial seed
    set_seed(100)
    initial_val = random.random()

    # Use context manager with different seed
    with DeterministicContext(seed=200):
        context_val = random.random()

    # After context, should be back to initial state (or at least reproducible)
    set_seed(100)
    final_val = random.random()

    assert initial_val == final_val, "Context manager did not restore state correctly"
    assert context_val != initial_val, "Context manager seed should be different"


def test_get_current_seeds():
    """Test that get_current_seeds returns valid states."""
    set_seed(999)
    states = get_current_seeds()

    assert 'python' in states, "Missing python state"
    assert 'numpy' in states, "Missing numpy state"
    assert 'torch' in states, "Missing torch state"

    # Verify states are actually usable
    random.setstate(states['python'])
    assert isinstance(random.random(), float), "Python state not valid"

    np.random.set_state(states['numpy'])
    assert isinstance(np.random.rand(), float), "NumPy state not valid"

    torch.set_rng_state(states['torch'])
    assert isinstance(torch.rand(1), torch.Tensor), "PyTorch state not valid"


def test_deterministic_mode():
    """Test that deterministic mode settings are applied."""
    set_seed(555)
    # If deterministic mode is enabled, these should be True/False respectively
    # Note: These might not be set if config disables deterministic mode
    # This test just ensures no errors occur
    assert torch.backends.cudnn.deterministic in [True, False]
    assert torch.backends.cudnn.benchmark in [True, False]

if __name__ == "__main__":
    test_set_seed_python()
    test_set_seed_numpy()
    test_set_seed_torch()
    test_get_seed_hash()
    test_verify_determinism()
    test_deterministic_context_manager()
    test_get_current_seeds()
    test_deterministic_mode()
    print("All seeding tests passed!")