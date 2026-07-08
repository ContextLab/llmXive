"""
Unit tests for the configuration management system.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import Config, get_config, reload_config

class TestConfig:
    """Tests for the Config class."""
    
    def test_default_config_creation(self, tmp_path):
        """Test that Config can be created with default paths."""
        # Create a temporary config file
        config_file = tmp_path / "config.yaml"
        config_data = {
            "data": {"max_samples": 100},
            "models": {"gpr": {"kernel": "RBF"}}
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Create config with explicit paths
        cfg = Config(config_path=str(config_file))
        
        assert cfg.get("data.max_samples") == 100
        assert cfg.get("models.gpr.kernel") == "RBF"
    
    def test_nested_key_access(self, tmp_path):
        """Test accessing nested configuration keys."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        cfg = Config(config_path=str(config_file))
        assert cfg.get("level1.level2.level3") == "deep_value"
    
    def test_missing_key_returns_default(self, tmp_path):
        """Test that missing keys return the provided default."""
        config_file = tmp_path / "config.yaml"
        config_data = {"existing": "value"}
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        cfg = Config(config_path=str(config_file))
        assert cfg.get("nonexistent", "default") == "default"
        assert cfg.get("nonexistent") is None
    
    def test_env_variable_loading(self, tmp_path):
        """Test loading environment variables from .env file."""
        env_file = tmp_path / ".env"
        env_content = """
        TEST_VAR=test_value
        ANOTHER_VAR=123
        """
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        cfg = Config(env_path=str(env_file))
        
        assert cfg.get_env("TEST_VAR") == "test_value"
        assert cfg.get_env("ANOTHER_VAR") == "123"
        assert cfg.get_env("NONEXISTENT") is None
    
    def test_default_hyperparameters(self, tmp_path):
        """Test that default hyperparameters are loaded when config file is missing."""
        # Use a non-existent config path
        cfg = Config(config_path=str(tmp_path / "nonexistent.yaml"))
        
        # Check that defaults are present
        assert cfg.get("data.max_samples") == 1000
        assert cfg.get("data.random_seed") == 42
        assert cfg.get("models.gpr.kernel") == "RBF"
    
    def test_properties(self, tmp_path):
        """Test the convenience properties."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "data": {"test": 1},
            "models": {"test": 2},
            "stats": {"test": 3}
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        cfg = Config(config_path=str(config_file))
        
        assert cfg.data_config["test"] == 1
        assert cfg.models_config["test"] == 2
        assert cfg.stats_config["test"] == 3
    
    def test_global_config_singleton(self, tmp_path):
        """Test that get_config returns a singleton instance."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({"data": {"max_samples": 999}}, f)
        
        cfg1 = get_config(config_path=str(config_file))
        cfg2 = get_config()
        
        assert cfg1 is cfg2
    
    def test_reload_config(self, tmp_path):
        """Test that reload_config creates a new instance."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({"data": {"max_samples": 100}}, f)
        
        cfg1 = get_config(config_path=str(config_file))
        cfg2 = reload_config()
        
        assert cfg1 is not cfg2
        assert cfg2.get("data.max_samples") == 100
    
    def test_config_repr(self, tmp_path):
        """Test the string representation of Config."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({}, f)
        
        cfg = Config(config_path=str(config_file))
        repr_str = repr(cfg)
        
        assert "Config" in repr_str
        assert str(config_file) in repr_str

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
