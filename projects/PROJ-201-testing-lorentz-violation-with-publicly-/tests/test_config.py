"""
Tests for the configuration management module.
"""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from code.config import load_config, ConfigError, get_config_value


def create_temp_config(content: dict) -> Path:
    """Helper to create a temporary config file."""
    fd, path = tempfile.mkstemp(suffix=".yaml")
    try:
        with os.fdopen(fd, "w") as f:
            yaml.dump(content, f)
        return Path(path)
    except Exception:
        os.close(fd)
        raise


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        valid_config = {
            "paths": {
                "raw": "data/raw",
                "processed": "data/processed",
                "results": "data/results",
                "simulations": "data/simulations",
                "figures": "figures"
            },
            "seeds": {
                "random": 42,
                "numpy": 42
            },
            "constants": {
                "sme_coefficient": 1e-5,
                "l_max": 200
            }
        }
        config_path = create_temp_config(valid_config)
        
        try:
            config = load_config(config_path)
            assert config == valid_config
            assert config["paths"]["raw"] == "data/raw"
        finally:
            config_path.unlink()

    def test_missing_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/path/config.yaml"))

    def test_invalid_yaml(self):
        """Test that ConfigError is raised for invalid YAML."""
        fd, path = tempfile.mkstemp(suffix=".yaml")
        try:
            with os.fdopen(fd, "w") as f:
                f.write("invalid: yaml: content: [")
            with pytest.raises(ConfigError):
                load_config(Path(path))
        finally:
            os.close(fd)
            os.unlink(path)

    def test_missing_required_section(self):
        """Test that ConfigError is raised for missing required sections."""
        invalid_config = {
            "paths": {
                "raw": "data/raw",
                "processed": "data/processed",
                "results": "data/results",
                "simulations": "data/simulations",
                "figures": "figures"
            },
            # Missing 'seeds' and 'constants'
        }
        config_path = create_temp_config(invalid_config)
        
        try:
            with pytest.raises(ConfigError) as exc_info:
                load_config(config_path)
            assert "Missing required configuration sections" in str(exc_info.value)
        finally:
            config_path.unlink()

    def test_missing_required_subkey(self):
        """Test that ConfigError is raised for missing required sub-keys."""
        invalid_config = {
            "paths": {
                "raw": "data/raw",
                "processed": "data/processed",
                "results": "data/results",
                "simulations": "data/simulations",
                "figures": "figures"
            },
            "seeds": {
                "random": 42
                # Missing 'numpy'
            },
            "constants": {
                "sme_coefficient": 1e-5,
                "l_max": 200
            }
        }
        config_path = create_temp_config(invalid_config)
        
        try:
            with pytest.raises(ConfigError) as exc_info:
                load_config(config_path)
            assert "Missing required keys in 'seeds'" in str(exc_info.value)
        finally:
            config_path.unlink()

    def test_non_dict_config(self):
        """Test that ConfigError is raised if config is not a dictionary."""
        fd, path = tempfile.mkstemp(suffix=".yaml")
        try:
            with os.fdopen(fd, "w") as f:
                f.write("- item1\n- item2\n")
            with pytest.raises(ConfigError):
                load_config(Path(path))
        finally:
            os.close(fd)
            os.unlink(path)


class TestGetConfigValue:
    """Tests for the get_config_value function."""

    def test_get_existing_value(self):
        """Test retrieving an existing value."""
        config = {
            "paths": {"raw": "data/raw"},
            "seeds": {"random": 42}
        }
        assert get_config_value(config, "paths.raw") == "data/raw"
        assert get_config_value(config, "seeds.random") == 42

    def test_get_non_existing_value_default(self):
        """Test retrieving a non-existing value returns default."""
        config = {"paths": {"raw": "data/raw"}}
        assert get_config_value(config, "nonexistent.key", "default") == "default"

    def test_get_non_existing_value_no_default(self):
        """Test retrieving a non-existing value returns None."""
        config = {"paths": {"raw": "data/raw"}}
        assert get_config_value(config, "nonexistent.key") is None

    def test_nested_missing_key(self):
        """Test retrieving a value where an intermediate key is missing."""
        config = {"paths": {}}
        assert get_config_value(config, "paths.raw", "default") == "default"
