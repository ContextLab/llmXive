"""
Unit tests for the configuration module (src/config.py).

Verifies:
- SEED is defined as 42.
- set_rng_seed correctly initializes random and numpy RNGs.
- get_config_summary returns expected keys.
- Seeding produces deterministic results.
"""

import random
import numpy as np
import pytest
from pathlib import Path
import sys

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.config import SEED, set_rng_seed, get_config_summary


class TestConfigConstants:
    """Test that core constants are defined correctly."""

    def test_seed_is_42(self):
        """Verify SEED is exactly 42."""
        assert SEED == 42, f"Expected SEED to be 42, got {SEED}"

    def test_p_value_tolerance_defined(self):
        """Verify P_VALUE_TOLERANCE exists and is reasonable."""
        from src.config import P_VALUE_TOLERANCE
        assert P_VALUE_TOLERANCE == 0.05

    def test_effect_size_tolerance_defined(self):
        """Verify EFFECT_SIZE_TOLERANCE exists and is reasonable."""
        from src.config import EFFECT_SIZE_TOLERANCE
        assert EFFECT_SIZE_TOLERANCE == 0.05

    def test_resource_limits_defined(self):
        """Verify resource limits are defined."""
        from src.config import MAX_MEMORY_GB, MAX_CPU_PERCENT
        assert MAX_MEMORY_GB == 2.0
        assert MAX_CPU_PERCENT == 100.0

    def test_monte_carlo_settings_defined(self):
        """Verify Monte Carlo settings are defined."""
        from src.config import MONTE_CARLO_N_REPLICATES, MONTE_CARLO_P_VALUE_TOLERANCE
        assert MONTE_CARLO_N_REPLICATES == 100000
        assert MONTE_CARLO_P_VALUE_TOLERANCE == 0.005

    def test_get_config_summary_keys(self):
        """Verify get_config_summary returns expected keys."""
        summary = get_config_summary()
        expected_keys = [
            "seed", "p_value_tolerance", "effect_size_tolerance",
            "max_memory_gb", "max_cpu_percent", "monte_carlo_replicates",
            "monte_carlo_tolerance", "min_corpus_size"
        ]
        for key in expected_keys:
            assert key in summary, f"Missing key '{key}' in config summary"
        assert summary["seed"] == 42


class TestRNGSeeding:
    """Test that set_rng_seed correctly initializes RNGs."""

    def test_set_rng_seed_initializes_random(self):
        """Verify random module is seeded."""
        set_rng_seed(12345)
        val1 = random.random()
        
        set_rng_seed(12345)
        val2 = random.random()
        
        assert val1 == val2, "random.random() should be deterministic after seeding"

    def test_set_rng_seed_initializes_numpy(self):
        """Verify numpy is seeded."""
        set_rng_seed(54321)
        arr1 = np.random.rand(5)
        
        set_rng_seed(54321)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2, "numpy random should be deterministic")

    def test_set_rng_seed_default_uses_config_seed(self):
        """Verify calling set_rng_seed() without args uses SEED (42)."""
        # Reset to a known bad state
        random.seed(999)
        np.random.seed(999)
        
        # Call without args
        set_rng_seed()
        
        # Generate a value
        val = random.random()
        
        # Reset and regenerate with explicit 42
        random.seed(42)
        val_expected = random.random()
        
        assert val == val_expected, "Default seed should match SEED (42)"

    def test_deterministic_sequence(self):
        """Verify a sequence of random calls is reproducible."""
        set_rng_seed(42)
        seq1 = [random.random() for _ in range(10)]
        
        set_rng_seed(42)
        seq2 = [random.random() for _ in range(10)]
        
        assert seq1 == seq2, "Sequences should be identical with same seed"

    def test_numpy_and_random_independent_but_seeded(self):
        """Verify both RNGs are seeded independently but consistently."""
        set_rng_seed(777)
        r_val = random.random()
        n_val = np.random.rand()
        
        set_rng_seed(777)
        r_val_2 = random.random()
        n_val_2 = np.random.rand()
        
        assert r_val == r_val_2
        assert n_val == n_val_2