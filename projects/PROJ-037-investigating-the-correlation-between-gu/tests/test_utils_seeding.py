"""
Unit tests for seed management.
"""
import pytest
import random
import numpy as np
import os

from code.utils.seeding import SeedManager, set_seed, get_seed_manager

def test_seed_manager_init():
    """Test SeedManager initialization sets seeds."""
    manager = SeedManager(seed=123)

    assert manager.seed == 123
    assert random.randint(0, 100) != random.randint(0, 100)  # Just a sanity check that random works
    # To verify seed actually works, we'd need to reset and check reproducibility
    # But here we just check it doesn't crash

def test_set_seed():
    """Test set_seed function."""
    import code.utils.seeding as seeding_module
    original_manager = seeding_module._global_seed_manager
    seeding_module._global_seed_manager = None

    try:
        manager = set_seed(456)
        assert manager.seed == 456
        assert get_seed_manager() is manager
    finally:
        seeding_module._global_seed_manager = original_manager

def test_seed_reproducibility():
    """Test that setting the same seed produces same results."""
    import code.utils.seeding as seeding_module
    original_manager = seeding_module._global_seed_manager
    seeding_module._global_seed_manager = None

    try:
        set_seed(789)
        val1 = random.random()
        arr1 = np.random.rand(5)

        set_seed(789)
        val2 = random.random()
        arr2 = np.random.rand(5)

        assert val1 == val2
        np.testing.assert_array_equal(arr1, arr2)
    finally:
        seeding_module._global_seed_manager = original_manager
