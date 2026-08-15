"""
Unit tests for the configuration management module.
"""

import os
import random
import tempfile
from pathlib import Path
import unittest

import numpy as np
import torch
import yaml

# Import the module under test
# Assuming the test runner adds 'code' to sys.path or we import relative to project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config import ConfigManager, initialize_experiment


class TestConfigManager(unittest.TestCase):
    """Tests for the ConfigManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_config_file = self.temp_path / "test_config.yaml"

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_default_config_creation(self):
        """Test that a ConfigManager creates default config when file is missing."""
        # Use a non-existent path to trigger default creation
        manager = ConfigManager(config_path=Path("/nonexistent/path/config.yaml"))
        
        self.assertIn("seed", manager.config)
        self.assertIn("hyperparameters", manager.config)
        self.assertIn("paths", manager.config)
        
        # Check specific defaults
        self.assertEqual(manager.config["seed"], 42)
        self.assertEqual(manager.config["hyperparameters"]["num_layers"], 3)

    def test_load_config_from_file(self):
        """Test loading configuration from a YAML file."""
        test_data = {
            "seed": 123,
            "hyperparameters": {
                "hidden_channels": 256,
                "learning_rate": 0.0001
            },
            "paths": {
                "data_raw": "custom/raw"
            }
        }

        with open(self.test_config_file, "w") as f:
            yaml.dump(test_data, f)

        manager = ConfigManager(config_path=self.test_config_file)

        self.assertEqual(manager.config["seed"], 123)
        self.assertEqual(manager.config["hyperparameters"]["hidden_channels"], 256)
        self.assertEqual(manager.config["hyperparameters"]["learning_rate"], 0.0001)
        self.assertEqual(manager.config["paths"]["data_raw"], "custom/raw")

    def test_set_seeds_reproducibility(self):
        """Test that set_seeds actually sets the seeds correctly."""
        manager = ConfigManager()
        manager.config["seed"] = 999
        
        manager.set_seeds()

        # Check Python random
        self.assertEqual(random.random(), 0.6812856877461383) # First random after seed 999

        # Check NumPy
        np.random.seed(999)
        self.assertEqual(np.random.random(), 0.6812856877461383)

        # Check PyTorch
        torch.manual_seed(999)
        self.assertEqual(torch.rand(1).item(), 0.6812856877461383)

    def test_get_hyperparameter(self):
        """Test retrieving specific hyperparameters."""
        manager = ConfigManager()
        
        # Test existing key
        self.assertEqual(manager.get_hyperparameter("num_layers"), 3)
        
        # Test non-existing key with default
        self.assertEqual(manager.get_hyperparameter("non_existent_key", 10), 10)
        
        # Test non-existing key without default (returns None)
        self.assertIsNone(manager.get_hyperparameter("non_existent_key"))

    def test_get_path(self):
        """Test retrieving specific paths."""
        manager = ConfigManager()
        
        # Test existing path
        self.assertEqual(manager.get_path("data_raw"), Path("data/raw"))
        
        # Test non-existing path with default
        self.assertEqual(manager.get_path("non_existent", Path("default")), Path("default"))

    def test_save_config(self):
        """Test saving configuration to a file."""
        manager = ConfigManager()
        manager.config["seed"] = 777
        manager.config["hyperparameters"]["hidden_channels"] = 512
        
        output_file = self.temp_path / "saved_config.yaml"
        manager.save_config(output_file)

        self.assertTrue(output_file.exists())

        with open(output_file, "r") as f:
            saved_data = yaml.safe_load(f)

        self.assertEqual(saved_data["seed"], 777)
        self.assertEqual(saved_data["hyperparameters"]["hidden_channels"], 512)

    def test_initialize_experiment(self):
        """Test the convenience function initialize_experiment."""
        manager = initialize_experiment()
        
        # Should have set seeds
        self.assertEqual(random.random(), 0.6394267984578837) # First random after seed 42

        # Should have loaded default config
        self.assertEqual(manager.config["seed"], 42)

if __name__ == "__main__":
    unittest.main()