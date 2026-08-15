"""
Unit tests for config.py
"""
import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import (
    Hyperparameters,
    SafetyConstraints,
    PathConfig,
    Config,
    get_config,
    set_config,
    ensure_directories,
    verify_default_values,
    get_trajectory_path,
    get_log_path,
    get_checkpoint_path
)


class TestConfigDefaults(unittest.TestCase):
    """Test that default configuration values match the specification."""

    def setUp(self):
        """Reset config before each test."""
        # Clear the global config to ensure fresh instance
        import config
        config._config = None

    def tearDown(self):
        """Clean up after each test."""
        import config
        config._config = None

    def test_hyperparameters_defaults(self):
        """Test that hyperparameters have correct default values."""
        hp = Hyperparameters()
        self.assertEqual(hp.learning_rate, 5e-5)
        self.assertEqual(hp.batch_size, 4)
        self.assertEqual(hp.seed, 42)
        self.assertEqual(hp.gradient_accumulation_steps, 4)
        self.assertEqual(hp.max_epochs, 1)
        self.assertEqual(hp.weight_decay, 0.01)
        self.assertEqual(hp.max_grad_norm, 1.0)
        self.assertEqual(hp.num_resamples, 1000)

    def test_safety_constraints_defaults(self):
        """Test that safety constraints have correct default values."""
        sc = SafetyConstraints()
        self.assertEqual(sc.max_param_increase_percent, 0.30)
        self.assertEqual(sc.max_ram_gb, 7.0)
        self.assertEqual(sc.max_cycle_time_seconds, 3600.0)
        self.assertEqual(sc.max_total_time_hours, 12.0)
        self.assertEqual(sc.max_attempts, 3)
        self.assertEqual(sc.degradation_threshold_percent, 0.05)

    def test_path_config_initialization(self):
        """Test that path config initializes correctly."""
        pc = PathConfig()
        # Check that data directories are set
        self.assertTrue(pc.data_raw.endswith(os.path.join("data", "raw")))
        self.assertTrue(pc.data_processed.endswith(os.path.join("data", "processed")))
        self.assertTrue(pc.results_dir.endswith("results"))
        self.assertTrue(pc.results_logs.endswith(os.path.join("results", "logs")))
        self.assertTrue(pc.trajectory_file.endswith("trajectory.json"))

    def test_config_set_seed(self):
        """Test that config.set_seed() sets all random seeds."""
        import random
        import numpy as np
        import torch

        config = Config()
        config.set_seed()

        # Verify seeds are set
        self.assertEqual(random.getstate()[1][0], np.random.get_state()[1][0])
        self.assertEqual(torch.initial_seed() % (2**32), np.random.get_state()[1][0] % (2**32))

    def test_get_config_returns_singleton(self):
        """Test that get_config() returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        self.assertIs(config1, config2)

    def test_set_config_updates_global(self):
        """Test that set_config() updates the global config."""
        new_config = Config()
        set_config(new_config)
        self.assertIs(get_config(), new_config)

    def test_ensure_directories_creates_dirs(self):
        """Test that ensure_directories() creates required directories."""
        with patch('os.makedirs') as mock_makedirs:
            ensure_directories()
            # Should be called for each directory
            self.assertEqual(mock_makedirs.call_count, 6)
            # Verify exist_ok=True is passed
            for call in mock_makedirs.call_args_list:
                self.assertTrue(call.kwargs.get('exist_ok', False))

    def test_verify_default_values_passes(self):
        """Test that verify_default_values() returns True for correct config."""
        # Reset config to defaults
        import config
        config._config = None
        self.assertTrue(verify_default_values())

    def test_get_trajectory_path(self):
        """Test that get_trajectory_path() returns correct path."""
        path = get_trajectory_path()
        self.assertTrue(path.endswith("trajectory.json"))

    def test_get_log_path(self):
        """Test that get_log_path() returns correct path for a cycle."""
        path = get_log_path(1)
        self.assertTrue(path.endswith("logs"))
        self.assertTrue("cycle_1.log" in path)

    def test_get_checkpoint_path(self):
        """Test that get_checkpoint_path() returns correct path."""
        path = get_checkpoint_path(1)
        self.assertTrue(path.endswith("checkpoints"))
        self.assertTrue("cycle_1.pt" in path)

    def test_custom_hyperparameters(self):
        """Test that custom hyperparameters can be set."""
        hp = Hyperparameters(learning_rate=1e-4, batch_size=8, seed=123)
        self.assertEqual(hp.learning_rate, 1e-4)
        self.assertEqual(hp.batch_size, 8)
        self.assertEqual(hp.seed, 123)

    def test_custom_safety_constraints(self):
        """Test that custom safety constraints can be set."""
        sc = SafetyConstraints(max_param_increase_percent=0.50, max_ram_gb=16.0)
        self.assertEqual(sc.max_param_increase_percent, 0.50)
        self.assertEqual(sc.max_ram_gb, 16.0)


if __name__ == '__main__':
    unittest.main()