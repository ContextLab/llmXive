"""
Unit tests for T010: Configuration constants and RNG seeding.

Verifies:
1. src/config.py defines SEED = 42.
2. set_rng_seed() correctly seeds random, numpy, and (if available) other RNGs.
3. Re-running set_rng_seed produces deterministic results.
"""
import random
import numpy as np
import pytest
from pathlib import Path

# Ensure we can import the config module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code.src.config import SEED, set_rng_seed, get_config_summary


class TestConfigConstants:
    def test_seed_is_42(self):
        """Verify that the global SEED constant is exactly 42."""
        assert SEED == 42, f"Expected SEED to be 42, got {SEED}"

    def test_config_summary_contains_seed(self):
        """Verify that get_config_summary() returns the seed."""
        summary = get_config_summary()
        assert "seed" in summary
        assert summary["seed"] == 42


class TestRNGSeeding:
    def test_random_seed_determinism(self):
        """Verify that random.seed(42) produces deterministic output."""
        # Reset seed
        set_rng_seed(42)
        val1 = random.random()
        
        # Reset seed again
        set_rng_seed(42)
        val2 = random.random()
        
        assert val1 == val2, "random.random() is not deterministic after seeding"

    def test_numpy_seed_determinism(self):
        """Verify that np.random.seed(42) produces deterministic output."""
        # Reset seed
        set_rng_seed(42)
        arr1 = np.random.rand(5)
        
        # Reset seed again
        set_rng_seed(42)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2), "np.random.rand() is not deterministic after seeding"

    def test_set_rng_seed_applies_to_both(self):
        """Verify that our wrapper seeds both random and numpy."""
        set_rng_seed(12345)
        r_val = random.random()
        n_val = np.random.rand()
        
        set_rng_seed(12345)
        assert random.random() == r_val
        assert np.random.rand() == n_val

    def test_default_seed_usage(self):
        """Verify that calling set_rng_seed() with no args uses SEED (42)."""
        set_rng_seed(999) # Change it first
        set_rng_seed() # Call with default
        
        # Check if it's back to 42 behavior
        val = random.random()
        set_rng_seed(42)
        assert val == random.random(), "Default seed usage did not revert to SEED"
