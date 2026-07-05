"""
Unit tests for T010: Configuration constants and RNG seeding.

Verifies:
1. src/config.py defines SEED = 42.
2. set_rng_seed() correctly seeds Python's random and numpy.random.
3. Deterministic output is produced when the seed is set.
"""

import random
import numpy as np
import pytest
from pathlib import Path
import sys

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.config import SEED, set_rng_seed, get_config_summary


class TestConfigConstants:
    """Tests for static configuration constants."""

    def test_seed_is_42(self):
        """Verify that the global SEED constant is 42."""
        assert SEED == 42, f"Expected SEED to be 42, got {SEED}"

    def test_config_summary_contains_seed(self):
        """Verify get_config_summary includes the seed."""
        summary = get_config_summary()
        assert "seed" in summary
        assert summary["seed"] == 42


class TestRNGSeeding:
    """Tests for the set_rng_seed function."""

    def test_set_rng_seed_initializes_random(self):
        """Verify that set_rng_seed initializes Python's random module."""
        # Set seed
        set_rng_seed(SEED)

        # Generate a number
        val1 = random.random()

        # Reset seed
        set_rng_seed(SEED)

        # Generate again
        val2 = random.random()

        # They must be identical
        assert val1 == val2, "Python random module was not seeded correctly."

    def test_set_rng_seed_initializes_numpy(self):
        """Verify that set_rng_seed initializes numpy's random module."""
        # Set seed
        set_rng_seed(SEED)

        # Generate an array
        arr1 = np.random.rand(5)

        # Reset seed
        set_rng_seed(SEED)

        # Generate again
        arr2 = np.random.rand(5)

        # Arrays must be identical
        np.testing.assert_array_equal(arr1, arr2, err_msg="NumPy random module was not seeded correctly.")

    def test_set_rng_seed_custom_value(self):
        """Verify that set_rng_seed accepts a custom seed value."""
        custom_seed = 12345
        set_rng_seed(custom_seed)
        val1 = random.random()

        set_rng_seed(custom_seed)
        val2 = random.random()

        assert val1 == val2, "Custom seed did not produce deterministic results."

    def test_default_seed_uses_config_seed(self):
        """Verify that calling set_rng_seed() without args uses config.SEED."""
        set_rng_seed()  # No args
        val1 = random.random()

        set_rng_seed(SEED)  # Explicitly
        val2 = random.random()

        assert val1 == val2, "Default seed call did not match explicit SEED call."
