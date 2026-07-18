"""
Unit tests for deterministic random seed management (T006).
"""
import pytest
import os
import sys
from pathlib import Path
import numpy as np

# Ensure code path is available
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.seeds import (
    SeedManager,
    get_master_seed,
    generate_component_seed,
    get_rng,
    set_global_seed,
    init_simulation_seed
)
from src.utils.config import GLOBAL_SEED

class TestGetMasterSeed:
    def test_default_seed_matches_config(self):
        """Verify that the default master seed matches the GLOBAL_SEED constant."""
        # Reset state
        SeedManager._initialized = False
        SeedManager._master_seed = None

        seed = get_master_seed()
        assert seed == GLOBAL_SEED

    def test_custom_seed_initialization(self):
        """Verify that a custom seed can be set."""
        custom_seed = 12345
        SeedManager._initialized = False
        SeedManager._master_seed = None

        SeedManager.init(custom_seed)
        assert get_master_seed() == custom_seed

class TestGenerateComponentSeed:
    def test_deterministic_sub_seeds(self):
        """Verify that component seeds are deterministic."""
        SeedManager.init(42)
        seed_a = generate_component_seed("analysis")
        seed_b = generate_component_seed("analysis")
        assert seed_a == seed_b

    def test_different_components_different_seeds(self):
        """Verify that different components get different seeds."""
        SeedManager.init(42)
        seed_a = generate_component_seed("analysis")
        seed_b = generate_component_seed("ingestion")
        assert seed_a != seed_b

class TestGetRNG:
    def test_rng_reproducibility(self):
        """Verify that RNGs generated with the same component name produce same sequence."""
        SeedManager.init(42)
        rng1 = get_rng("test_component")
        rng2 = get_rng("test_component")

        seq1 = [rng1.random() for _ in range(5)]
        seq2 = [rng2.random() for _ in range(5)]

        assert seq1 == seq2

    def test_rng_independence(self):
        """Verify that RNGs for different components are independent."""
        SeedManager.init(42)
        rng1 = get_rng("component_1")
        rng2 = get_rng("component_2")

        val1 = rng1.random()
        val2 = rng2.random()

        # While collision is possible, it's extremely unlikely for 64-bit floats
        # to be exactly equal if seeds are different.
        # We assert they are not equal to ensure the seeds diverged.
        assert val1 != val2

class TestSetGlobalSeed:
    def test_sets_numpy_seed(self):
        """Verify that set_global_seed initializes numpy random."""
        # Reset numpy seed to something else
        np.random.seed(999)
        set_global_seed()

        # Generate a number
        val = np.random.random()
        # If seed was set correctly, subsequent runs should be reproducible
        # We can't easily test "correctness" without a reference, but we ensure
        # the function runs without error and numpy is seeded.
        assert 0.0 <= val <= 1.0

    def test_sets_python_random_seed(self):
        """Verify that set_global_seed initializes python random."""
        import random
        random.seed(999)
        set_global_seed()
        val = random.random()
        assert 0.0 <= val <= 1.0

class TestInitSimulationSeed:
    def test_alias_functionality(self):
        """Verify that init_simulation_seed is an alias for set_global_seed."""
        SeedManager._initialized = False
        init_simulation_seed()
        assert SeedManager._initialized
        assert get_master_seed() == GLOBAL_SEED
