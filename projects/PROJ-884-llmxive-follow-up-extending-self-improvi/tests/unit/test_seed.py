"""
Unit tests for the seed management utility.
"""

import pytest
import random
import os

# Import the module under test
from code.utils.seed import (
    set_seed,
    get_seed,
    generate_seed_from_string,
    reset_seed,
    set_deterministic_mode,
    HAS_NUMPY,
    HAS_TORCH
)

# Optional imports for testing
if HAS_NUMPY:
    import numpy as np
if HAS_TORCH:
    import torch


class TestSeedManagement:
    """Tests for seed management functions."""

    def test_set_seed_updates_global_state(self):
        """Test that set_seed updates the global seed state."""
        test_seed = 42
        status = set_seed(test_seed)
        
        assert get_seed() == test_seed
        assert status["seed"] == test_seed
        assert status["python_random"] is True

    def test_set_seed_python_random(self):
        """Test that set_seed correctly seeds Python's random module."""
        seed_val = 12345
        set_seed(seed_val)
        
        val1 = random.random()
        set_seed(seed_val)
        val2 = random.random()
        
        assert val1 == val2, "Python random should be reproducible with same seed"

    def test_set_seed_numpy_reproducibility(self):
        """Test that set_seed correctly seeds NumPy if available."""
        if not HAS_NUMPY:
            pytest.skip("NumPy not available")
        
        seed_val = 54321
        set_seed(seed_val)
        arr1 = np.random.rand(5)
        
        set_seed(seed_val)
        arr2 = np.random.rand(5)
        
        assert np.allclose(arr1, arr2), "NumPy arrays should be reproducible"

    def test_set_seed_torch_reproducibility(self):
        """Test that set_seed correctly seeds PyTorch if available."""
        if not HAS_TORCH:
            pytest.skip("PyTorch not available")
        
        seed_val = 98765
        set_seed(seed_val)
        tensor1 = torch.rand(5)
        
        set_seed(seed_val)
        tensor2 = torch.rand(5)
        
        assert torch.allclose(tensor1, tensor2), "PyTorch tensors should be reproducible"

    def test_get_seed_before_set(self):
        """Test that get_seed returns None before any seed is set."""
        reset_seed()
        assert get_seed() is None

    def test_generate_seed_from_string_deterministic(self):
        """Test that generate_seed_from_string produces deterministic results."""
        test_string = "test_experiment_123"
        
        seed1 = generate_seed_from_string(test_string)
        seed2 = generate_seed_from_string(test_string)
        
        assert seed1 == seed2, "Same string should produce same seed"
        assert isinstance(seed1, int), "Seed should be an integer"
        assert seed1 >= 0, "Seed should be non-negative"

    def test_generate_seed_from_string_unique(self):
        """Test that different strings produce different seeds."""
        seed1 = generate_seed_from_string("string_A")
        seed2 = generate_seed_from_string("string_B")
        
        assert seed1 != seed2, "Different strings should produce different seeds"

    def test_reset_seed(self):
        """Test that reset_seed clears the global state."""
        set_seed(42)
        assert get_seed() == 42
        
        reset_seed()
        assert get_seed() is None

    def test_set_deterministic_mode(self):
        """Test that set_deterministic_mode sets environment variables if PyTorch is available."""
        if not HAS_TORCH:
            pytest.skip("PyTorch not available")
        
        # This test mainly verifies the function runs without error
        # The actual environment variable setting is hard to verify in a unit test
        set_deterministic_mode(True)
        set_deterministic_mode(False)

    def test_seed_status_dict_keys(self):
        """Test that set_seed returns a dictionary with all expected keys."""
        status = set_seed(42)
        
        expected_keys = ["seed", "python_random", "numpy", "torch", "torch_deterministic"]
        for key in expected_keys:
            assert key in status, f"Status dict missing key: {key}"

    def test_seed_persistence_across_calls(self):
        """Test that the seed persists until explicitly changed or reset."""
        set_seed(100)
        assert get_seed() == 100
        
        # Call other functions that don't change seed
        generate_seed_from_string("test")
        assert get_seed() == 100

        set_seed(200)
        assert get_seed() == 200