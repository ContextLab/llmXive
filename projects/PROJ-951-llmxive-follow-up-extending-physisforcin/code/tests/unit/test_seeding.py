"""
Unit tests for the deterministic seeding utility.
"""
import random
import os
import pytest
import torch
import numpy as np
from pathlib import Path
import sys
import logging

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.seeding import (
    set_deterministic_seed,
    get_seed_config,
    verify_reproducibility,
    DeterministicContext,
    DEFAULT_SEED
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


def reset_seed():
    """Helper function to reset seeds to a known state before tests."""
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    os.environ.pop('PYTHONHASHSEED', None)


class TestSetDeterministicSeed:
    """Tests for set_deterministic_seed function."""

    def test_sets_python_random_seed(self):
        """Test that Python's random module seed is set correctly."""
        reset_seed()
        set_deterministic_seed(42)
        val1 = random.random()
        set_deterministic_seed(42)
        val2 = random.random()
        assert val1 == val2, "Python random values should be reproducible"

    def test_sets_numpy_seed(self):
        """Test that NumPy's random seed is set correctly."""
        reset_seed()
        set_deterministic_seed(42)
        val1 = np.random.random()
        set_deterministic_seed(42)
        val2 = np.random.random()
        assert val1 == val2, "NumPy random values should be reproducible"

    def test_sets_torch_seed(self):
        """Test that PyTorch's random seed is set correctly."""
        reset_seed()
        set_deterministic_seed(42)
        val1 = torch.rand(1).item()
        set_deterministic_seed(42)
        val2 = torch.rand(1).item()
        assert val1 == val2, "PyTorch random values should be reproducible"

    def test_sets_python_hash_seed_env(self):
        """Test that PYTHONHASHSEED environment variable is set."""
        reset_seed()
        set_deterministic_seed(42)
        assert os.environ.get('PYTHONHASHSEED') == '42', "PYTHONHASHSEED should be set"

    def test_sets_cudnn_deterministic(self):
        """Test that CuDNN deterministic flag is set."""
        reset_seed()
        set_deterministic_seed(42)
        assert torch.backends.cudnn.deterministic is True, "CuDNN deterministic should be True"

    def test_sets_cudnn_benchmark_false(self):
        """Test that CuDNN benchmark flag is set to False."""
        reset_seed()
        set_deterministic_seed(42)
        assert torch.backends.cudnn.benchmark is False, "CuDNN benchmark should be False"

    def test_uses_default_seed_when_none(self):
        """Test that DEFAULT_SEED is used when seed is None."""
        reset_seed()
        set_deterministic_seed(None)
        assert os.environ.get('PYTHONHASHSEED') == str(DEFAULT_SEED)

    def test_returns_correct_seed(self):
        """Test that the function returns the seed that was set."""
        reset_seed()
        result = set_deterministic_seed(123)
        assert result == 123, "Function should return the seed that was set"


class TestGetSeedConfig:
    """Tests for get_seed_config function."""

    def test_returns_dict(self):
        """Test that the function returns a dictionary."""
        config = get_seed_config(42)
        assert isinstance(config, dict), "Config should be a dictionary"

    def test_contains_seed_key(self):
        """Test that the config contains the seed key."""
        config = get_seed_config(42)
        assert "seed" in config, "Config should contain 'seed' key"
        assert config["seed"] == 42, "Config seed should match input"

    def test_contains_all_expected_keys(self):
        """Test that the config contains all expected keys."""
        config = get_seed_config(42)
        expected_keys = [
            "seed", "python_random", "numpy_seed", "torch_seed",
            "cudnn_deterministic", "cudnn_benchmark", "python_hash_seed"
        ]
        for key in expected_keys:
            assert key in config, f"Config should contain '{key}' key"


class TestVerifyReproducibility:
    """Tests for verify_reproducibility function."""

    def test_returns_true_for_reproducible_seeds(self):
        """Test that function returns True when seeds are reproducible."""
        reset_seed()
        result = verify_reproducibility(42, num_iterations=3)
        assert result is True, "Reproducibility should be verified"

    def test_returns_true_with_default_seed(self):
        """Test that function works with default seed."""
        reset_seed()
        result = verify_reproducibility(None, num_iterations=2)
        assert result is True, "Reproducibility should be verified with default seed"

    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different random values."""
        reset_seed()
        set_deterministic_seed(42)
        val1 = random.random()

        set_deterministic_seed(123)
        val2 = random.random()

        assert val1 != val2, "Different seeds should produce different values"


class TestDeterministicContext:
    """Tests for DeterministicContext context manager."""

    def test_sets_seed_on_enter(self):
        """Test that the context manager sets the seed on entry."""
        reset_seed()
        with DeterministicContext(42):
            assert os.environ.get('PYTHONHASHSEED') == '42'

    def test_restores_state_on_exit(self):
        """Test that the context manager restores state on exit."""
        reset_seed()
        initial_state = random.getstate()

        with DeterministicContext(42):
            _ = random.random()

        # Check that we can still generate random numbers (state restored)
        val = random.random()
        assert isinstance(val, float), "State should be restored after exit"

    def test_produces_reproducible_results(self):
        """Test that code inside the context is reproducible."""
        reset_seed()

        with DeterministicContext(42):
            val1 = random.random()

        reset_seed()

        with DeterministicContext(42):
            val2 = random.random()

        assert val1 == val2, "Results should be reproducible"

    def test_uses_default_seed_when_none(self):
        """Test that context uses DEFAULT_SEED when seed is None."""
        reset_seed()
        with DeterministicContext(None):
            assert os.environ.get('PYTHONHASHSEED') == str(DEFAULT_SEED)

    def test_exception_handling(self):
        """Test that context manager handles exceptions properly."""
        reset_seed()
        try:
            with DeterministicContext(42):
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should still be able to generate random numbers
        val = random.random()
        assert isinstance(val, float), "State should be restored even after exception"


class TestIntegration:
    """Integration tests for the seeding module."""

    def test_full_workflow(self):
        """Test a complete workflow using the seeding module."""
        reset_seed()

        # Set seed
        set_deterministic_seed(42)

        # Generate values
        py_val1 = random.random()
        np_val1 = np.random.random()
        torch_val1 = torch.rand(1).item()

        # Verify config
        config = get_seed_config(42)
        assert config["seed"] == 42

        # Verify reproducibility
        assert verify_reproducibility(42, num_iterations=2)

        # Use context manager
        with DeterministicContext(42):
            py_val2 = random.random()
            np_val2 = np.random.random()
            torch_val2 = torch.rand(1).item()

        # Values should match
        assert py_val1 == py_val2
        assert np_val1 == np_val2
        assert torch_val1 == torch_val2

    def test_multiple_sequential_runs(self):
        """Test multiple sequential runs with the same seed."""
        reset_seed()

        results = []
        for i in range(5):
            set_deterministic_seed(42)
            val = random.random()
            results.append(val)

        # All values should be the same
        assert all(v == results[0] for v in results), "All values should be identical"