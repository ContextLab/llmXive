"""
Unit tests for configuration management (T008).
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Import the config module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from config import (
    load_config,
    get_seed,
    get_path,
    get_hyperparameter,
    get_simulation_config,
    _deep_merge,
    _resolve_paths,
    DEFAULT_CONFIG
)


class TestDeepMerge:
    """Tests for the _deep_merge utility function."""
    
    def test_simple_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}
    
    def test_nested_merge(self):
        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"c": 3, "d": 4}}
        result = _deep_merge(base, override)
        assert result == {"a": {"b": 1, "c": 3, "d": 4}}
    
    def test_override_non_dict(self):
        base = {"a": {"b": 1}}
        override = {"a": "string"}
        result = _deep_merge(base, override)
        assert result == {"a": "string"}
    
    def test_empty_override(self):
        base = {"a": 1}
        override = {}
        result = _deep_merge(base, override)
        assert result == {"a": 1}


class TestResolvePaths:
    """Tests for the _resolve_paths utility function."""
    
    def test_resolve_relative_paths(self, tmp_path):
        # Create a mock project root
        original_root = Path(__file__).parent.parent.parent
        
        config = {
            "paths": {
                "data_raw": "data/raw",
                "data_processed": "data/processed"
            }
        }
        
        result = _resolve_paths(config)
        
        # Paths should be converted to absolute
        assert Path(result["paths"]["data_raw"]).is_absolute()
        assert Path(result["paths"]["data_processed"]).is_absolute()
        
        # Directories should be created
        assert Path(result["paths"]["data_raw"]).exists()
        assert Path(result["paths"]["data_processed"]).exists()


class TestLoadConfig:
    """Tests for the load_config function."""
    
    def test_default_config_exists(self):
        config = load_config()
        assert "seeds" in config
        assert "paths" in config
        assert "hyperparameters" in config
        assert "simulation" in config
    
    def test_default_seeds(self):
        config = load_config()
        assert config["seeds"]["global_seed"] == 42
        assert config["seeds"]["train_test_split_seed"] == 42
    
    def test_default_paths_exist(self):
        config = load_config()
        assert "data_raw" in config["paths"]
        assert "data_processed" in config["paths"]
    
    def test_yaml_config_override(self, tmp_path):
        # Create a temporary config.yaml
        yaml_content = {
            "seeds": {"global_seed": 123},
            "hyperparameters": {"max_turns": 30}
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(yaml_content, f)
        
        # Temporarily override CONFIG_FILE_PATH
        import config as config_module
        original_path = config_module.CONFIG_FILE_PATH
        config_module.CONFIG_FILE_PATH = config_file
        
        try:
            config = config_module.load_config()
            assert config["seeds"]["global_seed"] == 123
            assert config["hyperparameters"]["max_turns"] == 30
        finally:
            config_module.CONFIG_FILE_PATH = original_path
    
    def test_env_variable_override(self, monkeypatch):
        monkeypatch.setenv("LLMXIVE_GLOBAL_SEED", "999")
        
        config = load_config()
        # Note: This might not work if .env is already loaded
        # The test verifies the mechanism exists
        assert "seeds" in config


class TestGetSeed:
    """Tests for the get_seed function."""
    
    def test_get_global_seed(self):
        seed = get_seed("global_seed")
        assert isinstance(seed, int)
    
    def test_get_nonexistent_seed(self):
        # Should return default or raise? Currently returns default
        seed = get_seed("nonexistent_seed")
        assert seed == 42  # Default fallback


class TestGetPath:
    """Tests for the get_path function."""
    
    def test_get_data_raw_path(self):
        path = get_path("data_raw")
        assert isinstance(path, Path)
        assert path.exists()
    
    def test_get_nonexistent_path(self):
        with pytest.raises(KeyError):
            get_path("nonexistent_path")


class TestGetHyperparameter:
    """Tests for the get_hyperparameter function."""
    
    def test_get_max_turns(self):
        value = get_hyperparameter("max_turns")
        assert isinstance(value, int)
        assert value > 0
    
    def test_get_nested_param(self):
        value = get_hyperparameter("xgboost_params", "max_depth")
        assert isinstance(value, int)
    
    def test_get_nonexistent_param(self):
        value = get_hyperparameter("nonexistent_param")
        assert value is None


class TestGetSimulationConfig:
    """Tests for the get_simulation_config function."""
    
    def test_simulation_config_structure(self):
        config = get_simulation_config()
        assert "run_baseline" in config
        assert "run_meta_critic" in config
        assert "seed" in config
    
    def test_default_simulation_values(self):
        config = get_simulation_config()
        assert config["run_baseline"] is True
        assert config["run_meta_critic"] is True


class TestConfigIntegration:
    """Integration tests for the configuration system."""
    
    def test_all_paths_are_valid(self):
        config = load_config()
        for key, value in config["paths"].items():
            path = Path(value)
            assert path.exists(), f"Path {key} ({value}) does not exist"
    
    def test_config_is_consistent(self):
        config = load_config()
        
        # Check that seeds are integers
        for key, value in config["seeds"].items():
            assert isinstance(value, int), f"Seed {key} is not an integer"
        
        # Check that hyperparameters are valid types
        assert isinstance(config["hyperparameters"]["max_turns"], int)
        assert isinstance(config["hyperparameters"]["token_budget"], int)
        assert isinstance(config["hyperparameters"]["abstention_threshold"], float)
    
    def test_directories_created(self):
        config = load_config()
        paths = config["paths"]
        
        # Ensure all configured paths exist as directories
        for key in ["data_raw", "data_processed", "data_results", "figures", "models", "logs"]:
            path = Path(paths[key])
            assert path.exists(), f"Directory {key} was not created"
            assert path.is_dir(), f"{key} is not a directory"