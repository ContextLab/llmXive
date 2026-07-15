import pytest
import random
import numpy as np
import torch
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.seeding import set_deterministic_seed

class TestSeeding:
    """Tests for deterministic seeding functionality."""

    def test_python_random_seed(self):
        """Test that Python random seed is set correctly."""
        set_deterministic_seed(42)
        val1 = random.random()
        
        set_deterministic_seed(42)
        val2 = random.random()
        
        assert val1 == val2, "Python random should be deterministic with same seed"

    def test_numpy_seed(self):
        """Test that NumPy seed is set correctly."""
        set_deterministic_seed(123)
        arr1 = np.random.rand(5)
        
        set_deterministic_seed(123)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2), "NumPy should be deterministic with same seed"

    def test_pytorch_seed(self):
        """Test that PyTorch seed is set correctly."""
        set_deterministic_seed(456)
        tensor1 = torch.rand(5)
        
        set_deterministic_seed(456)
        tensor2 = torch.rand(5)
        
        assert torch.equal(tensor1, tensor2), "PyTorch should be deterministic with same seed"

    def test_environment_variable_set(self):
        """Test that PYTHONHASHSEED environment variable is set."""
        set_deterministic_seed(789)
        assert os.environ.get('PYTHONHASHSEED') == '789', "PYTHONHASHSEED should be set"

    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different results."""
        set_deterministic_seed(111)
        val1 = random.random()
        
        set_deterministic_seed(222)
        val2 = random.random()
        
        assert val1 != val2, "Different seeds should produce different results"

    def test_seed_persists_across_modules(self):
        """Test that seeding affects multiple random sources."""
        set_deterministic_seed(999)
        
        python_val = random.random()
        numpy_val = np.random.rand()
        
        # Reset seed
        set_deterministic_seed(999)
        
        assert random.random() == python_val
        assert np.random.rand() == numpy_val