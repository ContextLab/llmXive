import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from config import (
    Hyperparameters, SafetyConstraints, PathConfig, Config,
    get_config, set_config, get_learning_rate, get_batch_size,
    get_seed, get_ram_limit, get_trajectory_path, set_seed,
    ensure_directories, get_max_param_increase_percent, get_bootstrap_resamples
)

class TestConfigDefaults(unittest.TestCase):
    """Test that config defaults match the specification."""

    def setUp(self):
        """Reset config before each test."""
        from config import _config_instance
        # Force re-initialization by clearing the instance
        import config as config_module
        config_module._config_instance = None
        self.config = get_config()

    def test_learning_rate_default(self):
        """Verify default learning rate is 5e-5."""
        self.assertEqual(get_learning_rate(), 5e-5)
        self.assertEqual(self.config.hyperparameters.learning_rate, 5e-5)

    def test_batch_size_default(self):
        """Verify default batch size is 4."""
        self.assertEqual(get_batch_size(), 4)
        self.assertEqual(self.config.hyperparameters.batch_size, 4)

    def test_seed_default(self):
        """Verify default seed is 42."""
        self.assertEqual(get_seed(), 42)
        self.assertEqual(self.config.hyperparameters.seed, 42)

    def test_max_param_increase_limit(self):
        """Verify the resolved FR-019 limit (30% param increase)."""
        # Per spec: "≤30% param increase limit defined here as the resolved value for FR-019's [deferred] limit"
        self.assertEqual(get_max_param_increase_percent(), 0.30)
        self.assertEqual(self.config.safety_constraints.max_param_increase_percent, 0.30)

    def test_ram_limit_default(self):
        """Verify default RAM limit is 7.0 GB (SC-005)."""
        self.assertEqual(get_ram_limit(), 7.0)
        self.assertEqual(self.config.safety_constraints.ram_limit_gb, 7.0)

    def test_degradation_threshold(self):
        """Verify degradation threshold is 5% (FR-015)."""
        self.assertEqual(self.config.safety_constraints.degradation_threshold, 0.05)

    def test_max_cycles(self):
        """Verify max cycles is 3 (FR-007)."""
        self.assertEqual(self.config.safety_constraints.max_cycles, 3)

    def test_max_attempts_per_cycle(self):
        """Verify max attempts per cycle is 3."""
        self.assertEqual(self.config.safety_constraints.max_attempts_per_cycle, 3)

    def test_bootstrap_resamples_default(self):
        """Verify default bootstrap resamples is 1000."""
        self.assertEqual(get_bootstrap_resamples(), 1000)
        self.assertEqual(self.config.hyperparameters.bootstrap_resamples, 1000)

    def test_bootstrap_alpha(self):
        """Verify bootstrap alpha is 0.05."""
        self.assertEqual(self.config.hyperparameters.bootstrap_alpha, 0.05)

    def test_trajectory_path_exists(self):
        """Verify trajectory path is set and exists."""
        path = get_trajectory_path()
        self.assertTrue(path.endswith('results/trajectory.json'))
        # The directory should exist
        self.assertTrue(os.path.exists(os.path.dirname(path)))

    def test_directories_created(self):
        """Verify ensure_directories creates required folders."""
        # Clear directories first
        config = get_config()
        for dir_path in [
            config.paths.data_raw_dir,
            config.paths.data_processed_dir,
            config.paths.results_dir,
            config.paths.checkpoints_dir,
            config.paths.logs_dir,
        ]:
            if os.path.exists(dir_path):
                import shutil
                shutil.rmtree(dir_path)
        
        # Recreate
        ensure_directories()
        
        # Verify they exist
        for dir_path in [
            config.paths.data_raw_dir,
            config.paths.data_processed_dir,
            config.paths.results_dir,
            config.paths.checkpoints_dir,
            config.paths.logs_dir,
        ]:
            self.assertTrue(os.path.isdir(dir_path), f"Directory {dir_path} was not created")

    def test_set_seed_functionality(self):
        """Verify set_seed sets random seeds correctly."""
        import random
        import numpy as np
        import torch
        
        set_seed(12345)
        
        # Check random
        val1 = random.random()
        set_seed(12345)
        val2 = random.random()
        self.assertEqual(val1, val2)
        
        # Check numpy
        arr1 = np.random.rand(5)
        set_seed(12345)
        arr2 = np.random.rand(5)
        np.testing.assert_array_equal(arr1, arr2)
        
        # Check torch
        t1 = torch.rand(5)
        set_seed(12345)
        t2 = torch.rand(5)
        torch.testing.assert_close(t1, t2)

    def test_config_singleton(self):
        """Verify get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        self.assertIs(config1, config2)

    def test_path_config_defaults(self):
        """Verify path config has correct defaults."""
        paths = self.config.paths
        
        # Check that base directories are set
        self.assertIsNotNone(paths.base_dir)
        self.assertTrue(os.path.exists(paths.base_dir))
        
        # Check dataset paths
        self.assertEqual(paths.openwebtext_path, "openwebtext")
        self.assertEqual(paths.gsm8k_path, "gsm8k")
        self.assertEqual(paths.arc_challenge_path, "arc_challenge")
        self.assertEqual(paths.boolq_path, "boolq")

    def test_hyperparameters_dataclass(self):
        """Verify Hyperparameters is a proper dataclass with correct fields."""
        hp = Hyperparameters()
        self.assertIsInstance(hp.learning_rate, float)
        self.assertIsInstance(hp.batch_size, int)
        self.assertIsInstance(hp.seed, int)
        self.assertIsInstance(hp.gradient_accumulation_steps, int)
        self.assertIsInstance(hp.max_epochs, int)
        self.assertIsInstance(hp.weight_decay, float)
        self.assertIsInstance(hp.warmup_steps, int)
        self.assertIsInstance(hp.bootstrap_resamples, int)
        self.assertIsInstance(hp.bootstrap_alpha, float)

    def test_safety_constraints_dataclass(self):
        """Verify SafetyConstraints is a proper dataclass with correct fields."""
        sc = SafetyConstraints()
        self.assertIsInstance(sc.max_param_increase_percent, float)
        self.assertIsInstance(sc.ram_limit_gb, float)
        self.assertIsInstance(sc.degradation_threshold, float)
        self.assertIsInstance(sc.max_cycles, int)
        self.assertIsInstance(sc.max_attempts_per_cycle, int)

    def test_path_config_dataclass(self):
        """Verify PathConfig is a proper dataclass with correct fields."""
        pc = PathConfig()
        self.assertIsInstance(pc.base_dir, str)
        self.assertIsInstance(pc.data_raw_dir, str)
        self.assertIsInstance(pc.data_processed_dir, str)
        self.assertIsInstance(pc.results_dir, str)
        self.assertIsInstance(pc.checkpoints_dir, str)
        self.assertIsInstance(pc.logs_dir, str)
        self.assertIsInstance(pc.openwebtext_path, str)
        self.assertIsInstance(pc.gsm8k_path, str)
        self.assertIsInstance(pc.arc_challenge_path, str)
        self.assertIsInstance(pc.boolq_path, str)
        self.assertIsInstance(pc.trajectory_path, str)
        self.assertIsInstance(pc.trade_off_path, str)
        self.assertIsInstance(pc.state_path, str)

if __name__ == '__main__':
    unittest.main()