import pytest
import os
import sys
from pathlib import Path
import numpy as np
from src.utils.seeds import (
    SeedManager,
    set_global_seed,
    get_master_seed,
    generate_component_seed,
    get_rng,
    init_simulation_seed
)
from src.utils.config import GLOBAL_SEED

class TestGetMasterSeed:
    def test_default_seed_from_config(self):
        """Test that default master seed comes from GLOBAL_SEED constant."""
        # Reset state if needed (though in isolated test env this might not be needed)
        SeedManager._master_seed = None
        seed = get_master_seed()
        assert seed == GLOBAL_SEED

    def test_master_seed_persistence(self):
        """Test that setting the seed persists."""
        SeedManager._master_seed = 12345
        assert get_master_seed() == 12345
        SeedManager._master_seed = None  # Reset

class TestGenerateComponentSeed:
    def test_deterministic_generation(self):
        """Test that component seeds are deterministic."""
        SeedManager._master_seed = 42
        seed1 = generate_component_seed("test_module")
        seed2 = generate_component_seed("test_module")
        assert seed1 == seed2
        assert isinstance(seed1, int)
        assert seed1 != 42  # Should be different from master
        SeedManager._master_seed = None

    def test_different_components_different_seeds(self):
        """Test that different component names yield different seeds."""
        SeedManager._master_seed = 42
        seed_a = generate_component_seed("module_a")
        seed_b = generate_component_seed("module_b")
        assert seed_a != seed_b
        SeedManager._master_seed = None

class TestGetRNG:
    def test_rng_from_master_seed(self):
        """Test RNG generation uses master seed when no component specified."""
        SeedManager._master_seed = 42
        rng = get_rng()
        val1 = rng.random()
        # Reset and generate again
        rng2 = get_rng()
        val2 = rng2.random()
        assert val1 == val2
        SeedManager._master_seed = None

    def test_rng_from_component_seed(self):
        """Test RNG generation uses derived component seed."""
        SeedManager._master_seed = 42
        rng = get_rng("test_comp")
        val = rng.random()
        # Verify determinism
        rng2 = get_rng("test_comp")
        val2 = rng2.random()
        assert val == val2
        SeedManager._master_seed = None

    def test_explicit_seed_override(self):
        """Test that explicit seed overrides derived seed."""
        SeedManager._master_seed = 42
        rng = get_rng(seed=999)
        val = rng.random()
        rng2 = get_rng(seed=999)
        val2 = rng2.random()
        assert val == val2
        SeedManager._master_seed = None

class TestSetGlobalSeed:
    def test_set_and_get(self):
        """Test setting the global seed."""
        set_global_seed(777)
        assert get_master_seed() == 777
        SeedManager._master_seed = None

    def test_set_none_uses_config(self):
        """Test setting seed to None uses GLOBAL_SEED."""
        set_global_seed(None)
        assert get_master_seed() == GLOBAL_SEED
        SeedManager._master_seed = None

class TestInitSimulationSeed:
    def test_initializes_python_and_numpy(self):
        """Test that init_simulation_seed sets both random and numpy seeds."""
        import random
        init_simulation_seed()
        # Run a sequence
        val1 = random.random()
        val2 = np.random.random()

        # Re-initialize and run again
        init_simulation_seed()
        val1_new = random.random()
        val2_new = np.random.random()

        assert val1 == val1_new
        assert val2 == val2_new
        SeedManager._master_seed = None