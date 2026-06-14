"""
Unit tests for random seed pinning utilities.

Verifies that the seed management system works correctly and that
all seeds are properly tracked for reproducibility.
"""
import pytest
import random
import hashlib
from unittest.mock import patch

# Import from the seeds module
from reproducibility.seeds import (
    SeedConfiguration,
    SeedManager,
    get_seed_manager,
    set_all_seeds,
    generate_seed_from_hash,
    pin_seed_for_module,
    HAS_NUMPY,
)


class TestSeedConfiguration:
    """Tests for SeedConfiguration dataclass."""

    def test_seed_configuration_creation(self):
        """Test basic SeedConfiguration creation."""
        config = SeedConfiguration(
            seed_value=42,
            module="numpy",
            purpose="test",
            description="Testing seed config"
        )
        assert config.seed_value == 42
        assert config.module == "numpy"
        assert config.purpose == "test"
        assert config.description == "Testing seed config"
        # Verify timestamp was set
        assert config.created_at is not None

    def test_seed_configuration_optional_description(self):
        """Test SeedConfiguration with optional description."""
        config = SeedConfiguration(
            seed_value=123,
            module="random",
            purpose="validation"
        )
        assert config.description is None


class TestSeedManager:
    """Tests for SeedManager class."""

    def test_seed_manager_initialization(self):
        """Test SeedManager creates with empty seed list."""
        manager = SeedManager()
        assert manager.seeds == []

    def test_seed_manager_register_seed(self):
        """Test registering a seed returns the configuration."""
        manager = SeedManager()
        config = manager.register_seed(
            seed_value=42,
            module="numpy",
            purpose="test_split"
        )
        assert len(manager.seeds) == 1
        assert config.seed_value == 42
        assert config.module == "numpy"

    def test_seed_manager_get_documentation_empty(self):
        """Test documentation generation with no seeds."""
        manager = SeedManager()
        doc = manager.get_seed_documentation()
        assert "No stochastic operations" in doc
        assert "random seeds" in doc.lower()

    def test_seed_manager_get_documentation_with_seeds(self):
        """Test documentation generation with registered seeds."""
        manager = SeedManager()
        manager.register_seed(42, "numpy", "training", "Test description")
        doc = manager.get_seed_documentation()
        assert "42" in doc
        assert "numpy" in doc
        assert "training" in doc
        assert "Test description" in doc
        # Verify markdown table structure
        assert "|" in doc

    def test_seed_manager_multiple_seeds(self):
        """Test registering multiple seeds."""
        manager = SeedManager()
        manager.register_seed(42, "numpy", "split1")
        manager.register_seed(123, "random", "split2")
        manager.register_seed(456, "torch", "split3")
        assert len(manager.seeds) == 3


class TestGlobalSeedManager:
    """Tests for global seed manager singleton."""

    def test_get_seed_manager_creates_instance(self):
        """Test that get_seed_manager creates an instance."""
        manager = get_seed_manager()
        assert isinstance(manager, SeedManager)

    def test_get_seed_manager_singleton(self):
        """Test that get_seed_manager returns the same instance."""
        manager1 = get_seed_manager()
        manager2 = get_seed_manager()
        assert manager1 is manager2

    def test_get_seed_manager_persists_seeds(self):
        """Test that seeds persist across calls."""
        # Clear the global manager by creating a new one
        import reproducibility.seeds as seeds_module
        seeds_module._seed_manager = None

        manager1 = get_seed_manager()
        manager1.register_seed(42, "test", "persistence")

        manager2 = get_seed_manager()
        assert len(manager2.seeds) == 1
        assert manager2.seeds[0].seed_value == 42


class TestSetAllSeeds:
    """Tests for set_all_seeds function."""

    def test_set_all_seeds_registers_seed(self):
        """Test that set_all_seeds registers the seed."""
        import reproducibility.seeds as seeds_module
        seeds_module._seed_manager = None

        set_all_seeds(seed_value=99, purpose="test")
        manager = get_seed_manager()
        assert len(manager.seeds) == 1
        assert manager.seeds[0].seed_value == 99
        assert manager.seeds[0].module == "all"

    def test_set_all_seeds_sets_random_seed(self):
        """Test that set_all_seeds sets Python's random seed."""
        import reproducibility.seeds as seeds_module
        seeds_module._seed_manager = None

        set_all_seeds(seed_value=42, purpose="test")
        # Generate a number and verify it's deterministic
        val1 = random.random()
        set_all_seeds(seed_value=42, purpose="test")
        val2 = random.random()
        assert val1 == val2

    @pytest.mark.skipif(not HAS_NUMPY, reason="numpy not installed")
    def test_set_all_seeds_sets_numpy_seed(self):
        """Test that set_all_seeds sets numpy's random seed."""
        import numpy as np
        import reproducibility.seeds as seeds_module
        seeds_module._seed_manager = None

        set_all_seeds(seed_value=42, purpose="test")
        val1 = np.random.random()
        set_all_seeds(seed_value=42, purpose="test")
        val2 = np.random.random()
        assert val1 == val2


class TestGenerateSeedFromHash:
    """Tests for generate_seed_from_hash function."""

    def test_generate_seed_from_hash_deterministic(self):
        """Test that hash generation is deterministic."""
        seed1 = generate_seed_from_hash("test_input", "purpose")
        seed2 = generate_seed_from_hash("test_input", "purpose")
        assert seed1 == seed2

    def test_generate_seed_from_hash_different_inputs(self):
        """Test that different inputs produce different seeds."""
        seed1 = generate_seed_from_hash("input1", "purpose")
        seed2 = generate_seed_from_hash("input2", "purpose")
        assert seed1 != seed2

    def test_generate_seed_from_hash_returns_integer(self):
        """Test that the function returns an integer."""
        seed = generate_seed_from_hash("test", "purpose")
        assert isinstance(seed, int)
        assert seed >= 0

    def test_generate_seed_from_hash_consistent_hash(self):
        """Test that the hash is based on SHA-256."""
        # Verify the seed is derived from SHA-256
        input_str = "verification_test"
        expected_hash = hashlib.sha256(input_str.encode()).digest()
        expected_seed = int.from_bytes(expected_hash[:4], byteorder='big')
        actual_seed = generate_seed_from_hash(input_str, "purpose")
        assert actual_seed == expected_seed


class TestPinSeedForModule:
    """Tests for pin_seed_for_module function."""

    def test_pin_seed_for_module_auto_generates_seed(self):
        """Test that pin_seed_for_module generates seed if not provided."""
        import reproducibility.seeds as seeds_module
        seeds_module._seed_manager = None

        seed = pin_seed_for_module("test.module", purpose="test")
        assert isinstance(seed, int)
        assert seed >= 0

    def test_pin_seed_for_module_uses_provided_seed(self):
        """Test that pin_seed_for_module uses provided seed value."""
        import reproducibility.seeds as seeds_module
        seeds_module._seed_manager = None

        seed = pin_seed_for_module("test.module", seed_value=42, purpose="test")
        assert seed == 42

    def test_pin_seed_for_module_registers_seed(self):
        """Test that pin_seed_for_module registers the seed."""
        import reproducibility.seeds as seeds_module
        seeds_module._seed_manager = None

        pin_seed_for_module("test.module", seed_value=42, purpose="test")
        manager = get_seed_manager()
        assert len(manager.seeds) == 1
        assert manager.seeds[0].module == "test.module"
        assert manager.seeds[0].seed_value == 42