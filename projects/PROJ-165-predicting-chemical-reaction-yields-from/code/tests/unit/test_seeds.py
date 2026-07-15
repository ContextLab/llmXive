"""
Unit tests for seed management functionality.
"""

import random
import os
import torch
import numpy as np
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.seeds import set_seed, get_seed_env, reset_seeds_to_default, DEFAULT_SEED


class TestSeedManagement:
    """Tests for seed management functions."""

    def test_set_seed_sets_python_random(self):
        """Test that set_seed correctly sets Python's random seed."""
        seed = 12345
        set_seed(seed)

        # Generate a random number
        val1 = random.random()

        # Reset seed and generate again
        set_seed(seed)
        val2 = random.random()

        assert val1 == val2, "Python random should be reproducible with same seed"

    def test_set_seed_sets_numpy(self):
        """Test that set_seed correctly sets NumPy's random seed."""
        seed = 54321
        set_seed(seed)

        # Generate random array
        arr1 = np.random.rand(3, 3)

        # Reset seed and generate again
        set_seed(seed)
        arr2 = np.random.rand(3, 3)

        np.testing.assert_array_equal(arr1, arr2, "NumPy random should be reproducible with same seed")

    def test_set_seed_sets_torch(self):
        """Test that set_seed correctly sets PyTorch's random seed."""
        seed = 98765
        set_seed(seed)

        # Generate random tensor
        tensor1 = torch.rand(3, 3)

        # Reset seed and generate again
        set_seed(seed)
        tensor2 = torch.rand(3, 3)

        torch.testing.assert_close(tensor1, tensor2, "PyTorch random should be reproducible with same seed")

    def test_set_seed_sets_environment_variable(self):
        """Test that set_seed sets the PYTHONHASHSEED environment variable."""
        seed = 11111
        set_seed(seed)

        assert os.environ.get("PYTHONHASHSEED") == str(seed), \
            "PYTHONHASHSEED environment variable should be set"

    def test_set_seed_default(self):
        """Test that set_seed uses DEFAULT_SEED when no argument is provided."""
        set_seed()  # Should use DEFAULT_SEED

        val1 = random.random()

        set_seed()  # Reset to default
        val2 = random.random()

        assert val1 == val2, "Default seed should produce reproducible results"

    def test_get_seed_env_returns_value(self):
        """Test that get_seed_env returns the correct value when PYTHONHASHSEED is set."""
        seed = 22222
        os.environ["PYTHONHASHSEED"] = str(seed)

        result = get_seed_env()
        assert result == seed, f"get_seed_env should return {seed}, got {result}"

    def test_get_seed_env_returns_none_when_not_set(self):
        """Test that get_seed_env returns None when PYTHONHASHSEED is not set."""
        # Remove the environment variable if it exists
        if "PYTHONHASHSEED" in os.environ:
            del os.environ["PYTHONHASHSEED"]

        result = get_seed_env()
        assert result is None, "get_seed_env should return None when PYTHONHASHSEED is not set"

    def test_get_seed_env_returns_none_for_invalid_value(self):
        """Test that get_seed_env returns None for invalid PYTHONHASHSEED value."""
        os.environ["PYTHONHASHSEED"] = "invalid"

        result = get_seed_env()
        assert result is None, "get_seed_env should return None for invalid PYTHONHASHSEED value"

    def test_reset_seeds_to_default(self):
        """Test that reset_seeds_to_default resets to DEFAULT_SEED."""
        # Set a different seed first
        set_seed(99999)
        val1 = random.random()

        # Reset to default
        reset_seeds_to_default()
        val2 = random.random()

        # Reset to default again
        reset_seeds_to_default()
        val3 = random.random()

        assert val2 == val3, "reset_seeds_to_default should produce reproducible results"
        assert val1 != val2, "Different seeds should produce different results"

    def test_cuda_deterministic_flags(self):
        """Test that CUDA deterministic flags are set when CUDA is available."""
        if torch.cuda.is_available():
            set_seed(42)

            assert torch.backends.cudnn.deterministic is True, \
                "cudnn.deterministic should be True"
            assert torch.backends.cudnn.benchmark is False, \
                "cudnn.benchmark should be False"
            assert os.environ.get("CUBLAS_WORKSPACE_CONFIG") == ":4096:8", \
                "CUBLAS_WORKSPACE_CONFIG should be set"
        else:
            # Skip test if CUDA is not available
            pytest.skip("CUDA not available")

    def test_multiple_seeds_produce_different_results(self):
        """Test that different seeds produce different random results."""
        set_seed(1)
        val1 = random.random()

        set_seed(2)
        val2 = random.random()

        assert val1 != val2, "Different seeds should produce different random values"