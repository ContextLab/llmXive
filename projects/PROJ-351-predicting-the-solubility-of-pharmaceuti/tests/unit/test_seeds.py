"""
Unit tests for random seed configuration management.

These tests verify that the seed configuration utilities work correctly
and set seeds for all relevant random number generators.
"""
import os
import random
import numpy as np
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config.seeds import get_seed, set_seed, ensure_seeded, DEFAULT_SEED, SEED_ENV_VAR


class TestGetSeed:
    """Tests for the get_seed function."""

    def test_explicit_seed_value(self):
        """Test that explicit seed value is returned."""
        assert get_seed(123) == 123
        assert get_seed(0) == 0
        assert get_seed(999999) == 999999

    def test_default_seed_value(self):
        """Test that default seed value is returned when no seed provided."""
        # Clear environment variable to ensure default is used
        original_env = os.environ.get(SEED_ENV_VAR)
        if SEED_ENV_VAR in os.environ:
            del os.environ[SEED_ENV_VAR]
        
        try:
            assert get_seed() == DEFAULT_SEED
        finally:
            # Restore original environment
            if original_env is not None:
                os.environ[SEED_ENV_VAR] = original_env

    def test_environment_variable_seed(self):
        """Test that environment variable seed is used when provided."""
        original_env = os.environ.get(SEED_ENV_VAR)
        os.environ[SEED_ENV_VAR] = "456"
        
        try:
            assert get_seed() == 456
        finally:
            # Restore original environment
            if original_env is not None:
                os.environ[SEED_ENV_VAR] = original_env
            elif SEED_ENV_VAR in os.environ:
                del os.environ[SEED_ENV_VAR]

    def test_explicit_overrides_environment(self):
        """Test that explicit seed value overrides environment variable."""
        original_env = os.environ.get(SEED_ENV_VAR)
        os.environ[SEED_ENV_VAR] = "789"
        
        try:
            assert get_seed(111) == 111
        finally:
            # Restore original environment
            if original_env is not None:
                os.environ[SEED_ENV_VAR] = original_env
            elif SEED_ENV_VAR in os.environ:
                del os.environ[SEED_ENV_VAR]


class TestSetSeed:
    """Tests for the set_seed function."""

    def test_seed_affects_python_random(self):
        """Test that set_seed affects Python's random module."""
        seed_value = 42
        set_seed(seed_value)
        
        # Generate a random number
        val1 = random.random()
        
        # Reset seed and generate again
        set_seed(seed_value)
        val2 = random.random()
        
        assert val1 == val2, "Python random should be reproducible with same seed"

    def test_seed_affects_numpy(self):
        """Test that set_seed affects NumPy's random generator."""
        seed_value = 42
        set_seed(seed_value)
        
        # Generate random numbers
        arr1 = np.random.rand(5)
        
        # Reset seed and generate again
        set_seed(seed_value)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2, "NumPy random should be reproducible with same seed")

    def test_environment_variable_set(self):
        """Test that PYTHONHASHSEED environment variable is set."""
        seed_value = 123
        set_seed(seed_value)
        
        assert os.environ.get(SEED_ENV_VAR) == str(seed_value), \
            f"PYTHONHASHSEED should be set to {seed_value}"

    def test_seed_consistency(self):
        """Test that multiple calls with same seed produce consistent results."""
        seed_value = 999
        
        set_seed(seed_value)
        python_val = random.random()
        numpy_val = np.random.rand()
        
        set_seed(seed_value)
        python_val2 = random.random()
        numpy_val2 = np.random.rand()
        
        assert python_val == python_val2
        assert numpy_val == numpy_val2


class TestEnsureSeeded:
    """Tests for the ensure_seeded function."""

    def test_returns_seed_value(self):
        """Test that ensure_seeded returns the seed value used."""
        seed_value = 777
        result = ensure_seeded(seed_value)
        
        assert result == seed_value, "ensure_seeded should return the seed value"

    def test_sets_all_generators(self):
        """Test that ensure_seeded sets all random number generators."""
        seed_value = 555
        ensure_seeded(seed_value)
        
        # Verify environment variable is set
        assert os.environ.get(SEED_ENV_VAR) == str(seed_value)
        
        # Verify reproducibility
        val1 = random.random()
        np_val1 = np.random.rand()
        
        ensure_seeded(seed_value)
        val2 = random.random()
        np_val2 = np.random.rand()
        
        assert val1 == val2
        assert np_val1 == np_val2

    def test_default_seed_when_none(self):
        """Test that ensure_seeded uses default seed when None is provided."""
        result = ensure_seeded(None)
        assert result == DEFAULT_SEED