"""
Unit tests for the seed pinning utility module.
"""

import pytest
import random
import os
from unittest.mock import patch
import numpy as np
from src.utils.seed import (
    get_default_seed,
    set_seed,
    get_seed_hash,
    verify_seed_consistency,
    SeedContext,
    generate_experiment_id,
    get_environment_seeds,
    DEFAULT_SEED
)


class TestSetSeed:
    """Tests for the set_seed function."""

    def test_set_seed_with_explicit_value(self):
        """Test setting seed with an explicit value."""
        test_seed = 12345
        result = set_seed(test_seed)

        assert result == test_seed
        assert random.random() >= 0  # Should not raise
        assert np.random.random() >= 0  # Should not raise

    def test_set_seed_uses_default_when_none(self):
        """Test that set_seed uses DEFAULT_SEED when None is provided."""
        result = set_seed(None)
        assert result == DEFAULT_SEED

    def test_set_seed_affects_random(self):
        """Test that set_seed actually affects random number generation."""
        seed = 99999
        set_seed(seed)
        val1 = random.random()

        set_seed(seed)
        val2 = random.random()

        assert val1 == val2

    def test_set_seed_affects_numpy(self):
        """Test that set_seed actually affects NumPy random generation."""
        seed = 88888
        set_seed(seed)
        val1 = np.random.random()

        set_seed(seed)
        val2 = np.random.random()

        assert val1 == val2

    def test_set_seed_sets_environment_variable(self):
        """Test that set_seed sets PYTHONHASHSEED environment variable."""
        seed = 77777
        set_seed(seed)
        assert os.environ.get('PYTHONHASHSEED') == str(seed)


class TestGetSeedHash:
    """Tests for the get_seed_hash function."""

    def test_get_seed_hash_returns_string(self):
        """Test that get_seed_hash returns a string."""
        hash_result = get_seed_hash(42)
        assert isinstance(hash_result, str)

    def test_get_seed_hash_length(self):
        """Test that the hash has the expected length (16 chars)."""
        hash_result = get_seed_hash(42)
        assert len(hash_result) == 16

    def test_get_seed_hash_deterministic(self):
        """Test that the same seed produces the same hash."""
        hash1 = get_seed_hash(42)
        hash2 = get_seed_hash(42)
        assert hash1 == hash2

    def test_get_seed_hash_unique_for_different_seeds(self):
        """Test that different seeds produce different hashes."""
        hash1 = get_seed_hash(42)
        hash2 = get_seed_hash(43)
        assert hash1 != hash2


class TestVerifySeedConsistency:
    """Tests for the verify_seed_consistency function."""

    def test_all_seeds_match(self):
        """Test verification when all seeds match."""
        seeds = [42, 42, 42]
        assert verify_seed_consistency(seeds, 42) is True

    def test_seeds_dont_match(self):
        """Test verification when seeds don't match."""
        seeds = [42, 43, 42]
        assert verify_seed_consistency(seeds, 42) is False

    def test_empty_seeds_list(self):
        """Test verification with empty seeds list."""
        assert verify_seed_consistency([], 42) is False

    def test_single_seed_match(self):
        """Test verification with a single matching seed."""
        seeds = [42]
        assert verify_seed_consistency(seeds, 42) is True


class TestSeedContext:
    """Tests for the SeedContext context manager."""

    def test_seed_context_sets_seed(self):
        """Test that SeedContext sets the seed within the context."""
        test_seed = 54321
        with SeedContext(test_seed):
            # Verify seed is set by checking if random numbers are reproducible
            val1 = random.random()

        # Outside context, seed should be restored
        with SeedContext(test_seed):
            val2 = random.random()

        assert val1 == val2

    def test_seed_context_restores_state(self):
        """Test that SeedContext restores the original state."""
        original_state = random.getstate()

        with SeedContext(12345):
            pass

        # State should be restored
        assert random.getstate()[1] == original_state[1]

    def test_seed_context_with_numpy(self):
        """Test that SeedContext works with NumPy."""
        test_seed = 67890
        with SeedContext(test_seed):
            val1 = np.random.random()

        with SeedContext(test_seed):
            val2 = np.random.random()

        assert val1 == val2


class TestGenerateExperimentId:
    """Tests for the generate_experiment_id function."""

    def test_generate_experiment_id_returns_string(self):
        """Test that generate_experiment_id returns a string."""
        exp_id = generate_experiment_id(42)
        assert isinstance(exp_id, str)

    def test_generate_experiment_id_contains_prefix(self):
        """Test that the experiment ID contains the prefix."""
        exp_id = generate_experiment_id(42, prefix="test")
        assert exp_id.startswith("test_")

    def test_generate_experiment_id_contains_seed_hash(self):
        """Test that the experiment ID contains the seed hash."""
        exp_id = generate_experiment_id(42)
        expected_hash = get_seed_hash(42)
        assert expected_hash in exp_id

    def test_generate_experiment_id_uses_default_seed(self):
        """Test that generate_experiment_id uses DEFAULT_SEED when None is provided."""
        exp_id = generate_experiment_id(None)
        expected_hash = get_seed_hash(DEFAULT_SEED)
        assert expected_hash in exp_id


class TestGetDefaultSeed:
    """Tests for the get_default_seed function."""

    def test_get_default_seed_returns_int(self):
        """Test that get_default_seed returns an integer."""
        seed = get_default_seed()
        assert isinstance(seed, int)

    def test_get_default_seed_matches_constant(self):
        """Test that get_default_seed matches the DEFAULT_SEED constant."""
        seed = get_default_seed()
        assert seed == DEFAULT_SEED


class TestGetEnvironmentSeeds:
    """Tests for the get_environment_seeds function."""

    def test_get_environment_seeds_returns_dict(self):
        """Test that get_environment_seeds returns a dictionary."""
        seeds = get_environment_seeds()
        assert isinstance(seeds, dict)

    def test_get_environment_seeds_has_expected_keys(self):
        """Test that the returned dict has expected keys."""
        seeds = get_environment_seeds()
        expected_keys = ['python_random', 'numpy_random', 'python_hash_seed']
        assert all(key in seeds for key in expected_keys)

    def test_get_environment_seeds_values_are_valid(self):
        """Test that the returned values are valid."""
        seeds = get_environment_seeds()
        assert isinstance(seeds['python_random'], int)
        assert isinstance(seeds['numpy_random'], int)
        assert isinstance(seeds['python_hash_seed'], str)