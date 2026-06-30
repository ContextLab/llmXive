"""
Tests for environment configuration management in utils.py.
"""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from utils import load_config, _parse_env_value


class TestParseEnvValue:
    """Tests for the _parse_env_value helper function."""

    def test_parse_boolean_true(self):
        assert _parse_env_value("true") is True
        assert _parse_env_value("True") is True
        assert _parse_env_value("TRUE") is True
        assert _parse_env_value("yes") is True
        assert _parse_env_value("1") is True

    def test_parse_boolean_false(self):
        assert _parse_env_value("false") is False
        assert _parse_env_value("False") is False
        assert _parse_env_value("FALSE") is False
        assert _parse_env_value("no") is False
        assert _parse_env_value("0") is False

    def test_parse_integer(self):
        assert _parse_env_value("42") == 42
        assert _parse_env_value("-10") == -10

    def test_parse_float(self):
        assert _parse_env_value("3.14") == pytest.approx(3.14)
        assert _parse_env_value("-2.5") == pytest.approx(-2.5)

    def test_parse_none(self):
        assert _parse_env_value("null") is None
        assert _parse_env_value("none") is None
        assert _parse_env_value("") is None

    def test_parse_string(self):
        assert _parse_env_value("hello") == "hello"
        assert _parse_env_value("path/to/file") == "path/to/file"


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_from_file(self, tmp_path):
        """Test loading configuration from a YAML file."""
        config_data = {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "logging": {
                "level": "INFO"
            },
            "feature_flags": {
                "enable_cache": True
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(str(config_file))

        assert config["database"]["host"] == "localhost"
        assert config["database"]["port"] == 5432
        assert config["logging"]["level"] == "INFO"
        assert config["feature_flags"]["enable_cache"] is True

    def test_load_config_from_env(self, tmp_path, monkeypatch):
        """Test that environment variables override file config."""
        # Create a base config file
        config_data = {
            "database": {
                "host": "localhost",
                "port": 5432
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Set environment variables to override
        monkeypatch.setenv("LLMXIVE_DATABASE_HOST", "production-db.example.com")
        monkeypatch.setenv("LLMXIVE_DATABASE_PORT", "3306")
        monkeypatch.setenv("LLMXIVE_NEW_KEY", "new_value")

        config = load_config(str(config_file))

        assert config["database"]["host"] == "production-db.example.com"
        assert config["database"]["port"] == 3306
        assert config["new_key"] == "new_value"

    def test_load_config_nested_env(self, tmp_path, monkeypatch):
        """Test nested environment variable mapping."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()  # Empty config

        monkeypatch.setenv("LLMXIVE_DATABASE_CONNECTION_TIMEOUT", "30")
        monkeypatch.setenv("LLMXIVE_DATABASE_RETRIES", "3")

        config = load_config(str(config_file))

        assert config["database"]["connection"]["timeout"] == 30
        assert config["database"]["retries"] == 3

    def test_load_config_missing_file(self, tmp_path):
        """Test handling of missing config file."""
        config = load_config(str(tmp_path / "nonexistent.yaml"))
        assert config == {}

    def test_load_config_default_path(self, monkeypatch):
        """Test that default path 'config.yaml' is used when none provided."""
        # This test assumes config.yaml doesn't exist in the current dir
        # We just verify it doesn't crash
        config = load_config()
        assert isinstance(config, dict)

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test handling of invalid YAML file."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(Exception):  # yaml.YAMLError
            load_config(str(config_file))

    def test_load_config_custom_prefix(self, tmp_path, monkeypatch):
        """Test using a custom environment variable prefix."""
        config_file = tmp_path / "config.yaml"
        config_file.touch()

        monkeypatch.setenv("CUSTOM_PREFIX_VALUE", "custom_val")

        config = load_config(str(config_file), env_prefix="CUSTOM_PREFIX_")

        assert config["value"] == "custom_val"
