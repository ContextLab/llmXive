"""
Unit tests for the configuration module (T010).

Tests verify:
1. SEED constant is defined as 42
2. All expected constants exist with correct types
3. set_rng_seed() function works correctly
4. get_config_summary() returns expected structure
"""

import pytest
import random
from code.src.config import (
    SEED,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_THRESHOLD,
    SAMPLE_SIZE_MINIMUM,
    MIN_SUBGROUP_SIZE,
    MAX_DOMAIN_PROPORTION,
    MAX_CPU_VCPUS,
    MAX_RAM_GB,
    MAX_RUNTIME_HOURS,
    MONTE_CARLO_REPLICATES,
    MONTE_CARLO_TOLERANCE,
    set_rng_seed,
    get_config_summary,
)


class TestConfigConstants:
    """Tests for configuration constant values."""

    def test_seed_is_42(self):
        """Verify SEED is exactly 42 per Constitution Principle I."""
        assert SEED == 42, f"SEED must be 42, got {SEED}"

    def test_seed_is_integer(self):
        """Verify SEED is an integer."""
        assert isinstance(SEED, int), f"SEED must be int, got {type(SEED)}"

    def test_p_value_threshold(self):
        """Verify p-value threshold is 0.05."""
        assert P_VALUE_THRESHOLD == 0.05
        assert isinstance(P_VALUE_THRESHOLD, float)

    def test_effect_size_threshold(self):
        """Verify effect size threshold is 0.05 (5%)."""
        assert EFFECT_SIZE_THRESHOLD == 0.05
        assert isinstance(EFFECT_SIZE_THRESHOLD, float)

    def test_sample_size_minimum(self):
        """Verify minimum sample size is 300."""
        assert SAMPLE_SIZE_MINIMUM == 300
        assert isinstance(SAMPLE_SIZE_MINIMUM, int)

    def test_min_subgroup_size(self):
        """Verify minimum subgroup size is 10."""
        assert MIN_SUBGROUP_SIZE == 10
        assert isinstance(MIN_SUBGROUP_SIZE, int)

    def test_max_domain_proportion(self):
        """Verify max domain proportion is 0.30 (30%)."""
        assert MAX_DOMAIN_PROPORTION == 0.30
        assert isinstance(MAX_DOMAIN_PROPORTION, float)

    def test_max_cpu_vcpus(self):
        """Verify max CPU vCPUs is 2."""
        assert MAX_CPU_VCPUS == 2
        assert isinstance(MAX_CPU_VCPUS, int)

    def test_max_ram_gb(self):
        """Verify max RAM is 2 GB."""
        assert MAX_RAM_GB == 2.0
        assert isinstance(MAX_RAM_GB, float)

    def test_max_runtime_hours(self):
        """Verify max runtime is 6 hours."""
        assert MAX_RUNTIME_HOURS == 6.0
        assert isinstance(MAX_RUNTIME_HOURS, float)

    def test_monte_carlo_replicates(self):
        """Verify Monte Carlo replicates is 10000."""
        assert MONTE_CARLO_REPLICATES == 10000
        assert isinstance(MONTE_CARLO_REPLICATES, int)

    def test_monte_carlo_tolerance(self):
        """Verify Monte Carlo tolerance is 0.005."""
        assert MONTE_CARLO_TOLERANCE == 0.005
        assert isinstance(MONTE_CARLO_TOLERANCE, float)


class TestRNGSeeding:
    """Tests for RNG seeding functionality."""

    def test_set_rng_seed_with_default(self):
        """Verify set_rng_seed uses default SEED when no argument provided."""
        # Generate a random number before seeding
        random.seed(12345)  # Use different seed
        val_before = random.random()

        # Seed with default
        set_rng_seed()

        # Generate after seeding
        val_after = random.random()

        # Should be reproducible
        set_rng_seed()
        val_repro = random.random()

        assert val_after == val_repro, "RNG should be reproducible with same seed"

    def test_set_rng_seed_with_custom(self):
        """Verify set_rng_seed accepts custom seed value."""
        set_rng_seed(999)
        val1 = random.random()

        set_rng_seed(999)
        val2 = random.random()

        assert val1 == val2, "Custom seed should produce reproducible results"

    def test_random_reproducibility(self):
        """Verify that random numbers are reproducible with SEED."""
        set_rng_seed(SEED)
        vals1 = [random.random() for _ in range(10)]

        set_rng_seed(SEED)
        vals2 = [random.random() for _ in range(10)]

        assert vals1 == vals2, "Random sequences should be identical"


class TestConfigSummary:
    """Tests for get_config_summary function."""

    def test_summary_returns_dict(self):
        """Verify get_config_summary returns a dictionary."""
        summary = get_config_summary()
        assert isinstance(summary, dict)

    def test_summary_contains_seed(self):
        """Verify summary contains SEED key."""
        summary = get_config_summary()
        assert "SEED" in summary
        assert summary["SEED"] == 42

    def test_summary_contains_all_thresholds(self):
        """Verify summary contains all threshold constants."""
        summary = get_config_summary()
        required_keys = [
            "P_VALUE_THRESHOLD",
            "EFFECT_SIZE_THRESHOLD",
            "SAMPLE_SIZE_MINIMUM",
            "MIN_SUBGROUP_SIZE",
            "MAX_DOMAIN_PROPORTION",
            "MAX_CPU_VCPUS",
            "MAX_RAM_GB",
            "MAX_RUNTIME_HOURS",
            "MONTE_CARLO_REPLICATES",
            "MONTE_CARLO_TOLERANCE",
        ]
        for key in required_keys:
            assert key in summary, f"Summary missing key: {key}"

    def test_summary_values_match_constants(self):
        """Verify summary values match module constants."""
        summary = get_config_summary()
        assert summary["SEED"] == SEED
        assert summary["P_VALUE_THRESHOLD"] == P_VALUE_THRESHOLD
        assert summary["EFFECT_SIZE_THRESHOLD"] == EFFECT_SIZE_THRESHOLD
        assert summary["SAMPLE_SIZE_MINIMUM"] == SAMPLE_SIZE_MINIMUM
        assert summary["MAX_CPU_VCPUS"] == MAX_CPU_VCPUS
        assert summary["MAX_RAM_GB"] == MAX_RAM_GB
        assert summary["MONTE_CARLO_REPLICATES"] == MONTE_CARLO_REPLICATES
        assert summary["MONTE_CARLO_TOLERANCE"] == MONTE_CARLO_TOLERANCE


class TestImportability:
    """Tests ensuring config module can be imported correctly."""

    def test_config_module_importable(self):
        """Verify config module is importable."""
        from code.src import config
        assert config is not None

    def test_all_public_names_importable(self):
        """Verify all public names can be imported."""
        from code.src.config import (
            SEED,
            P_VALUE_THRESHOLD,
            EFFECT_SIZE_THRESHOLD,
            SAMPLE_SIZE_MINIMUM,
            MIN_SUBGROUP_SIZE,
            MAX_DOMAIN_PROPORTION,
            MAX_CPU_VCPUS,
            MAX_RAM_GB,
            MAX_RUNTIME_HOURS,
            MONTE_CARLO_REPLICATES,
            MONTE_CARLO_TOLERANCE,
            set_rng_seed,
            get_config_summary,
        )
        assert SEED is not None
        assert callable(set_rng_seed)
        assert callable(get_config_summary)