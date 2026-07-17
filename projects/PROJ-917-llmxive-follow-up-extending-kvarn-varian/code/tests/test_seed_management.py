"""
Tests for random seed management across all modules.
Ensures reproducibility of random operations.
"""
import pytest
import numpy as np
import random
import os
from pathlib import Path

# Import from the shared utility module
from utils.seed_manager import set_seed, get_seed, reset_seed, ensure_seed_set


class TestSeedManager:
    """Test suite for the seed manager utility."""

    def test_set_seed_initializes_all_rngs(self):
        """Test that set_seed initializes numpy, python random, and os.environ."""
        seed_value = 12345
        set_seed(seed_value)

        # Check that the seed is stored
        assert get_seed() == seed_value

        # Verify numpy reproducibility
        arr1 = np.random.rand(5)
        set_seed(seed_value)
        arr2 = np.random.rand(5)
        assert np.allclose(arr1, arr2), "NumPy RNG not reproducible"

        # Verify Python random reproducibility
        list1 = [random.random() for _ in range(5)]
        set_seed(seed_value)
        list2 = [random.random() for _ in range(5)]
        assert list1 == list2, "Python random RNG not reproducible"

    def test_reset_seed_clears_state(self):
        """Test that reset_seed clears the stored seed state."""
        set_seed(42)
        assert get_seed() == 42

        reset_seed()
        assert get_seed() is None

    def test_ensure_seed_set_uses_default(self):
        """Test that ensure_seed_set sets a default seed if none is set."""
        reset_seed()
        ensure_seed_set()

        # Should have a default seed (typically 42)
        assert get_seed() is not None

    def test_ensure_seed_set_respects_existing(self):
        """Test that ensure_seed_set does not overwrite an existing seed."""
        set_seed(999)
        ensure_seed_set()

        # Should still be 999
        assert get_seed() == 999

    def test_numpy_reproducibility_across_modules(self):
        """Test that numpy operations are reproducible when seed is set."""
        set_seed(54321)
        result1 = np.random.normal(0, 1, 100)

        set_seed(54321)
        result2 = np.random.normal(0, 1, 100)

        assert np.array_equal(result1, result2)

    def test_random_reproducibility_across_modules(self):
        """Test that Python random operations are reproducible when seed is set."""
        set_seed(54321)
        result1 = [random.uniform(0, 1) for _ in range(100)]

        set_seed(54321)
        result2 = [random.uniform(0, 1) for _ in range(100)]

        assert result1 == result2

    def test_seed_persistence(self):
        """Test that the seed persists across multiple calls."""
        set_seed(777)
        assert get_seed() == 777

        # Do some random ops
        _ = np.random.rand(10)
        _ = random.random()

        # Seed should still be 777
        assert get_seed() == 777

    def test_invalid_seed_types(self):
        """Test handling of invalid seed types."""
        with pytest.raises((TypeError, ValueError)):
            set_seed("invalid")

        with pytest.raises((TypeError, ValueError)):
            set_seed(None)  # Although None is handled by reset_seed, explicit invalid check

    def test_large_seed_values(self):
        """Test that large integer seeds work correctly."""
        large_seed = 2**31 - 1
        set_seed(large_seed)
        assert get_seed() == large_seed

        # Should still be reproducible
        arr1 = np.random.rand(5)
        set_seed(large_seed)
        arr2 = np.random.rand(5)
        assert np.allclose(arr1, arr2)
