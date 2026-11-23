"""
Unit tests for deterministic seed utilities in code/utils/seed_utils.py.
"""

import os
import random
import hashlib
import pytest
import numpy as np

# Import the module under test
from utils.seed_utils import (
    set_deterministic_seeds,
    get_reproducible_seed_from_string,
    ensure_seed_environment,
)

class TestSetDeterministicSeeds:
    """Tests for set_deterministic_seeds function."""

    def test_sets_python_random_seed(self):
        """Verify that Python's random module is seeded correctly."""
        seed = 12345
        set_deterministic_seeds(seed)

        # Generate two random numbers
        val1 = random.random()
        val2 = random.random()

        # Reset and generate again
        set_deterministic_seeds(seed)
        val3 = random.random()
        val4 = random.random()

        assert val1 == val3
        assert val2 == val4

    def test_sets_numpy_seed(self):
        """Verify that NumPy's random state is seeded correctly."""
        seed = 54321
        set_deterministic_seeds(seed)

        arr1 = np.random.rand(5)
        np.random.seed(seed) # Reset manually to compare
        arr2 = np.random.rand(5)

        # Re-seed using our function to ensure consistency
        set_deterministic_seeds(seed)
        arr3 = np.random.rand(5)

        assert np.array_equal(arr1, arr3)

    def test_returns_correct_status_dict(self):
        """Verify the return dictionary structure and basic status."""
        result = set_deterministic_seeds(42)

        assert "seed" in result
        assert result["seed"] == 42
        assert "python" in result
        assert "numpy" in result
        assert isinstance(result["python"], bool)
        assert isinstance(result["numpy"], bool)
        # Torch and transformers might be False if not installed, but keys must exist
        assert "torch" in result
        assert "transformers" in result

    def test_torch_seeding_if_available(self):
        """Test that torch is seeded if available."""
        try:
            import torch
            TORCH_AVAILABLE = True
        except ImportError:
            TORCH_AVAILABLE = False

        result = set_deterministic_seeds(999)

        if TORCH_AVAILABLE:
            assert result["torch"] is True
            # Verify torch manual seed worked
            t1 = torch.rand(1)
            torch.manual_seed(999)
            t2 = torch.rand(1)
            assert torch.equal(t1, t2)
        else:
            assert result["torch"] is False


class TestGetReproducibleSeedFromString:
    """Tests for get_reproducible_seed_from_string function."""

    def test_deterministic_output(self):
        """Verify same string produces same seed."""
        s1 = get_reproducible_seed_from_string("experiment_A")
        s2 = get_reproducible_seed_from_string("experiment_A")
        assert s1 == s2

    def test_different_string_different_output(self):
        """Verify different strings produce different seeds (high probability)."""
        s1 = get_reproducible_seed_from_string("experiment_A")
        s2 = get_reproducible_seed_from_string("experiment_B")
        # While collisions are theoretically possible, they are extremely unlikely
        # with SHA-256 for distinct short strings.
        assert s1 != s2

    def test_valid_range(self):
        """Verify output is within expected range."""
        seed = get_reproducible_seed_from_string("test_string")
        max_seed = 2**32 - 1
        assert 0 <= seed <= max_seed

    def test_invalid_input_type(self):
        """Verify TypeError is raised for non-string input."""
        with pytest.raises(TypeError):
            get_reproducible_seed_from_string(12345)


class TestEnsureSeedEnvironment:
    """Tests for ensure_seed_environment function."""

    def test_uses_explicit_seed(self):
        """Verify function uses explicitly passed seed."""
        # Clear env var if it exists
        if "LLMXIVE_SEED" in os.environ:
            del os.environ["LLMXIVE_SEED"]

        seed = ensure_seed_environment(seed=777)
        assert seed == 777

        # Verify it actually set the seed by checking random behavior
        val1 = random.random()
        ensure_seed_environment(seed=777)
        val2 = random.random()
        assert val1 == val2

    def test_uses_env_variable(self):
        """Verify function uses LLMXIVE_SEED env var."""
        os.environ["LLMXIVE_SEED"] = "888"

        seed = ensure_seed_environment() # No explicit seed
        assert seed == 888

        # Cleanup
        del os.environ["LLMXIVE_SEED"]

    def test_defaults_to_42(self):
        """Verify function defaults to 42 if no seed provided."""
        if "LLMXIVE_SEED" in os.environ:
            del os.environ["LLMXIVE_SEED"]

        seed = ensure_seed_environment()
        assert seed == 42

    def test_invalid_env_seed_raises_error(self):
        """Verify ValueError is raised for non-integer env seed."""
        os.environ["LLMXIVE_SEED"] = "not_a_number"

        with pytest.raises(ValueError):
            ensure_seed_environment()

        del os.environ["LLMXIVE_SEED"]