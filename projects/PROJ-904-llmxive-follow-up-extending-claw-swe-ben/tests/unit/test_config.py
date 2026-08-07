"""
Unit tests for the config module (T004).
Tests Constitution Principle I: Deterministic Reproducibility.
"""

import random
import numpy as np
import pytest
import torch

# Import the config module
import sys
import os

# Ensure the code directory is in the path
code_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "projects",
    "PROJ-904-llmxive-follow-up-extending-claw-swe-ben",
    "code"
)
sys.path.insert(0, code_dir)

from config import RANDOM_SEED, set_global_seeds, get_env_var, get_hf_token


class TestRandomSeedConfiguration:
    """Tests for random seed configuration."""

    def test_random_seed_constant_is_defined(self):
        """Test that RANDOM_SEED is defined and is an integer."""
        assert RANDOM_SEED is not None
        assert isinstance(RANDOM_SEED, int)
        # Verify it's a common seed value (42 is standard)
        assert RANDOM_SEED == 42

    def test_set_global_seeds_sets_python_random(self):
        """Test that set_global_seeds affects Python's random module."""
        # Reset seeds first
        set_global_seeds(RANDOM_SEED)

        # Generate a random number
        val1 = random.random()

        # Reset seeds again
        set_global_seeds(RANDOM_SEED)

        # Generate another random number - should be identical
        val2 = random.random()

        assert val1 == val2

    def test_set_global_seeds_sets_numpy_random(self):
        """Test that set_global_seeds affects NumPy's random module."""
        set_global_seeds(RANDOM_SEED)
        arr1 = np.random.rand(5)

        set_global_seeds(RANDOM_SEED)
        arr2 = np.random.rand(5)

        np.testing.assert_array_equal(arr1, arr2)

    def test_set_global_seeds_sets_torch_random(self):
        """Test that set_global_seeds affects PyTorch's random module."""
        set_global_seeds(RANDOM_SEED)
        tensor1 = torch.rand(5)

        set_global_seeds(RANDOM_SEED)
        tensor2 = torch.rand(5)

        torch.testing.assert_close(tensor1, tensor2)

    def test_reproducibility_chain(self):
        """Test a chain of operations produces reproducible results."""
        set_global_seeds(RANDOM_SEED)

        # Simulate a chain of operations
        results = []
        for i in range(3):
            r = random.random()
            n = np.random.rand()
            t = torch.rand(1).item()
            results.append((r, n, t))

        # Reset and run again
        set_global_seeds(RANDOM_SEED)
        results2 = []
        for i in range(3):
            r = random.random()
            n = np.random.rand()
            t = torch.rand(1).item()
            results2.append((r, n, t))

        assert results == results2


class TestEnvironmentVariables:
    """Tests for environment variable handling."""

    def test_get_env_var_with_existing_var(self, monkeypatch):
        """Test get_env_var with an existing environment variable."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        assert get_env_var("TEST_VAR") == "test_value"

    def test_get_env_var_with_missing_var(self, monkeypatch):
        """Test get_env_var with a missing environment variable."""
        # Make sure it's not set
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        assert get_env_var("NONEXISTENT_VAR") is None

    def test_get_env_var_with_default(self, monkeypatch):
        """Test get_env_var with a default value."""
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        assert get_env_var("NONEXISTENT_VAR", "default_value") == "default_value"

    def test_get_hf_token_success(self, monkeypatch):
        """Test get_hf_token when token is set."""
        monkeypatch.setenv("HF_TOKEN", "test_token_123")
        assert get_hf_token() == "test_token_123"

    def test_get_hf_token_missing(self, monkeypatch):
        """Test get_hf_token raises error when token is missing."""
        monkeypatch.delenv("HF_TOKEN", raising=False)
        with pytest.raises(RuntimeError, match="HF_TOKEN"):
            get_hf_token()
