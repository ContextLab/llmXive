import unittest
import os
import sys
import tempfile
import shutil
from config import (
    Config, Hyperparameters, SafetyConstraints, PathConfig,
    get_config, set_config, get_learning_rate, get_batch_size,
    get_seed, get_ram_limit, get_trajectory_path, set_seed,
    ensure_directories
)

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Reset singleton before each test
        Config.reset_instance()
        # Also reset the module-level _config if it exists
        import config
        config._config = None

    def tearDown(self):
        # Cleanup any created directories
        pass

    def test_default_hyperparameters(self):
        cfg = get_config()
        self.assertEqual(cfg.hyperparameters.learning_rate, 5e-5)
        self.assertEqual(cfg.hyperparameters.batch_size, 4)
        self.assertEqual(cfg.hyperparameters.seed, 42)
        self.assertEqual(cfg.hyperparameters.gradient_accumulation_steps, 4)

    def test_default_safety_constraints(self):
        cfg = get_config()
        self.assertEqual(cfg.safety_constraints.max_param_increase_percent, 30.0)
        self.assertEqual(cfg.safety_constraints.max_ram_gb, 6.8)
        self.assertEqual(cfg.safety_constraints.max_attempts, 3)
        self.assertEqual(cfg.safety_constraints.degradation_threshold_percent, 5.0)

    def test_default_paths(self):
        cfg = get_config()
        self.assertEqual(cfg.paths.data_raw, "data/raw")
        self.assertEqual(cfg.paths.data_processed, "data/processed")
        self.assertEqual(cfg.paths.results, "results")
        self.assertEqual(cfg.paths.trajectory_file, "results/trajectory.json")

    def test_get_learning_rate(self):
        self.assertEqual(get_learning_rate(), 5e-5)

    def test_get_batch_size(self):
        self.assertEqual(get_batch_size(), 4)

    def test_get_seed(self):
        self.assertEqual(get_seed(), 42)

    def test_get_ram_limit(self):
        self.assertEqual(get_ram_limit(), 6.8)

    def test_get_trajectory_path(self):
        self.assertEqual(get_trajectory_path(), "results/trajectory.json")

    def test_set_seed(self):
        set_seed(123)
        self.assertEqual(get_seed(), 123)
        # Check that random seed was set
        import random
        import numpy as np
        import torch
        random.seed(123)
        np.random.seed(123)
        torch.manual_seed(123)
        self.assertEqual(random.random(), random.random())

    def test_ensure_directories_creates_paths(self):
        # Create a temporary directory to act as project root
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp dir to avoid polluting current directory
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Reset config to use relative paths in tmpdir
                Config.reset_instance()
                import config
                config._config = None
                
                # Manually set paths to temp dir for testing
                cfg = get_config()
                cfg.paths.data_raw = os.path.join(tmpdir, "data", "raw")
                cfg.paths.data_processed = os.path.join(tmpdir, "data", "processed")
                cfg.paths.results = os.path.join(tmpdir, "results")
                cfg.paths.logs = os.path.join(tmpdir, "results", "logs")
                cfg.paths.checkpoints = os.path.join(tmpdir, "data", "checkpoints")
                
                ensure_directories()
                
                # Verify directories exist
                self.assertTrue(os.path.exists(cfg.paths.data_raw))
                self.assertTrue(os.path.exists(cfg.paths.data_processed))
                self.assertTrue(os.path.exists(cfg.paths.results))
                self.assertTrue(os.path.exists(cfg.paths.logs))
                self.assertTrue(os.path.exists(cfg.paths.checkpoints))
            finally:
                os.chdir(old_cwd)

    def test_singleton_behavior(self):
        cfg1 = get_config()
        cfg2 = get_config()
        self.assertIs(cfg1, cfg2)

    def test_set_config_updates_instance(self):
        new_cfg = Config(
            hyperparameters=Hyperparameters(learning_rate=1e-4, batch_size=8),
            safety_constraints=SafetyConstraints(max_ram_gb=10.0),
            paths=PathConfig(results="custom_results")
        )
        set_config(new_cfg)
        self.assertIs(get_config(), new_cfg)
        self.assertEqual(get_learning_rate(), 1e-4)
        self.assertEqual(get_batch_size(), 8)
        self.assertEqual(get_ram_limit(), 10.0)
        self.assertEqual(get_config().paths.results, "custom_results")

if __name__ == '__main__':
    unittest.main()