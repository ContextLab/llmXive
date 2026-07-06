"""
Unit tests for the configuration management module (T007).
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.utils.config import (
    Config, 
    config, 
    get_config, 
    set_seed, 
    get_paths,
    DEFAULT_SEED,
    FILTER_LOW_FREQ_HZ,
    FILTER_HIGH_FREQ_HZ
)

class TestConfigSingleton:
    def test_singleton_instance(self):
        """Ensure Config returns the same instance."""
        c1 = Config()
        c2 = Config()
        assert c1 is c2

    def test_reset_singleton(self):
        """Test that reset clears the instance."""
        c1 = Config()
        Config.reset()
        c2 = Config()
        assert c1 is not c2

class TestConfigDefaults:
    def test_default_seed(self):
        cfg = Config()
        assert cfg.seed == DEFAULT_SEED

    def test_default_filter_params(self):
        cfg = Config()
        assert cfg.filter_low == FILTER_LOW_FREQ_HZ
        assert cfg.filter_high == FILTER_HIGH_FREQ_HZ

    def test_default_paths_exist(self):
        cfg = Config()
        paths = cfg.get_paths()
        assert "data" in paths
        assert "logs" in paths
        assert isinstance(paths["data"], Path)

class TestConfigOverrides:
    def setup_method(self):
        """Reset config and env vars before each test."""
        Config.reset()
        # Remove env vars if they exist to ensure clean state
        for key in ["LLMXIVE_SEED", "LLMXIVE_FILTER_LOW", "LLMXIVE_FILTER_HIGH"]:
            if key in os.environ:
                del os.environ[key]

    def test_env_seed_override(self):
        os.environ["LLMXIVE_SEED"] = "12345"
        cfg = Config()
        assert cfg.seed == 12345

    def test_env_filter_override(self):
        os.environ["LLMXIVE_FILTER_LOW"] = "0.5"
        os.environ["LLMXIVE_FILTER_HIGH"] = "50.0"
        cfg = Config()
        assert cfg.filter_low == 0.5
        assert cfg.filter_high == 50.0

    def test_set_seed_function(self):
        set_seed(999)
        cfg = get_config()
        assert cfg.seed == 999

    def test_to_dict_structure(self):
        cfg = Config()
        d = cfg.to_dict()
        assert "seed" in d
        assert "filter" in d
        assert "epochs" in d
        assert "analysis" in d
        assert "statistics" in d
        assert "constraints" in d

class TestConfigPersistence:
    def setup_method(self):
        Config.reset()

    def test_save_config(self, tmp_path):
        cfg = Config()
        cfg.set_seed(42)
        save_path = tmp_path / "test_config.json"
        cfg.save(save_path)
        
        assert save_path.exists()
        import json
        with open(save_path, 'r') as f:
            data = json.load(f)
        
        assert data["seed"] == 42
        assert data["filter"]["low_hz"] == FILTER_LOW_FREQ_HZ
        assert "analysis_window_start_s" in data["analysis"]