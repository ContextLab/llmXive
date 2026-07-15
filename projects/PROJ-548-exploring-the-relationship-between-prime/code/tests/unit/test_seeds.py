"""
Unit tests for the deterministic random seed management system.

These tests verify that:
  1. The master seed is correctly retrieved and set.
  2. Component seeds are deterministic and unique per component.
  3. RNG instances produce reproducible sequences.
  4. The system handles missing configuration gracefully.
"""
import pytest
import os
import sys
from pathlib import Path
from src.utils.seeds import (
    SeedManager,
    get_master_seed,
    generate_component_seed,
    get_rng,
    set_global_seed,
    init_simulation_seed,
    DEFAULT_MASTER_SEED
)
import numpy as np


class TestGetMasterSeed:
    def test_default_master_seed(self):
        """Test that the default master seed is used when none is set."""
        # Ensure no seed is set
        SeedManager._master_seed = None
        os.environ.pop('LLMXIVE_MASTER_SEED', None)

        seed = get_master_seed()
        assert seed == DEFAULT_MASTER_SEED

    def test_explicit_master_seed(self):
        """Test that an explicitly set master seed is returned."""
        SeedManager.set_master_seed(12345)
        assert get_master_seed() == 12345

    def test_env_master_seed(self):
        """Test that the environment variable overrides the default."""
        SeedManager._master_seed = None
        os.environ['LLMXIVE_MASTER_SEED'] = '99999'

        seed = get_master_seed()
        assert seed == 99999
        # Cleanup
        del os.environ['LLMXIVE_MASTER_SEED']


class TestGenerateComponentSeed:
    def test_deterministic_derivation(self):
        """Test that the same component always gets the same seed."""
        SeedManager.set_master_seed(42)

        seed1 = generate_component_seed("cramer")
        seed2 = generate_component_seed("cramer")

        assert seed1 == seed2
        assert isinstance(seed1, int)

    def test_unique_per_component(self):
        """Test that different components get different seeds."""
        SeedManager.set_master_seed(42)

        seed_cramer = generate_component_seed("cramer")
        seed_permutation = generate_component_seed("permutation")

        assert seed_cramer != seed_permutation

    def test_salt_differentiation(self):
        """Test that salt changes the derived seed."""
        SeedManager.set_master_seed(42)

        seed1 = generate_component_seed("test", salt="v1")
        seed2 = generate_component_seed("test", salt="v2")

        assert seed1 != seed2

    def test_master_seed_change_affects_components(self):
        """Test that changing the master seed changes derived component seeds."""
        SeedManager.set_master_seed(42)
        seed_a = generate_component_seed("test")

        SeedManager.set_master_seed(99)
        seed_b = generate_component_seed("test")

        assert seed_a != seed_b


class TestGetRNG:
    def test_reproducible_sequence(self):
        """Test that an RNG produces the same sequence across runs."""
        SeedManager.set_master_seed(42)

        rng1 = get_rng("test_component")
        seq1 = rng1.random(5)

        rng2 = get_rng("test_component")
        seq2 = rng2.random(5)

        assert np.array_equal(seq1, seq2)

    def test_isolation_between_components(self):
        """Test that RNGs for different components are independent."""
        SeedManager.set_master_seed(42)

        rng_a = get_rng("comp_a")
        rng_b = get_rng("comp_b")

        # Consume one value from each
        val_a = rng_a.random()
        val_b = rng_b.random()

        # Reset and regenerate to check independence
        # (Since they are seeded differently, sequences should differ)
        rng_a2 = get_rng("comp_a")
        rng_b2 = get_rng("comp_b")

        # The sequences should not be identical
        seq_a = rng_a2.random(10)
        seq_b = rng_b2.random(10)

        assert not np.array_equal(seq_a, seq_b)

    def test_rng_type(self):
        """Test that the returned object is a numpy Generator."""
        SeedManager.set_master_seed(42)
        rng = get_rng("test")
        assert isinstance(rng, np.random.Generator)


class TestSetGlobalSeed:
    def test_set_explicit_seed(self):
        """Test setting a specific seed."""
        set_global_seed(777)
        assert SeedManager._master_seed == 777

    def test_set_none_uses_default(self):
        """Test that setting None uses the default or env var."""
        SeedManager._master_seed = None
        os.environ.pop('LLMXIVE_MASTER_SEED', None)
        set_global_seed(None)
        assert SeedManager._master_seed == DEFAULT_MASTER_SEED


class TestInitSimulationSeed:
    def test_from_config(self):
        """Test initialization from a config dictionary."""
        config = {"master_seed": 555}
        init_simulation_seed(config)
        assert get_master_seed() == 555

    def test_from_none_uses_default(self):
        """Test initialization with None config uses default."""
        SeedManager._master_seed = None
        os.environ.pop('LLMXIVE_MASTER_SEED', None)
        init_simulation_seed(None)
        assert get_master_seed() == DEFAULT_MASTER_SEED

    def test_from_empty_dict_uses_default(self):
        """Test initialization with empty config uses default."""
        SeedManager._master_seed = None
        os.environ.pop('LLMXIVE_MASTER_SEED', None)
        init_simulation_seed({})
        assert get_master_seed() == DEFAULT_MASTER_SEED
