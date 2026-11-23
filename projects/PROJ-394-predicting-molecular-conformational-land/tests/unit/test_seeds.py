"""
Unit tests for the global seed setting utility.
"""

import random
import os
import pytest
import numpy as np
import torch

from code.utils.seeds import (
    set_global_seed,
    get_seed_environment_variable,
    set_seed_from_environment
)


class TestSeedSetting:
    """Test cases for seed setting functionality."""

    def test_set_global_seed_validates_input(self):
        """Test that non-integer and negative seeds raise ValueError."""
        with pytest.raises(ValueError):
            set_global_seed(-1)

        with pytest.raises(ValueError):
            set_global_seed("42")

        with pytest.raises(ValueError):
            set_global_seed(3.14)

    def test_set_global_seed_sets_python_random(self):
        """Test that Python's random module is seeded correctly."""
        seed = 12345
        set_global_seed(seed)

        # Generate a few random values
        val1 = random.random()
        val2 = random.random()

        # Reset and regenerate
        set_global_seed(seed)
        val3 = random.random()
        val4 = random.random()

        assert val1 == val3
        assert val2 == val4

    def test_set_global_seed_sets_numpy(self):
        """Test that NumPy is seeded correctly."""
        seed = 54321
        set_global_seed(seed)

        arr1 = np.random.rand(3, 3)

        set_global_seed(seed)
        arr2 = np.random.rand(3, 3)

        np.testing.assert_array_equal(arr1, arr2)

    def test_set_global_seed_sets_pytorch(self):
        """Test that PyTorch is seeded correctly."""
        seed = 98765
        set_global_seed(seed)

        tensor1 = torch.rand(3, 3)

        set_global_seed(seed)
        tensor2 = torch.rand(3, 3)

        torch.testing.assert_close(tensor1, tensor2)

    def test_set_global_seed_deterministic_mode(self):
        """Test that deterministic mode sets correct flags."""
        seed = 11111
        set_global_seed(seed, deterministic=True)

        if torch.backends.cudnn.is_available():
            assert torch.backends.cudnn.deterministic is True
            assert torch.backends.cudnn.benchmark is False
        else:
            # If CUDA is not available, the flags may not be set
            # This is acceptable behavior
            pass

    def test_get_seed_environment_variable(self):
        """Test retrieval of seed from environment variable."""
        # Set environment variable
        os.environ['PYTHONHASHSEED'] = '99999'

        seed = get_seed_environment_variable()
        assert seed == 99999

        # Clean up
        del os.environ['PYTHONHASHSEED']

    def test_get_seed_environment_variable_not_set(self):
        """Test retrieval when environment variable is not set."""
        # Ensure it's not set
        if 'PYTHONHASHSEED' in os.environ:
            del os.environ['PYTHONHASHSEED']

        seed = get_seed_environment_variable()
        assert seed is None

    def test_set_seed_from_environment(self):
        """Test setting seed from environment variable."""
        os.environ['PYTHONHASHSEED'] = '77777'

        set_seed_from_environment()

        # Verify the seed was set by generating values
        val1 = random.random()
        np_val1 = np.random.rand()
        torch_val1 = torch.rand(1).item()

        # Reset and regenerate
        set_seed_from_environment()
        val2 = random.random()
        np_val2 = np.random.rand()
        torch_val2 = torch.rand(1).item()

        assert val1 == val2
        assert np_val1 == np_val2
        assert torch_val1 == torch_val2

        # Clean up
        del os.environ['PYTHONHASHSEED']

    def test_set_seed_from_environment_default(self):
        """Test default seed when environment variable is not set."""
        # Ensure it's not set
        if 'PYTHONHASHSEED' in os.environ:
            del os.environ['PYTHONHASHSEED']

        set_seed_from_environment()

        # Should use default seed of 42
        val1 = random.random()
        np_val1 = np.random.rand()
        torch_val1 = torch.rand(1).item()

        # Reset and regenerate
        set_seed_from_environment()
        val2 = random.random()
        np_val2 = np.random.rand()
        torch_val2 = torch.rand(1).item()

        assert val1 == val2
        assert np_val1 == np_val2
        assert torch_val1 == torch_val2

    def test_reproducibility_full_pipeline(self):
        """Test that a simple pipeline produces identical results with same seed."""
        seed = 42

        # First run
        set_global_seed(seed)
        data1 = {
            'random': random.random(),
            'numpy': np.random.rand(5).tolist(),
            'torch': torch.rand(5).tolist()
        }

        # Second run
        set_global_seed(seed)
        data2 = {
            'random': random.random(),
            'numpy': np.random.rand(5).tolist(),
            'torch': torch.rand(5).tolist()
        }

        assert data1['random'] == data2['random']
        assert data1['numpy'] == data2['numpy']
        assert data1['torch'] == data2['torch']