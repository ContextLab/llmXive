"""
Unit tests for the seed pinning utility (src/utils/seed.py).
"""
import pytest
import random
import os
from unittest.mock import patch

import numpy as np

# Import the module under test
from src.utils.seed import (
    set_seed,
    get_seed_hash,
    verify_seed_consistency,
    SeedContext,
    generate_experiment_id,
    get_default_seed,
    DEFAULT_SEED
)


class TestSetSeed:
    """Tests for the set_seed function."""

    def test_set_seed_validates_input(self):
        """Test that invalid seed values raise ValueError."""
        with pytest.raises(ValueError):
            set_seed(-1)
        with pytest.raises(ValueError):
            set_seed(3.14)
        with pytest.raises(ValueError):
            set_seed("42")

    def test_set_seed_python_random(self):
        """Test that Python's random module is seeded correctly."""
        seed = 12345
        set_seed(seed, verbose=False)
        val1 = random.random()

        set_seed(seed, verbose=False)
        val2 = random.random()

        assert val1 == val2, "Python random should be reproducible with same seed"

    def test_set_seed_numpy(self):
        """Test that NumPy is seeded correctly."""
        seed = 54321
        set_seed(seed, verbose=False)
        arr1 = np.random.random(10)

        set_seed(seed, verbose=False)
        arr2 = np.random.random(10)

        np.testing.assert_array_equal(arr1, arr2, "NumPy should be reproducible with same seed")

    def test_set_seed_returns_results_dict(self):
        """Test that set_seed returns a dictionary with results."""
        result = set_seed(42, verbose=False)
        assert isinstance(result, dict)
        assert 'python_random' in result
        assert 'numpy' in result
        assert result['python_random'] is True
        assert result['numpy'] is True

    def test_set_seed_sets_environment_variable(self):
        """Test that PYTHONHASHSEED is set correctly."""
        seed = 99999
        set_seed(seed, verbose=False)
        assert os.environ.get('PYTHONHASHSEED') == str(seed)


class TestGetSeedHash:
    """Tests for the get_seed_hash function."""

    def test_get_seed_hash_deterministic(self):
        """Test that hash is deterministic for same seed."""
        seed = 42
        hash1 = get_seed_hash(seed)
        hash2 = get_seed_hash(seed)
        assert hash1 == hash2

    def test_get_seed_hash_unique(self):
        """Test that different seeds produce different hashes."""
        hash1 = get_seed_hash(42)
        hash2 = get_seed_hash(43)
        assert hash1 != hash2

    def test_get_seed_hash_format(self):
        """Test that hash is a 16-character hex string."""
        seed = 42
        hash_val = get_seed_hash(seed)
        assert len(hash_val) == 16
        assert all(c in '0123456789abcdef' for c in hash_val)


class TestVerifySeedConsistency:
    """Tests for the verify_seed_consistency function."""

    def test_verify_seed_consistency_returns_true(self):
        """Test that verification passes for valid seed."""
        result = verify_seed_consistency(42, verbose=False)
        assert result is True

    def test_verify_seed_consistency_different_seeds(self):
        """Test that different seeds produce different states."""
        # Set seed 42 and get state
        set_seed(42, verbose=False)
        state1 = random.random()

        # Set seed 43 and get state
        set_seed(43, verbose=False)
        state2 = random.random()

        assert state1 != state2, "Different seeds should produce different states"


class TestSeedContext:
    """Tests for the SeedContext context manager."""

    def test_seed_context_sets_seed(self):
        """Test that context manager sets the seed."""
        with SeedContext(12345):
            val1 = random.random()

        with SeedContext(12345):
            val2 = random.random()

        assert val1 == val2, "Context manager should produce reproducible results"

    def test_seed_context_with_numpy(self):
        """Test that context manager works with NumPy."""
        with SeedContext(54321):
            arr1 = np.random.random(5)

        with SeedContext(54321):
            arr2 = np.random.random(5)

        np.testing.assert_array_equal(arr1, arr2)


class TestGenerateExperimentId:
    """Tests for the generate_experiment_id function."""

    def test_generate_experiment_id_deterministic(self):
        """Test that experiment ID is deterministic."""
        id1 = generate_experiment_id(42, "test_exp")
        id2 = generate_experiment_id(42, "test_exp")
        assert id1 == id2

    def test_generate_experiment_id_unique_for_different_seeds(self):
        """Test that different seeds produce different IDs."""
        id1 = generate_experiment_id(42, "test_exp")
        id2 = generate_experiment_id(43, "test_exp")
        assert id1 != id2

    def test_generate_experiment_id_unique_for_different_names(self):
        """Test that different names produce different IDs."""
        id1 = generate_experiment_id(42, "exp_a")
        id2 = generate_experiment_id(42, "exp_b")
        assert id1 != id2

    def test_generate_experiment_id_without_name(self):
        """Test experiment ID generation without name."""
        id_val = generate_experiment_id(42)
        assert id_val.startswith("exp_s")
        assert len(id_val) > 10  # Should have seed hash


class TestGetDefaultSeed:
    """Tests for the get_default_seed function."""

    def test_get_default_seed_returns_int(self):
        """Test that default seed is an integer."""
        seed = get_default_seed()
        assert isinstance(seed, int)

    def test_get_default_seed_is_42(self):
        """Test that default seed is 42."""
        assert get_default_seed() == 42

    def test_default_seed_constant(self):
        """Test that DEFAULT_SEED constant matches function."""
        assert DEFAULT_SEED == get_default_seed()