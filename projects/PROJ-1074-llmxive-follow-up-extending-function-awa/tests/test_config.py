"""Tests for the configuration management module."""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
import sys

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import load_settings, CONFIG_PATH
from utils.common import ConfigurationError

class TestLoadSettings:
    def test_load_settings_valid_file(self):
        """Test loading a valid settings file."""
        # We assume the file exists as per T006 creation
        # Just verify it loads without error and has structure
        config = load_settings()
        
        assert "dataset_paths" in config
        assert "model_hyperparameters" in config
        assert "gsm8k" in config["dataset_paths"]
        assert "logiqa" in config["dataset_paths"]
        assert "model_name" in config["model_hyperparameters"]
        assert "batch_size" in config["model_hyperparameters"]
        assert "max_length" in config["model_hyperparameters"]

    def test_load_settings_missing_file_raises(self, monkeypatch):
        """Test that a missing config file raises ConfigurationError."""
        # Temporarily rename the file
        if CONFIG_PATH.exists():
            backup = CONFIG_PATH.with_suffix('.yaml.bak')
            CONFIG_PATH.rename(backup)
            try:
                with pytest.raises(ConfigurationError, match="not found"):
                    load_settings()
            finally:
                backup.rename(CONFIG_PATH)
        else:
            # If file doesn't exist, just verify error is raised
            with pytest.raises(ConfigurationError):
                load_settings()

    def test_load_settings_missing_keys_raises(self, monkeypatch, tmp_path):
        """Test that missing required keys raise ConfigurationError."""
        # Create a temporary invalid config
        invalid_config = {
            "dataset_paths": {"gsm8k": "path"}
            # Missing logiqa and model_hyperparameters
        }
        
        temp_config_path = tmp_path / "settings.yaml"
        with open(temp_config_path, 'w') as f:
            yaml.dump(invalid_config, f)
        
        # Monkeypatch CONFIG_PATH
        monkeypatch.setattr('code.config.CONFIG_PATH', temp_config_path)
        
        with pytest.raises(ConfigurationError):
            load_settings()

    def test_load_settings_missing_dataset_key_raises(self, monkeypatch, tmp_path):
        """Test that missing dataset keys raise ConfigurationError."""
        invalid_config = {
            "dataset_paths": {},
            "model_hyperparameters": {
                "model_name": "test",
                "batch_size": 8,
                "max_length": 512
            }
        }
        
        temp_config_path = tmp_path / "settings.yaml"
        with open(temp_config_path, 'w') as f:
            yaml.dump(invalid_config, f)
        
        monkeypatch.setattr('code.config.CONFIG_PATH', temp_config_path)
        
        with pytest.raises(ConfigurationError, match="Missing required dataset path key"):
            load_settings()

    def test_load_settings_missing_model_key_raises(self, monkeypatch, tmp_path):
        """Test that missing model hyperparameter keys raise ConfigurationError."""
        invalid_config = {
            "dataset_paths": {
                "gsm8k": "path1",
                "logiqa": "path2"
            },
            "model_hyperparameters": {
                "model_name": "test"
                # Missing batch_size and max_length
            }
        }
        
        temp_config_path = tmp_path / "settings.yaml"
        with open(temp_config_path, 'w') as f:
            yaml.dump(invalid_config, f)
        
        monkeypatch.setattr('code.config.CONFIG_PATH', temp_config_path)
        
        with pytest.raises(ConfigurationError, match="Missing required model hyperparameter key"):
            load_settings()