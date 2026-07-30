"""
Tests for configuration management and random seed handling.
"""
import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

import config
import random
import numpy as np

class TestConfigLoading:
    """Tests for configuration loading functionality."""
    
    def test_load_config_creates_default(self, tmp_path):
        """Test that load_config creates a default config file if it doesn't exist."""
        config_path = tmp_path / "test_config.yaml"
        
        # Config should be created when loading from non-existent path
        loaded_config = config.load_config(str(config_path))
        
        assert config_path.exists()
        assert "simulation" in loaded_config
        assert "datasets" in loaded_config
        assert "paths" in loaded_config
    
    def test_load_config_from_existing(self, tmp_path):
        """Test loading an existing configuration file."""
        config_path = tmp_path / "test_config.yaml"
        
        # Create a custom config
        custom_config = {
            "simulation": {
                "random_seed": 12345,
                "confidence_levels": [0.95],
                "sample_sizes": [10]
            },
            "paths": {
                "data_dir": str(tmp_path / "custom_data")
            }
        }
        
        with open(config_path, 'w') as f:
            import yaml
            yaml.dump(custom_config, f)
        
        # Load the config
        loaded_config = config.load_config(str(config_path))
        
        assert loaded_config["simulation"]["random_seed"] == 12345
        assert loaded_config["paths"]["data_dir"] == str(tmp_path / "custom_data")
    
    def test_save_config(self, tmp_path):
        """Test saving configuration to a file."""
        config_path = tmp_path / "test_config.yaml"
        test_config = {
            "simulation": {
                "random_seed": 999
            }
        }
        
        config.save_config(test_config, str(config_path))
        
        assert config_path.exists()
        
        # Verify the saved content
        with open(config_path, 'r') as f:
            import yaml
            saved_config = yaml.safe_load(f)
        
        assert saved_config["simulation"]["random_seed"] == 999

class TestRandomSeedManagement:
    """Tests for random seed management functionality."""
    
    def test_get_random_seed_default(self):
        """Test that get_random_seed returns the default seed when not set."""
        # Reset state
        config._random_seed = None
        config._config = {}
        
        seed = config.get_random_seed()
        assert seed == config.DEFAULT_SEED
    
    def test_get_random_seed_from_config(self):
        """Test that get_random_seed uses value from config."""
        config._config = {
            "simulation": {
                "random_seed": 54321
            }
        }
        config._random_seed = None
        
        seed = config.get_random_seed()
        assert seed == 54321
    
    def test_set_random_seed_updates_state(self):
        """Test that set_random_seed updates the internal state."""
        config.set_random_seed(7777)
        assert config.get_random_seed() == 7777
    
    def test_set_random_seed_affects_python_random(self):
        """Test that set_random_seed affects Python's random module."""
        config.set_random_seed(42)
        val1 = random.random()
        
        config.set_random_seed(42)
        val2 = random.random()
        
        assert val1 == val2
    
    def test_set_random_seed_affects_numpy(self):
        """Test that set_random_seed affects numpy's random module."""
        config.set_random_seed(42)
        arr1 = np.random.rand(10)
        
        config.set_random_seed(42)
        arr2 = np.random.rand(10)
        
        assert np.array_equal(arr1, arr2)
    
    def test_initialize_random_state(self):
        """Test that initialize_random_state sets up the random state correctly."""
        seed = config.initialize_random_state(12345)
        assert seed == 12345
        assert config.get_random_seed() == 12345
        
        # Verify reproducibility
        val1 = random.random()
        config.initialize_random_state(12345)
        val2 = random.random()
        assert val1 == val2

class TestDirectoryPaths:
    """Tests for directory path functions."""
    
    def test_get_data_dir_default(self):
        """Test default data directory path."""
        config._config = {}
        path = config.get_data_dir()
        assert str(path) == config.DEFAULT_DATA_DIR
    
    def test_get_data_dir_from_config(self):
        """Test data directory from configuration."""
        config._config = {
            "paths": {
                "data_dir": "/custom/data/path"
            }
        }
        path = config.get_data_dir()
        assert str(path) == "/custom/data/path"
    
    def test_get_output_dir_default(self):
        """Test default output directory path."""
        config._config = {}
        path = config.get_output_dir()
        assert str(path) == config.DEFAULT_OUTPUT_DIR
    
    def test_get_raw_data_dir_default(self):
        """Test default raw data directory path."""
        config._config = {}
        path = config.get_raw_data_dir()
        assert str(path) == "data/raw"
    
    def test_get_processed_data_dir_default(self):
        """Test default processed data directory path."""
        config._config = {}
        path = config.get_processed_data_dir()
        assert str(path) == "data/processed"
    
    def test_get_figures_dir_default(self):
        """Test default figures directory path."""
        config._config = {}
        path = config.get_figures_dir()
        assert str(path) == "figures"

class TestSimulationConfig:
    """Tests for simulation-specific configuration."""
    
    def test_get_simulation_config_default(self):
        """Test default simulation configuration."""
        config._config = {}
        sim_config = config.get_simulation_config()
        
        assert "random_seed" in sim_config
        assert "confidence_levels" in sim_config
        assert "sample_sizes" in sim_config
        assert "n_replications" in sim_config
        assert sim_config["n_replications"] == 1000
    
    def test_get_simulation_config_from_config(self):
        """Test simulation configuration from loaded config."""
        config._config = {
            "simulation": {
                "random_seed": 111,
                "confidence_levels": [0.99],
                "sample_sizes": [5, 10],
                "n_replications": 5000,
                "bootstrap_resamples": 500
            }
        }
        
        sim_config = config.get_simulation_config()
        assert sim_config["random_seed"] == 111
        assert sim_config["n_replications"] == 5000

class TestLoggingConfig:
    """Tests for logging configuration."""
    
    def test_get_log_level_default(self):
        """Test default log level."""
        config._config = {}
        level = config.get_log_level()
        assert level == config.DEFAULT_LOG_LEVEL
    
    def test_get_log_level_from_config(self):
        """Test log level from configuration."""
        config._config = {
            "logging": {
                "level": "DEBUG"
            }
        }
        level = config.get_log_level()
        assert level == "DEBUG"

class TestConfigIntegration:
    """Integration tests for configuration system."""
    
    def test_full_workflow(self, tmp_path):
        """Test a complete configuration workflow."""
        config_path = tmp_path / "integration_config.yaml"
        
        # Load and create default config
        loaded = config.load_config(str(config_path))
        
        # Modify and save
        loaded["simulation"]["random_seed"] = 9999
        config.save_config(loaded, str(config_path))
        
        # Reload and verify
        reloaded = config.load_config(str(config_path))
        assert reloaded["simulation"]["random_seed"] == 9999
        
        # Initialize random state
        config.initialize_random_state(reloaded["simulation"]["random_seed"])
        assert config.get_random_seed() == 9999
        
        # Verify reproducibility
        val1 = random.random()
        config.initialize_random_state(9999)
        val2 = random.random()
        assert val1 == val2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])