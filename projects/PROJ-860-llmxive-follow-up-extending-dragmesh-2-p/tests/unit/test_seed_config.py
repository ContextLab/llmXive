"""
Unit tests for seed configuration and enforcement logic.

These tests verify that:
1. Seeds are correctly retrieved from environment variables
2. Seeds are correctly set for numpy, random, and pybullet
3. Invalid seed values raise appropriate errors
4. Reproducibility is maintained across multiple calls
"""

import os
import random
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

import sys
import importlib

# Ensure we're testing the fresh module
if 'seed_config' in sys.modules:
    del sys.modules['seed_config']

from seed_config import (
    get_seed,
    set_seeds,
    enforce_seed_in_training_loop,
    enforce_seed_in_evaluation_loop,
    enforce_seed_in_generation_loop,
    init_reproducibility,
    DEFAULT_SEED,
    SEED_ENV_VAR
)


class TestGetSeed:
    """Tests for the get_seed function."""

    def test_default_seed_when_no_env_var(self):
        """Test that DEFAULT_SEED is returned when no env var is set."""
        # Ensure env var is not set
        if SEED_ENV_VAR in os.environ:
            del os.environ[SEED_ENV_VAR]

        seed = get_seed()
        assert seed == DEFAULT_SEED

    def test_custom_seed_from_env_var(self):
        """Test that custom seed is retrieved from environment variable."""
        with patch.dict(os.environ, {SEED_ENV_VAR: "12345"}):
            seed = get_seed()
            assert seed == 12345

    def test_invalid_seed_from_env_var_raises_error(self):
        """Test that invalid seed value raises ValueError."""
        with patch.dict(os.environ, {SEED_ENV_VAR: "not_a_number"}):
            with pytest.raises(ValueError, match="Invalid seed value"):
                get_seed()

    def test_negative_seed_from_env_var_raises_error(self):
        """Test that negative seed value raises ValueError during set_seeds."""
        with patch.dict(os.environ, {SEED_ENV_VAR: "-1"}):
            with pytest.raises(ValueError, match="non-negative"):
                set_seeds()


class TestSetSeeds:
    """Tests for the set_seeds function."""

    def test_sets_numpy_seed(self):
        """Test that numpy random seed is set correctly."""
        seed = 42
        set_seeds(seed)

        # Generate a random number
        val1 = np.random.random()

        # Reset seed and generate again
        np.random.seed(seed)
        val2 = np.random.random()

        assert val1 == val2

    def test_sets_python_random_seed(self):
        """Test that Python random module seed is set correctly."""
        seed = 42
        set_seeds(seed)

        # Generate a random number
        val1 = random.random()

        # Reset seed and generate again
        random.seed(seed)
        val2 = random.random()

        assert val1 == val2

    def test_sets_pybullet_seed(self):
        """Test that pybullet seed is attempted to be set."""
        seed = 42
        set_seeds(seed)

        # Check that the environment variable was set
        assert os.environ.get("PYBULLET_ENABLE_Deterministic") == "1"

    def test_returns_correct_seed(self):
        """Test that the function returns the seed that was set."""
        seed = 999
        result = set_seeds(seed)
        assert result == seed

    def test_uses_default_seed_when_none_provided(self):
        """Test that DEFAULT_SEED is used when None is provided."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing seed env var
            if SEED_ENV_VAR in os.environ:
                del os.environ[SEED_ENV_VAR]

            result = set_seeds(None)
            assert result == DEFAULT_SEED

    def test_invalid_seed_type_raises_error(self):
        """Test that invalid seed type raises ValueError."""
        with pytest.raises(ValueError, match="non-negative integer"):
            set_seeds("not_an_int")

    def test_negative_seed_raises_error(self):
        """Test that negative seed raises ValueError."""
        with pytest.raises(ValueError, match="non-negative integer"):
            set_seeds(-1)


class TestEnforceSeedFunctions:
    """Tests for the enforce_seed_* functions."""

    def test_enforce_seed_in_training_loop(self):
        """Test that training loop seed enforcement works."""
        seed = 123
        with patch('seed_config.set_seeds', return_value=seed) as mock_set:
            result = enforce_seed_in_training_loop()
            mock_set.assert_called_once()
            assert result == seed

    def test_enforce_seed_in_evaluation_loop(self):
        """Test that evaluation loop seed enforcement works."""
        seed = 456
        with patch('seed_config.set_seeds', return_value=seed) as mock_set:
            result = enforce_seed_in_evaluation_loop()
            mock_set.assert_called_once()
            assert result == seed

    def test_enforce_seed_in_generation_loop(self):
        """Test that generation loop seed enforcement works."""
        seed = 789
        with patch('seed_config.set_seeds', return_value=seed) as mock_set:
            result = enforce_seed_in_generation_loop()
            mock_set.assert_called_once()
            assert result == seed


class TestReproducibility:
    """Tests for reproducibility across multiple runs."""

    def test_reproducible_numpy_results(self):
        """Test that numpy results are reproducible with same seed."""
        seed = 42

        # First run
        set_seeds(seed)
        arr1 = np.random.randn(100)

        # Second run with same seed
        set_seeds(seed)
        arr2 = np.random.randn(100)

        np.testing.assert_array_equal(arr1, arr2)

    def test_reproducible_random_results(self):
        """Test that random module results are reproducible with same seed."""
        seed = 42

        # First run
        set_seeds(seed)
        vals1 = [random.random() for _ in range(100)]

        # Second run with same seed
        set_seeds(seed)
        vals2 = [random.random() for _ in range(100)]

        assert vals1 == vals2

    def test_init_reproducibility(self):
        """Test the init_reproducibility convenience function."""
        seed = 999
        with patch('seed_config.set_seeds', return_value=seed) as mock_set:
            result = init_reproducibility()
            mock_set.assert_called_once()
            assert result == seed


class TestEnvironmentVariableHandling:
    """Tests for environment variable handling."""

    def test_env_var_override(self):
        """Test that environment variable overrides default."""
        with patch.dict(os.environ, {SEED_ENV_VAR: "777"}):
            # Clear module cache to force re-read
            if 'seed_config' in sys.modules:
                del sys.modules['seed_config']
            from seed_config import get_seed

            seed = get_seed()
            assert seed == 777

    def test_empty_env_var_uses_default(self):
        """Test that empty env var falls back to default."""
        with patch.dict(os.environ, {SEED_ENV_VAR: ""}):
            # This should raise an error because "" is not a valid int
            with pytest.raises(ValueError):
                get_seed()

    def test_env_var_with_whitespace(self):
        """Test that whitespace in env var is handled."""
        with patch.dict(os.environ, {SEED_ENV_VAR: "  42  "}):
            # This should raise an error because "  42  " is not directly convertible
            # unless we strip it, but our implementation doesn't strip
            with pytest.raises(ValueError):
                get_seed()