import os
import random
import numpy as np
import torch
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.config import set_global_seed, get_env_config, init_environment

class TestSeedFixation:
    """Tests for random seed fixation and reproducibility."""

    def test_set_global_seed_affects_random(self):
        """Verify that set_global_seed affects Python's random module."""
        set_global_seed(12345)
        val1 = random.random()
        
        set_global_seed(12345)
        val2 = random.random()
        
        assert val1 == val2, "Random module not properly seeded"

    def test_set_global_seed_affects_numpy(self):
        """Verify that set_global_seed affects NumPy."""
        set_global_seed(54321)
        arr1 = np.random.rand(5)
        
        set_global_seed(54321)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2, "NumPy not properly seeded")

    def test_set_global_seed_affects_torch(self):
        """Verify that set_global_seed affects PyTorch."""
        set_global_seed(99999)
        tensor1 = torch.rand(5)
        
        set_global_seed(99999)
        tensor2 = torch.rand(5)
        
        torch.testing.assert_close(tensor1, tensor2, "PyTorch not properly seeded")

    def test_cudnn_deterministic_flag_set(self):
        """Verify that cudnn deterministic flags are set."""
        set_global_seed(42)
        assert torch.backends.cudnn.deterministic is True
        assert torch.backends.cudnn.benchmark is False

    def test_environment_initialization(self):
        """Test that init_environment properly configures the system."""
        # Clean environment variables for test
        for key in ["DEEPMX_SEED", "DEEPMX_DEVICE", "DEEPMX_LOG_LEVEL", "DEEPMX_DATA_ROOT"]:
            os.environ.pop(key, None)
        
        config = init_environment(seed=77777)
        
        assert config["seed"] == 77777
        assert config["device"] == "cpu"
        assert config["log_level"] == "INFO"

    def test_env_variable_override(self):
        """Test that environment variables override defaults."""
        os.environ["DEEPMX_SEED"] = "11111"
        os.environ["DEEPMX_DEVICE"] = "cuda"
        
        config = init_environment()
        
        assert config["seed"] == 11111
        assert config["device"] == "cuda"
        
        # Clean up
        os.environ.pop("DEEPMX_SEED")
        os.environ.pop("DEEPMX_DEVICE")

    def test_seed_range_validation(self):
        """Test that seeds within valid range work correctly."""
        # Test minimum valid seed
        set_global_seed(0)
        assert torch.backends.cudnn.deterministic is True
        
        # Test maximum valid seed (2^32 - 1)
        set_global_seed(2**32 - 1)
        assert torch.backends.cudnn.deterministic is True

    def test_reproducibility_chain(self):
        """Test that a chain of operations is reproducible."""
        def run_chain(seed):
            set_global_seed(seed)
            r = random.random()
            n = np.random.rand()
            t = torch.rand(1).item()
            return r, n, t
        
        result1 = run_chain(42424)
        result2 = run_chain(42424)
        
        assert result1 == result2, "Chain of operations not reproducible"
