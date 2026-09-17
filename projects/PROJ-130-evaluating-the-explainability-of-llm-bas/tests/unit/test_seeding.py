"""
Unit tests for the seeding utility module.
"""
import random
import numpy as np
import torch
import pytest
import os
import sys

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.seeding import set_global_seed, get_config, get_seed


class TestSetGlobalSeed:
    """Tests for set_global_seed function."""

    def test_sets_python_random_seed(self):
        """Test that Python's random module seed is set correctly."""
        seed = 42
        set_global_seed(seed)
        
        # Generate a random number
        val1 = random.random()
        
        # Reset and generate again
        set_global_seed(seed)
        val2 = random.random()
        
        assert val1 == val2, "Python random seed not set correctly"

    def test_sets_numpy_seed(self):
        """Test that NumPy's random seed is set correctly."""
        seed = 123
        set_global_seed(seed)
        
        # Generate a random array
        arr1 = np.random.rand(5)
        
        # Reset and generate again
        set_global_seed(seed)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2, "NumPy random seed not set correctly")

    def test_sets_pytorch_cpu_seed(self):
        """Test that PyTorch CPU seed is set correctly."""
        seed = 456
        set_global_seed(seed)
        
        # Generate a random tensor
        tensor1 = torch.rand(5)
        
        # Reset and generate again
        set_global_seed(seed)
        tensor2 = torch.rand(5)
        
        torch.testing.assert_close(tensor1, tensor2, "PyTorch CPU seed not set correctly")

    def test_sets_pytorch_cuda_seed_if_available(self):
        """Test that PyTorch CUDA seed is set if CUDA is available."""
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available")
        
        seed = 789
        set_global_seed(seed)
        
        # Generate a random tensor on GPU
        tensor1 = torch.rand(5, device='cuda')
        
        # Reset and generate again
        set_global_seed(seed)
        tensor2 = torch.rand(5, device='cuda')
        
        torch.testing.assert_close(tensor1, tensor2, "PyTorch CUDA seed not set correctly")

    def test_sets_cudnn_deterministic(self):
        """Test that cuDNN deterministic mode is enabled."""
        seed = 101
        set_global_seed(seed)
        
        config = get_config()
        assert config["cudnn_deterministic"] is True
        assert torch.backends.cudnn.deterministic is True

    def test_disables_cudnn_benchmark(self):
        """Test that cuDNN benchmark mode is disabled."""
        seed = 202
        set_global_seed(seed)
        
        config = get_config()
        assert config["cudnn_benchmark"] is False
        assert torch.backends.cudnn.benchmark is False

    def test_updates_global_config(self):
        """Test that the global config is updated with seed value."""
        seed = 303
        set_global_seed(seed)
        
        config = get_config()
        assert config["seed"] == seed
        assert config["deterministic"] is True

    def test_multiple_seeds_different_values(self):
        """Test that different seeds produce different random values."""
        set_global_seed(100)
        val1 = random.random()
        
        set_global_seed(200)
        val2 = random.random()
        
        assert val1 != val2, "Different seeds should produce different values"


class TestGetConfig:
    """Tests for get_config function."""

    def test_returns_dict(self):
        """Test that get_config returns a dictionary."""
        config = get_config()
        assert isinstance(config, dict)

    def test_contains_expected_keys(self):
        """Test that config contains expected keys."""
        config = get_config()
        expected_keys = ["seed", "deterministic", "cudnn_benchmark", "cudnn_deterministic"]
        for key in expected_keys:
            assert key in config, f"Missing key: {key}"

    def test_returns_copy(self):
        """Test that get_config returns a copy, not the original."""
        set_global_seed(42)
        config1 = get_config()
        config1["seed"] = 999
        
        config2 = get_config()
        assert config2["seed"] == 42, "get_config should return a copy"

    def test_initial_state(self):
        """Test the initial state before setting a seed."""
        # Reset state if any
        from code.utils import seeding
        seeding._GLOBAL_SEED = None
        seeding._CONFIG = {
            "seed": None,
            "deterministic": False,
            "cudnn_benchmark": False,
            "cudnn_deterministic": False,
        }
        
        config = get_config()
        assert config["seed"] is None
        assert config["deterministic"] is False


class TestGetSeed:
    """Tests for get_seed function."""

    def test_returns_none_when_not_set(self):
        """Test that get_seed returns None when no seed is set."""
        from code.utils import seeding
        seeding._GLOBAL_SEED = None
        
        assert get_seed() is None

    def test_returns_set_seed(self):
        """Test that get_seed returns the set seed."""
        seed = 555
        set_global_seed(seed)
        assert get_seed() == seed

    def test_returns_updated_seed(self):
        """Test that get_seed returns the most recently set seed."""
        set_global_seed(100)
        set_global_seed(200)
        assert get_seed() == 200
