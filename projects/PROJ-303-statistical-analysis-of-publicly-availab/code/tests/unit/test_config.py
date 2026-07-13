"""
Unit tests for the configuration module (src/config.py).
"""
import os
import tempfile
from pathlib import Path
import pytest
import time
import yaml

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.src.config import Config, get_config

class TestConfigInitialization:
    def test_default_paths(self):
        cfg = Config()
        assert cfg.data_raw_dir.name == "raw"
        assert cfg.data_processed_dir.name == "processed"
        assert cfg.wall_clock_budget_seconds == 6 * 3600
        assert cfg.seed == 42

    def test_ensure_dirs_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock PROJECT_ROOT behavior for testing without affecting global state
            # We test that the method creates directories
            test_dir = Path(tmpdir) / "test_data"
            cfg = Config()
            # Temporarily override to test creation
            original_dir = cfg.data_raw_dir
            cfg.data_raw_dir = test_dir
            cfg._ensure_dirs()
            assert test_dir.exists()
            assert test_dir.is_dir()

class TestConfigEnvironmentOverrides:
    def test_env_override_budget(self):
        old_val = os.environ.get("WALL_CLOCK_BUDGET_SECONDS")
        try:
            os.environ["WALL_CLOCK_BUDGET_SECONDS"] = "7200"
            # Re-instantiate to trigger override
            cfg = Config()
            assert cfg.wall_clock_budget_seconds == 7200
        finally:
            if old_val is None:
                os.environ.pop("WALL_CLOCK_BUDGET_SECONDS", None)
            else:
                os.environ["WALL_CLOCK_BUDGET_SECONDS"] = old_val

    def test_env_override_seed(self):
        old_val = os.environ.get("SEED")
        try:
            os.environ["SEED"] = "12345"
            cfg = Config()
            assert cfg.seed == 12345
        finally:
            if old_val is None:
                os.environ.pop("SEED", None)
            else:
                os.environ["SEED"] = old_val

class TestConfigTimeBudget:
    def test_check_time_budget_within_limit(self):
        cfg = Config()
        # Start time 10 seconds ago
        start = time.time() - 10
        assert cfg.check_time_budget(start) is True

    def test_check_time_budget_exceeded(self):
        cfg = Config()
        # Start time 10 hours ago (assuming default 6h limit)
        start = time.time() - (10 * 3600)
        assert cfg.check_time_budget(start) is False

    def test_should_trigger_fallback(self):
        cfg = Config()
        # Start time 2.5 hours ago (default fallback is 2h)
        start = time.time() - (2.5 * 3600)
        assert cfg.should_trigger_fallback(start) is True

        # Start time 1 hour ago
        start = time.time() - (1 * 3600)
        assert cfg.should_trigger_fallback(start) is False

class TestConfigYamlLoading:
    def test_load_from_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            test_data = {
                "seed": 999,
                "wall_clock_budget_seconds": 1000,
                "max_missing_ratio": 0.20
            }
            with open(config_file, 'w') as f:
                yaml.dump(test_data, f)
            
            cfg = Config()
            cfg.load_from_yaml(config_file)
            
            assert cfg.seed == 999
            assert cfg.wall_clock_budget_seconds == 1000
            assert cfg.max_missing_ratio == 0.20

    def test_load_nonexistent_yaml(self):
        cfg = Config()
        # Should not raise an error
        cfg.load_from_yaml(Path("/nonexistent/path.yaml"))
        # Config should remain default
        assert cfg.seed == 42

class TestConfigSetSeed:
    def test_set_seed_reproducibility(self):
        cfg = Config()
        cfg.set_seed()
        val1 = np.random.random()
        
        cfg.set_seed()
        val2 = np.random.random()
        
        assert val1 == val2