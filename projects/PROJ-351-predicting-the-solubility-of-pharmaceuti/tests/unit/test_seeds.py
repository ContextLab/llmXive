import os
import random
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Import the functions to test
from code.config.seeds import get_seed, set_seed, ensure_seeded, DEFAULT_SEED

class TestGetSeed:
    def test_returns_explicit_seed(self):
        """Test that get_seed returns the explicitly provided seed."""
        assert get_seed(123) == 123
        assert get_seed(0) == 0
        assert get_seed(42) == 42

    def test_returns_default_when_none(self):
        """Test that get_seed returns DEFAULT_SEED when no seed is provided."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_seed(None) == DEFAULT_SEED

    def test_returns_env_seed(self):
        """Test that get_seed reads from RANDOM_SEED environment variable."""
        with patch.dict(os.environ, {"RANDOM_SEED": "999"}):
            assert get_seed(None) == 999

    def test_invalid_env_seed_uses_default(self):
        """Test that invalid RANDOM_SEED falls back to DEFAULT_SEED."""
        with patch.dict(os.environ, {"RANDOM_SEED": "not_a_number"}):
            assert get_seed(None) == DEFAULT_SEED

class TestSetSeed:
    def test_sets_python_random(self):
        """Test that set_seed correctly seeds Python's random module."""
        seed = 42
        set_seed(seed)
        
        # Generate a few random numbers
        val1 = random.random()
        
        # Reset seed and generate again
        set_seed(seed)
        val2 = random.random()
        
        assert val1 == val2

    def test_sets_numpy_random(self):
        """Test that set_seed correctly seeds NumPy's random module."""
        seed = 42
        set_seed(seed)
        
        # Generate a random array
        arr1 = np.random.rand(5)
        
        # Reset seed and generate again
        set_seed(seed)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2)

    def test_sets_pytorch_if_available(self):
        """Test that set_seed seeds PyTorch if installed."""
        seed = 42
        
        try:
            import torch
            torch_available = True
        except ImportError:
            torch_available = False
        
        if torch_available:
            set_seed(seed)
            
            # Generate a random tensor
            tensor1 = torch.rand(5)
            
            # Reset seed and generate again
            set_seed(seed)
            tensor2 = torch.rand(5)
            
            torch.testing.assert_close(tensor1, tensor2)
        else:
            # If PyTorch isn't available, just ensure no exception is raised
            set_seed(seed)

    def test_ensures_deterministic_cudnn_when_cuda_available(self):
        """Test that deterministic CuDNN settings are applied when CUDA is available."""
        try:
            import torch
            if torch.cuda.is_available():
                set_seed(42)
                assert torch.backends.cudnn.deterministic is True
                assert torch.backends.cudnn.benchmark is False
            else:
                # CUDA not available, skip this check
                pass
        except ImportError:
            # PyTorch not installed, skip
            pass

    def test_returns_set_seed(self):
        """Test that set_seed returns the seed value it set."""
        assert set_seed(123) == 123
        assert set_seed(None) == DEFAULT_SEED

class TestEnsureSeeded:
    def test_ensures_seeded(self):
        """Test that ensure_seeded calls set_seed and returns the seed."""
        seed = 42
        result = ensure_seeded(seed)
        assert result == seed
        
        # Verify it actually set the seeds by checking reproducibility
        val1 = random.random()
        val2 = random.random()
        
        ensure_seeded(seed)
        val3 = random.random()
        val4 = random.random()
        
        assert val1 == val3
        assert val2 == val4