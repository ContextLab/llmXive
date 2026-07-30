"""
Unit tests for seed management utilities.
"""

import pytest
import random
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.seeds import (
    set_seed,
    generate_seed_from_string,
    get_seed_config,
    apply_seed_config,
    get_seed_environment
)


class TestSetSeed:
    """Tests for the set_seed function."""

    def test_seed_affects_random(self):
        """Test that set_seed affects Python's random module."""
        set_seed(42)
        val1 = random.random()

        set_seed(42)
        val2 = random.random()

        assert val1 == val2

    def test_seed_affects_numpy(self):
        """Test that set_seed affects NumPy."""
        import numpy as np

        set_seed(123)
        arr1 = np.random.rand(5)

        set_seed(123)
        arr2 = np.random.rand(5)

        assert np.array_equal(arr1, arr2)

    def test_seed_affects_torch(self):
        """Test that set_seed affects PyTorch."""
        import torch

        set_seed(456)
        tensor1 = torch.rand(5)

        set_seed(456)
        tensor2 = torch.rand(5)

        assert torch.equal(tensor1, tensor2)

    def test_env_variable_set(self):
        """Test that PYTHONHASHSEED environment variable is set."""
        set_seed(789)
        assert os.environ.get('PYTHONHASHSEED') == '789'


class TestGenerateSeedFromString:
    """Tests for the generate_seed_from_string function."""

    def test_deterministic_output(self):
        """Test that the same string produces the same seed."""
        seed1 = generate_seed_from_string("test_string")
        seed2 = generate_seed_from_string("test_string")
        assert seed1 == seed2

    def test_different_strings_different_seeds(self):
        """Test that different strings produce different seeds."""
        seed1 = generate_seed_from_string("string1")
        seed2 = generate_seed_from_string("string2")
        assert seed1 != seed2

    def test_within_range(self):
        """Test that generated seed is within valid range."""
        seed = generate_seed_from_string("test", max_seed=100)
        assert 0 <= seed <= 100

    def test_hash_consistency(self):
        """Test that SHA-256 hash is used consistently."""
        seed1 = generate_seed_from_string("hello")
        seed2 = generate_seed_from_string("hello")
        assert seed1 == seed2


class TestGetSeedConfig:
    """Tests for the get_seed_config function."""

    def test_provides_seed_key(self):
        """Test that config always contains a 'seed' key."""
        config = get_seed_config()
        assert 'seed' in config

    def test_direct_seed(self):
        """Test config with direct seed value."""
        config = get_seed_config(seed=42)
        assert config['seed'] == 42

    def test_seed_from_string(self):
        """Test config with seed string."""
        config = get_seed_config(seed_string="test")
        assert config['seed_string'] == "test"
        assert isinstance(config['seed'], int)

    def test_default_seed(self):
        """Test that default seed is used when neither is provided."""
        config = get_seed_config()
        assert config['seed'] == 42

    def test_is_deterministic_flag(self):
        """Test that is_deterministic is always True."""
        config = get_seed_config(seed=42)
        assert config['is_deterministic'] is True


class TestApplySeedConfig:
    """Tests for the apply_seed_config function."""

    def test_applies_seed_correctly(self):
        """Test that apply_seed_config sets the correct seed."""
        config = get_seed_config(seed=999)
        result = apply_seed_config(config)
        assert result == 999

    def test_sets_random_state(self):
        """Test that apply_seed_config actually sets the random state."""
        config = get_seed_config(seed=111)
        apply_seed_config(config)
        val1 = random.random()

        apply_seed_config(config)
        val2 = random.random()

        assert val1 == val2

    def test_raises_on_missing_seed(self):
        """Test that ValueError is raised when seed is missing."""
        with pytest.raises(ValueError):
            apply_seed_config({})


class TestGetSeedEnvironment:
    """Tests for the get_seed_environment function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        env = get_seed_environment()
        assert isinstance(env, dict)

    def test_contains_expected_keys(self):
        """Test that all expected keys are present."""
        env = get_seed_environment()
        expected_keys = ['PYTHONHASHSEED', 'CUBLAS_WORKSPACE_CONFIG', 'CUDA_DETERMINISTIC']
        for key in expected_keys:
            assert key in env

    def test_pythonhashseed_reflects_set_seed(self):
        """Test that PYTHONHASHSEED reflects the last set_seed call."""
        set_seed(12345)
        env = get_seed_environment()
        assert env['PYTHONHASHSEED'] == '12345'