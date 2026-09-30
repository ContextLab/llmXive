import os
import random
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Try to import torch, but handle if not available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from utils.config import set_seed, validate_seed

class TestSeedPinning:
    """Test suite for seed pinning utility functions."""

    def test_validate_seed_valid(self):
        """Test that valid seeds are accepted."""
        assert validate_seed(1) is True
        assert validate_seed(42) is True
        assert validate_seed(12345) is True

    def test_validate_seed_invalid(self):
        """Test that invalid seeds are rejected."""
        assert validate_seed(0) is False
        assert validate_seed(-1) is False
        assert validate_seed(3.14) is False
        assert validate_seed("42") is False

    def test_set_seed_python(self):
        """Test that set_seed affects Python's random module."""
        set_seed(42)
        val1 = random.random()
        
        set_seed(42)
        val2 = random.random()
        
        assert val1 == val2

    def test_set_seed_numpy(self):
        """Test that set_seed affects NumPy's random module."""
        set_seed(42)
        arr1 = np.random.rand(3, 3)
        
        set_seed(42)
        arr2 = np.random.rand(3, 3)
        
        np.testing.assert_array_equal(arr1, arr2)

    def test_set_seed_python_hash_env(self):
        """Test that set_seed sets the PYTHONHASHSEED environment variable."""
        seed = 42
        set_seed(seed)
        assert os.environ.get('PYTHONHASHSEED') == str(seed)

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not installed")
    def test_set_seed_torch_cpu(self):
        """Test that set_seed affects PyTorch's CPU random state."""
        set_seed(42)
        t1 = torch.rand(2, 2)
        
        set_seed(42)
        t2 = torch.rand(2, 2)
        
        assert torch.equal(t1, t2)

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not installed")
    def test_set_seed_torch_cuda(self):
        """Test that set_seed affects PyTorch's CUDA random state if available."""
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available")
            
        set_seed(42)
        t1 = torch.cuda.FloatTensor(2, 2).normal_()
        
        set_seed(42)
        t2 = torch.cuda.FloatTensor(2, 2).normal_()
        
        assert torch.equal(t1, t2)

    def test_set_seed_invalid_raises_error(self):
        """Test that set_seed raises ValueError for invalid seeds."""
        with pytest.raises(ValueError):
            set_seed(-1)
        
        with pytest.raises(ValueError):
            set_seed(0)
        
        with pytest.raises(ValueError):
            set_seed("invalid")

    def test_set_seed_deterministic_behavior(self):
        """Test that the full pipeline is deterministic with the same seed."""
        # Set seed and generate a sequence of values from different libraries
        set_seed(123)
        python_val = random.random()
        numpy_val = np.random.rand()
        python_list = [random.random() for _ in range(5)]
        numpy_arr = np.random.rand(3, 3)
        
        # Reset and regenerate
        set_seed(123)
        python_val_2 = random.random()
        numpy_val_2 = np.random.rand()
        python_list_2 = [random.random() for _ in range(5)]
        numpy_arr_2 = np.random.rand(3, 3)
        
        assert python_val == python_val_2
        assert numpy_val == numpy_val_2
        assert python_list == python_list_2
        np.testing.assert_array_equal(numpy_arr, numpy_arr_2)
