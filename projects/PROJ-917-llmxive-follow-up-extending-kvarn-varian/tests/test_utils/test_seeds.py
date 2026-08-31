"""
Tests for global random seed management.

These tests verify that set_global_seed correctly initializes
random state across numpy, torch, and the standard random module,
ensuring deterministic behavior.
"""

import random
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

import pytest

from utils.seeds import (
    set_global_seed,
    get_seed,
    reset_seed,
    ensure_seed_set,
    get_seed_info
)


class TestSeedManagement:
    """Test suite for seed management functions."""

    def setup_method(self):
        """Reset seed state before each test."""
        reset_seed()

    def teardown_method(self):
        """Clean up after each test."""
        reset_seed()

    def test_set_global_seed_basic(self):
        """Test that set_global_seed sets the global seed."""
        seed_value = 42
        set_global_seed(seed_value)
        assert get_seed() == seed_value

    def test_set_global_seed_type_error(self):
        """Test that set_global_seed raises TypeError for non-integer seeds."""
        with pytest.raises(TypeError):
            set_global_seed("not an integer")

        with pytest.raises(TypeError):
            set_global_seed(3.14)

    def test_deterministic_numpy(self):
        """Test that numpy operations are deterministic with the same seed."""
        seed = 12345
        set_global_seed(seed)
        arr1 = np.random.rand(100)

        set_global_seed(seed)
        arr2 = np.random.rand(100)

        assert np.allclose(arr1, arr2)

    def test_deterministic_python_random(self):
        """Test that Python random operations are deterministic with the same seed."""
        seed = 54321
        set_global_seed(seed)
        rand1 = [random.random() for _ in range(10)]

        set_global_seed(seed)
        rand2 = [random.random() for _ in range(10)]

        assert rand1 == rand2

    def test_deterministic_torch(self):
        """Test that torch operations are deterministic with the same seed."""
        if not TORCH_AVAILABLE:
            pytest.skip("PyTorch not available")

        seed = 98765
        set_global_seed(seed)
        tensor1 = torch.rand(100)

        set_global_seed(seed)
        tensor2 = torch.rand(100)

        assert torch.allclose(tensor1, tensor2)

    def test_reset_seed(self):
        """Test that reset_seed clears the global seed state."""
        set_global_seed(42)
        assert get_seed() == 42

        reset_seed()
        assert get_seed() is None

    def test_ensure_seed_set_with_existing(self):
        """Test ensure_seed_set when seed is already set."""
        set_global_seed(100)
        result = ensure_seed_set(default_seed=999)
        assert result == 100  # Should keep existing seed

    def test_ensure_seed_set_without_existing(self):
        """Test ensure_seed_set when no seed is set."""
        result = ensure_seed_set(default_seed=777)
        assert result == 777
        assert get_seed() == 777

    def test_get_seed_info(self):
        """Test get_seed_info returns correct information."""
        seed_info = get_seed_info()
        assert "seed" in seed_info
        assert "is_set" in seed_info
        assert "torch_available" in seed_info

        set_global_seed(42)
        seed_info = get_seed_info()
        assert seed_info["seed"] == 42
        assert seed_info["is_set"] is True

    def test_reproducibility_full_pipeline(self):
        """Test full reproducibility by simulating a small pipeline."""
        seed = 42
        set_global_seed(seed)

        # Simulate a small pipeline
        np_array = np.random.rand(10)
        py_random_val = random.random()
        if TORCH_AVAILABLE:
            torch_tensor = torch.rand(10)

        # Reset and run again
        set_global_seed(seed)
        np_array_2 = np.random.rand(10)
        py_random_val_2 = random.random()
        if TORCH_AVAILABLE:
            torch_tensor_2 = torch.rand(10)

        # Verify all match
        assert np.allclose(np_array, np_array_2)
        assert py_random_val == py_random_val_2
        if TORCH_AVAILABLE:
            assert torch.allclose(torch_tensor, torch_tensor_2)