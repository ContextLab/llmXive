"""
Unit tests for the configuration loader (code/config.py).
Validates that config loading handles missing files and valid YAML correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the function from the sibling module
from code.config import load_config, get_config_value, generate_default_config


class TestConfigLoading:
    """Tests for config.py functionality."""

    def test_load_config_missing_file(self):
        """Ensure loading a non-existent config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_config_valid_yaml(self):
        """Ensure loading a valid YAML file returns a dict."""
        yaml_content = """
        dataset_url: "https://example.com/data.zip"
        hyperparameters:
          batch_size: 32
          learning_rate: 0.01
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert isinstance(config, dict)
            assert config['dataset_url'] == "https://example.com/data.zip"
            assert config['hyperparameters']['batch_size'] == 32
        finally:
            os.unlink(temp_path)

    def test_get_config_value_default(self):
        """Ensure get_config_value returns default if key is missing."""
        config = {"existing_key": "value"}
        assert get_config_value(config, "missing_key", "default_val") == "default_val"

    def test_generate_default_config(self):
        """Ensure generate_default_config returns a dict with expected keys."""
        config = generate_default_config()
        assert isinstance(config, dict)
        assert "dataset_url" in config
        assert "hyperparameters" in config
