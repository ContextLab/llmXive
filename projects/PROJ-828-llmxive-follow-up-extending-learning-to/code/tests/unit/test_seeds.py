"""
Unit tests for seed pinning utilities.
"""

import pytest
import random
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.utils.seeds import (
    set_seed,
    generate_seed_from_string,
    get_seed_config,
    apply_seed_config,
    get_seed_environment
)

import numpy as np
import torch


class TestSetSeed:
    """Tests for set_seed function."""

    def test_set_seed_python(self):
        """Test that Python random seed is set correctly."""
        seed = 42
        set_seed(seed, deterministic=False)
        
        # Generate two random numbers
        val1 = random.random()
        
        # Reset seed
        set_seed(seed, deterministic=False)
        val2 = random.random()
        
        assert val1 == val2, "Python random should be reproducible with same seed"

    def test_set_seed_numpy(self):
        """Test that NumPy random seed is set correctly."""
        seed = 42
        set_seed(seed, deterministic=False)
        
        arr1 = np.random.rand(5)
        
        set_seed(seed, deterministic=False)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2, "NumPy random should be reproducible")

    def test_set_seed_torch(self):
        """Test that PyTorch random seed is set correctly."""
        seed = 42
        set_seed(seed, deterministic=False)
        
        t1 = torch.rand(5)
        
        set_seed(seed, deterministic=False)
        t2 = torch.rand(5)
        
        torch.testing.assert_close(t1, t2, "PyTorch random should be reproducible")

    def test_deterministic_mode(self):
        """Test that deterministic mode sets appropriate flags."""
        seed = 42
        set_seed(seed, deterministic=True)
        
        assert torch.backends.cudnn.deterministic is True
        assert torch.backends.cudnn.benchmark is False

    def test_environment_variable_set(self):
        """Test that PYTHONHASHSEED environment variable is set."""
        seed = 42
        with patch.dict(os.environ, {}, clear=True):
            set_seed(seed, deterministic=False)
            assert os.environ.get('PYTHONHASHSEED') == str(seed)


class TestGenerateSeedFromString:
    """Tests for generate_seed_from_string function."""

    def test_generate_seed_from_string(self):
        """Test that string generates consistent seed."""
        seed_str = "test_string"
        seed1 = generate_seed_from_string(seed_str)
        seed2 = generate_seed_from_string(seed_str)
        
        assert seed1 == seed2, "Same string should generate same seed"
        assert isinstance(seed1, int), "Seed should be an integer"
        assert 0 <= seed1 < 2**31, "Seed should be in valid range"

    def test_generate_with_offset(self):
        """Test that offset changes the generated seed."""
        seed_str = "test_string"
        seed1 = generate_seed_from_string(seed_str, offset=0)
        seed2 = generate_seed_from_string(seed_str, offset=1)
        
        assert seed1 != seed2, "Different offsets should generate different seeds"

    def test_different_strings_different_seeds(self):
        """Test that different strings generate different seeds."""
        seed1 = generate_seed_from_string("string1")
        seed2 = generate_seed_from_string("string2")
        
        assert seed1 != seed2, "Different strings should generate different seeds"

    def test_empty_string(self):
        """Test that empty string generates a valid seed."""
        seed = generate_seed_from_string("")
        assert isinstance(seed, int)
        assert 0 <= seed < 2**31


class TestGetSeedConfig:
    """Tests for get_seed_config function."""

    def test_get_seed_config(self):
        """Test that config dictionary is created correctly."""
        config = get_seed_config(base_seed=42, variant_name="opd", run_index=0)
        
        assert config['base_seed'] == 42
        assert config['variant_name'] == "opd"
        assert config['run_index'] == 0
        assert 'variant_seed' in config
        assert config['deterministic'] is True

    def test_different_run_indices(self):
        """Test that different run indices generate different seeds."""
        config1 = get_seed_config(base_seed=42, variant_name="opd", run_index=0)
        config2 = get_seed_config(base_seed=42, variant_name="opd", run_index=1)
        
        assert config1['variant_seed'] != config2['variant_seed']

    def test_different_variants(self):
        """Test that different variants generate different seeds."""
        config1 = get_seed_config(base_seed=42, variant_name="opd", run_index=0)
        config2 = get_seed_config(base_seed=42, variant_name="rl", run_index=0)
        
        assert config1['variant_seed'] != config2['variant_seed']

    def test_different_base_seeds(self):
        """Test that different base seeds generate different seeds."""
        config1 = get_seed_config(base_seed=42, variant_name="opd", run_index=0)
        config2 = get_seed_config(base_seed=100, variant_name="opd", run_index=0)
        
        assert config1['variant_seed'] != config2['variant_seed']

class TestApplySeedConfig:
    """Tests for apply_seed_config function."""

    def test_apply_seed_config(self):
        """Test that seed config is applied correctly."""
        config = get_seed_config(base_seed=42, variant_name="opd", run_index=0)
        
        # Generate a random value
        val1 = random.random()
        
        # Apply config
        apply_seed_config(config)
        val2 = random.random()
        
        # Apply config again
        apply_seed_config(config)
        val3 = random.random()
        
        assert val2 == val3, "Applying same config should produce same results"

    def test_apply_seed_config_missing_seed(self):
        """Test that missing variant_seed raises error."""
        config = {'base_seed': 42}
        
        with pytest.raises(ValueError, match="Config must contain 'variant_seed' key"):
            apply_seed_config(config)

class TestGetSeedEnvironment:
    """Tests for get_seed_environment function."""

    def test_seed_from_environment(self):
        """Test that seed is read from environment variable."""
        with patch.dict(os.environ, {'LLMXIVE_SEED': '42'}):
            seed = get_seed_environment()
            assert seed == 42

    def test_no_seed_in_environment(self):
        """Test that None is returned when no seed in environment."""
        with patch.dict(os.environ, {}, clear=True):
            seed = get_seed_environment()
            assert seed is None

    def test_invalid_seed_in_environment(self):
        """Test that None is returned for invalid seed value."""
        with patch.dict(os.environ, {'LLMXIVE_SEED': 'invalid'}):
            seed = get_seed_environment()
            assert seed is None