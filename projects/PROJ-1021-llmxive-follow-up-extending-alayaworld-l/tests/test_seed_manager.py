"""
Tests for the seed manager module.
"""
import pytest
import os
import json
import random
import tempfile
from pathlib import Path

# Import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.seed_manager import set_seed, save_seed_config, load_seed_config


class TestSeedManager:
    def test_set_seed_deterministic_random(self):
        """Test that setting the seed produces deterministic random numbers."""
        seed = 12345
        set_seed(seed)
        val1 = random.random()
        
        set_seed(seed)
        val2 = random.random()
        
        assert val1 == val2, "Random seed did not produce deterministic output"

    def test_set_seed_deterministic_numpy(self):
        """Test that setting the seed produces deterministic numpy arrays."""
        import numpy as np
        seed = 98765
        set_seed(seed)
        arr1 = np.random.rand(5)
        
        set_seed(seed)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2), "Numpy seed did not produce deterministic output"

    def test_save_and_load_seed_config(self):
        """Test saving and loading seed configuration."""
        seed = 54321
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test_config.json")
            
            # Save
            saved_path = save_seed_config(seed, config_path)
            assert os.path.exists(saved_path), "Config file was not created"
            
            # Load
            config = load_seed_config(config_path)
            assert config["seed"] == seed, "Loaded seed does not match saved seed"
            assert "timestamp" in config, "Timestamp missing from config"
            assert "description" in config, "Description missing from config"

    def test_invalid_seed_type(self):
        """Test that non-integer seeds raise an error."""
        with pytest.raises(TypeError):
            set_seed("not_an_integer")

    def test_load_missing_config(self):
        """Test that loading a missing config file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_seed_config("non_existent_path.json")
