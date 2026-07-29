import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from config import (
    Hyperparameters, SafetyConstraints, PathConfig, Config,
    get_config, set_config, get_learning_rate, get_batch_size,
    get_seed, get_ram_limit, get_trajectory_path, set_seed, ensure_directories
)

class TestConfig(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.original_config = None
        
    def tearDown(self):
        """Clean up after tests."""
        if self.original_config is not None:
            set_config(self.original_config)
        
    def test_default_hyperparameters(self):
        """Test that default hyperparameters match specification."""
        cfg = get_config()
        
        self.assertEqual(cfg.hyperparameters.learning_rate, 5e-5)
        self.assertEqual(cfg.hyperparameters.batch_size, 4)
        self.assertEqual(cfg.hyperparameters.seed, 42)
        self.assertEqual(cfg.hyperparameters.gradient_accumulation_steps, 4)
        self.assertEqual(cfg.hyperparameters.max_epochs, 1)
        self.assertEqual(cfg.hyperparameters.weight_decay, 0.01)
        self.assertEqual(cfg.hyperparameters.warmup_steps, 100)
        self.assertEqual(cfg.hyperparameters.max_grad_norm, 1.0)
        
    def test_default_safety_constraints(self):
        """Test that default safety constraints match specification."""
        cfg = get_config()
        
        self.assertEqual(cfg.safety.max_param_increase_percent, 30.0)
        self.assertEqual(cfg.safety.ram_limit_gb, 7.0)
        self.assertEqual(cfg.safety.degradation_threshold_percent, 5.0)
        self.assertEqual(cfg.safety.max_cycles, 10)
        self.assertEqual(cfg.safety.timeout_seconds, 3600)
        self.assertEqual(cfg.safety.max_prompt_attempts, 3)
        self.assertEqual(cfg.safety.max_training_retries, 2)
        
    def test_default_path_config(self):
        """Test that default paths are correctly set."""
        cfg = get_config()
        
        self.assertEqual(cfg.paths.code_dir, "code")
        self.assertEqual(cfg.paths.data_raw_dir, "data/raw")
        self.assertEqual(cfg.paths.data_processed_dir, "data/processed")
        self.assertEqual(cfg.paths.results_dir, "results")
        self.assertEqual(cfg.paths.specs_dir, "specs")
        self.assertEqual(cfg.paths.tests_dir, "tests")
        self.assertEqual(cfg.paths.templates_dir, "templates")
        self.assertEqual(cfg.paths.checkpoints_dir, "data/checkpoints")
        self.assertEqual(cfg.paths.logs_dir, "results/logs")
        self.assertEqual(cfg.paths.trajectory_file, "results/trajectory.json")
        self.assertEqual(cfg.paths.decay_analysis_file, "results/decay_analysis.json")
        self.assertEqual(cfg.paths.trade_off_file, "results/trade_off_analysis.json")
        self.assertEqual(cfg.paths.state_file, "results/state.json")
        
    def test_get_learning_rate(self):
        """Test get_learning_rate helper function."""
        self.assertEqual(get_learning_rate(), 5e-5)
        
    def test_get_batch_size(self):
        """Test get_batch_size helper function."""
        self.assertEqual(get_batch_size(), 4)
        
    def test_get_seed(self):
        """Test get_seed helper function."""
        self.assertEqual(get_seed(), 42)
        
    def test_get_ram_limit(self):
        """Test get_ram_limit helper function."""
        self.assertEqual(get_ram_limit(), 7.0)
        
    def test_get_trajectory_path(self):
        """Test get_trajectory_path returns correct path."""
        path = get_trajectory_path()
        self.assertTrue(path.endswith("results/trajectory.json"))
        
    def test_set_seed(self):
        """Test set_seed function sets all random seeds."""
        set_seed(123)
        self.assertEqual(get_seed(), 123)
        
        import random
        import numpy as np
        import torch
        
        # Verify seeds are actually set
        r1 = random.random()
        n1 = np.random.random()
        t1 = torch.rand(1).item()
        
        set_seed(123)
        r2 = random.random()
        n2 = np.random.random()
        t2 = torch.rand(1).item()
        
        self.assertEqual(r1, r2)
        self.assertEqual(n1, n2)
        self.assertEqual(t1, t2)
        
    def test_ensure_directories(self):
        """Test ensure_directories creates all required directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary config
            temp_paths = PathConfig(root=tmpdir)
            temp_config = Config(paths=temp_paths)
            self.original_config = get_config()
            set_config(temp_config)
            
            # Ensure directories
            ensure_directories()
            
            # Verify directories exist
            self.assertTrue(os.path.exists(temp_paths.data_raw_path))
            self.assertTrue(os.path.exists(temp_paths.data_processed_path))
            self.assertTrue(os.path.exists(temp_paths.results_path))
            self.assertTrue(os.path.exists(temp_paths.checkpoints_path))
            self.assertTrue(os.path.exists(temp_paths.logs_path))
            
    def test_custom_config(self):
        """Test that custom config values can be set."""
        custom_hp = Hyperparameters(learning_rate=1e-4, batch_size=8, seed=999)
        custom_safety = SafetyConstraints(max_param_increase_percent=50.0, ram_limit_gb=8.0)
        custom_config = Config(hyperparameters=custom_hp, safety=custom_safety)
        
        self.original_config = get_config()
        set_config(custom_config)
        
        self.assertEqual(get_learning_rate(), 1e-4)
        self.assertEqual(get_batch_size(), 8)
        self.assertEqual(get_seed(), 999)
        self.assertEqual(get_ram_limit(), 8.0)
        self.assertEqual(get_config().safety.max_param_increase_percent, 50.0)
        
    def test_config_immutability_of_defaults(self):
        """Test that default config values are correct and not mutated."""
        cfg1 = get_config()
        cfg2 = get_config()
        
        # Should return the same instance
        self.assertIs(cfg1, cfg2)
        
        # Values should match spec
        self.assertEqual(cfg1.hyperparameters.learning_rate, 5e-5)
        self.assertEqual(cfg1.hyperparameters.batch_size, 4)
        
        # Modify cfg1
        cfg1.hyperparameters.learning_rate = 1e-4
        
        # cfg2 should reflect the change since it's the same instance
        self.assertEqual(cfg2.hyperparameters.learning_rate, 1e-4)
        
        # Reset to default
        set_config(Config())
        self.assertEqual(get_learning_rate(), 5e-5)

if __name__ == "__main__":
    unittest.main()