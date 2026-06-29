"""
Test suite for random seed pinning functionality (Task T060).

This module verifies that set_global_seed properly seeds all random
number generators and that the seed value 12345 produces reproducible results.
"""
import random
import numpy as np
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline.utils import set_global_seed


class TestSeedPinning:
    """Test cases for seed pinning functionality."""

    def test_set_global_seed_initializes_random(self):
        """Verify that set_global_seed seeds Python's random module."""
        # Set seed and generate a value
        set_global_seed(12345)
        val1 = random.random()

        # Reset seed and generate again
        set_global_seed(12345)
        val2 = random.random()

        # Values should be identical
        assert val1 == val2, f"Random values not reproducible: {val1} != {val2}"

    def test_set_global_seed_initializes_numpy(self):
        """Verify that set_global_seed seeds NumPy's random module."""
        # Set seed and generate array
        set_global_seed(12345)
        arr1 = np.random.rand(5)

        # Reset seed and generate again
        set_global_seed(12345)
        arr2 = np.random.rand(5)

        # Arrays should be identical
        assert np.array_equal(arr1, arr2), f"NumPy arrays not reproducible:\n{arr1}\n!=\n{arr2}"

    def test_set_global_seed_deterministic_sequence(self):
        """Verify that a sequence of random calls is reproducible."""
        set_global_seed(12345)
        sequence1 = [random.random() for _ in range(10)]

        set_global_seed(12345)
        sequence2 = [random.random() for _ in range(10)]

        assert sequence1 == sequence2, "Random sequence not reproducible"

    def test_set_global_seed_with_numpy_sequence(self):
        """Verify that NumPy random sequences are reproducible."""
        set_global_seed(12345)
        sequence1 = np.random.randn(100).tolist()

        set_global_seed(12345)
        sequence2 = np.random.randn(100).tolist()

        assert sequence1 == sequence2, "NumPy random sequence not reproducible"

    def test_different_seeds_produce_different_results(self):
        """Verify that different seeds produce different random values."""
        set_global_seed(12345)
        val1 = random.random()

        set_global_seed(54321)
        val2 = random.random()

        assert val1 != val2, "Different seeds should produce different values"

    def test_numpy_different_seeds_produce_different_results(self):
        """Verify that different seeds produce different NumPy random arrays."""
        set_global_seed(12345)
        arr1 = np.random.rand(5)

        set_global_seed(54321)
        arr2 = np.random.rand(5)

        assert not np.array_equal(arr1, arr2), "Different seeds should produce different arrays"

    def test_utils_module_uses_default_seed(self):
        """Verify that utils.py seeds itself at import time (T060 requirement)."""
        # Re-import to check if seed was set at module level
        # The set_global_seed(12345) call at module start should have executed
        import importlib
        import pipeline.utils

        # Generate a value using the seeded state
        val1 = random.random()

        # Reset and regenerate
        set_global_seed(12345)
        val2 = random.random()

        # The value from import should match the value from explicit seed reset
        # This verifies the module-level seed call worked
        assert val1 == val2, "Module-level seed pinning not working correctly"
