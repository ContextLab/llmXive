import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from config import (
    Hyperparameters, SafetyConstraints, PathConfig, Config,
    get_config, set_config, get_learning_rate, get_batch_size,
    get_seed, get_ram_limit, get_trajectory_path,
    get_max_param_increase_percent, get_bootstrap_resamples,
    set_seed, ensure_directories
)

class TestConfigDefaults(unittest.TestCase):
    def setUp(self):
        self.original_config = get_config()

    def tearDown(self):
        set_config(self.original_config)

    def test_hyperparameters_defaults(self):
        hp = Hyperparameters()
        self.assertEqual(hp.learning_rate, 5e-5)
        self.assertEqual(hp.batch_size, 4)
        self.assertEqual(hp.seed, 42)
        self.assertEqual(hp.max_param_increase_percent, 30.0)
        self.assertEqual(hp.bootstrap_resamples, 1000)
        self.assertEqual(hp.max_cycles, 3)
        self.assertEqual(hp.retry_limit, 2)
        self.assertEqual(hp.timeout_seconds, 300)

    def test_safety_constraints_defaults(self):
        sc = SafetyConstraints()
        self.assertEqual(sc.param_limit, 0.30)
        self.assertEqual(sc.ram_limit_gb, 7.0)
        self.assertEqual(sc.max_attempts, 3)
        self.assertEqual(sc.distinctness_threshold, 0.05)

    def test_path_config_defaults(self):
        pc = PathConfig()
        self.assertIn("code", pc.code_dir)
        self.assertIn("data/raw", pc.data_raw_dir)
        self.assertIn("results", pc.results_dir)
        self.assertIn("trajectory.json", pc.trajectory_file)

    def test_get_config_singleton(self):
        cfg1 = get_config()
        cfg2 = get_config()
        self.assertIs(cfg1, cfg2)

    def test_set_config(self):
        new_cfg = Config()
        set_config(new_cfg)
        self.assertIs(get_config(), new_cfg)

    def test_get_learning_rate(self):
        self.assertEqual(get_learning_rate(), 5e-5)

    def test_get_batch_size(self):
        self.assertEqual(get_batch_size(), 4)

    def test_get_seed(self):
        self.assertEqual(get_seed(), 42)

    def test_get_ram_limit(self):
        self.assertEqual(get_ram_limit(), 7.0)

    def test_get_max_param_increase_percent(self):
        self.assertEqual(get_max_param_increase_percent(), 30.0)

    def test_get_bootstrap_resamples(self):
        self.assertEqual(get_bootstrap_resamples(), 1000)

    def test_set_seed(self):
        set_seed(123)
        self.assertEqual(get_seed(), 123)
        import random
        import numpy as np
        import torch
        # Verify side effects
        self.assertEqual(random.getstate()[1][0], 123)
        self.assertEqual(np.random.get_state()[1][0], 123)
        self.assertEqual(torch.initial_seed(), 123)

    def test_ensure_directories_creates_paths(self):
        with patch('config.os.makedirs') as mock_makedirs:
            ensure_directories()
            self.assertTrue(mock_makedirs.called)

if __name__ == '__main__':
    unittest.main()