"""Tests for the configuration loader."""
import pytest
import json
import tempfile
from pathlib import Path
from src.utils.config import Config, ConfigError, get_default_config, load_config_from_env
import os

class TestConfig:
    def test_init_valid(self):
        cfg = Config(seed=123, generation_count=10, rule_evaluation_budget=500)
        assert cfg.seed == 123
        assert cfg.generation_count == 10
        assert cfg.rule_evaluation_budget == 500

    def test_init_invalid_generation_count(self):
        with pytest.raises(ConfigError):
            Config(seed=1, generation_count=0, rule_evaluation_budget=100)

    def test_init_invalid_budget(self):
        with pytest.raises(ConfigError):
            Config(seed=1, generation_count=10, rule_evaluation_budget=-1)

    def test_to_dict_round_trip(self):
        original = Config(seed=42, generation_count=20, rule_evaluation_budget=2000)
        data = original.to_dict()
        restored = Config.from_dict(data)
        assert restored.seed == original.seed
        assert restored.generation_count == original.generation_count
        assert restored.rule_evaluation_budget == original.rule_evaluation_budget

    def test_file_io(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            cfg = Config(seed=99, generation_count=5, rule_evaluation_budget=50)
            cfg.to_file(str(path))
            
            assert path.exists()
            loaded = Config.from_file(str(path))
            assert loaded.seed == 99
            assert loaded.generation_count == 5

    def test_file_not_found(self):
        with pytest.raises(ConfigError):
            Config.from_file("/nonexistent/path/config.json")

    def test_default_config(self):
        cfg = get_default_config()
        assert cfg.seed == 42
        assert cfg.generation_count == 10
        assert cfg.rule_evaluation_budget == 1000

    def test_env_config(self):
        # Save original env vars
        orig_seed = os.environ.get("LLMXIVE_SEED")
        orig_count = os.environ.get("LLMXIVE_GEN_COUNT")
        orig_budget = os.environ.get("LLMXIVE_BUDGET")
        
        try:
            os.environ["LLMXIVE_SEED"] = "111"
            os.environ["LLMXIVE_GEN_COUNT"] = "22"
            os.environ["LLMXIVE_BUDGET"] = "333"
            
            cfg = load_config_from_env()
            assert cfg.seed == 111
            assert cfg.generation_count == 22
            assert cfg.rule_evaluation_budget == 333
        finally:
            # Restore env vars
            if orig_seed is None:
                os.environ.pop("LLMXIVE_SEED", None)
            else:
                os.environ["LLMXIVE_SEED"] = orig_seed
                
            if orig_count is None:
                os.environ.pop("LLMXIVE_GEN_COUNT", None)
            else:
                os.environ["LLMXIVE_GEN_COUNT"] = orig_count
                
            if orig_budget is None:
                os.environ.pop("LLMXIVE_BUDGET", None)
            else:
                os.environ["LLMXIVE_BUDGET"] = orig_budget
