"""
Unit tests for code/config.py.

Specifically tests:
- Seed verification and logging behavior.
- Warning generation when seed is missing.
- Seed application to random and numpy.
"""
import os
import logging
import random
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path if needed (assuming tests/ is at root)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import load_config, set_seed, ConfigError, logger

class TestSeedVerification:
    """Tests for seed verification and logging logic."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, caplog):
        """Setup test environment."""
        self.tmp_path = tmp_path
        self.caplog.set_level(logging.WARNING)
        # Ensure a clean environment for each test
        self.original_seed_env = os.environ.pop("LLMXIVE_SEED", None)
        self.original_config_env = os.environ.pop("LLMXIVE_CONFIG_PATH", None)

    def teardown_method(self):
        """Restore environment."""
        if self.original_seed_env is not None:
            os.environ["LLMXIVE_SEED"] = self.original_seed_env
        if self.original_config_env is not None:
            os.environ["LLMXIVE_CONFIG_PATH"] = self.original_config_env

    def test_seed_set_explicitly_logs_info(self, caplog):
        """Verify that setting a seed explicitly logs the action."""
        with caplog.at_level(logging.INFO):
            result = set_seed(seed=42)
        
        assert result == 42
        assert "Random seed set to: 42" in caplog.text
        # Verify random state is actually affected
        r1 = random.random()
        random.seed(42)
        r2 = random.random()
        assert r1 == r2

    def test_seed_from_config_logs_info(self, tmp_path, caplog):
        """Verify that loading a seed from config logs the action."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("seed: 12345")
        
        with caplog.at_level(logging.INFO):
            # Pass the config explicitly to avoid file path logic complexity in test
            cfg = {"seed": 12345}
            result = set_seed(config=cfg)
        
        assert result == 12345
        assert "Random seed set to: 12345" in caplog.text

    def test_no_seed_provided_logs_warning(self, caplog):
        """Verify that missing seed triggers a warning (Constitution Principle I)."""
        # Ensure no seed in config or env
        cfg = {"seed": None}
        
        with caplog.at_level(logging.WARNING):
            result = set_seed(config=cfg)
        
        assert result is None
        assert "No random seed provided" in caplog.text
        assert "Set LLXIVE_SEED or 'seed' in config.yaml" in caplog.text

    def test_no_seed_env_var_logs_warning(self, caplog):
        """Verify warning when environment variable is missing."""
        # Clear env if present
        os.environ.pop("LLMXIVE_SEED", None)
        
        with caplog.at_level(logging.WARNING):
            # load_config will return None for seed
            cfg = load_config()
            result = set_seed(config=cfg)
        
        assert result is None
        assert "No random seed provided" in caplog.text

    def test_seed_applied_to_numpy(self):
        """Verify seed is applied to numpy if available."""
        try:
            import numpy as np
            has_numpy = True
        except ImportError:
            has_numpy = False
            return

        set_seed(seed=999)
        val1 = np.random.random()
        
        set_seed(seed=999)
        val2 = np.random.random()
        
        assert val1 == val2

    def test_load_config_priority_env_over_yaml(self, tmp_path):
        """Verify environment variables take priority over YAML config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("seed: 100")
        
        os.environ["LLMXIVE_SEED"] = "200"
        
        cfg = load_config(config_file)
        assert cfg["seed"] == 200

    def test_load_config_defaults_when_missing(self, tmp_path):
        """Verify defaults are used when no config exists."""
        # Point to non-existent file
        fake_path = tmp_path / "nonexistent.yaml"
        
        cfg = load_config(fake_path)
        assert cfg["seed"] is None
        assert "gss_data_2022.csv" in cfg["dataset_url"]