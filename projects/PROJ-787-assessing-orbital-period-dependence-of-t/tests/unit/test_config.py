"""
Unit tests for the configuration management module.
"""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from utils.config import (
    PipelineConfig,
    load_config,
    get_config,
    reset_config,
)


class TestPipelineConfigDataclass:
    """Tests for the PipelineConfig dataclass."""

    def test_default_values(self):
        """Test that PipelineConfig has correct default values."""
        config = PipelineConfig()
        assert config.data_dir == "data"
        assert config.raw_data_dir == "data/raw"
        assert config.processed_data_dir == "data/processed"
        assert config.log_level == "INFO"
        assert config.api_timeout == 60
        assert config.max_retries == 3
        assert config.parallel_workers == 4
        assert config.period_max_days == 100.0
        assert config.radius_uncertainty_threshold == 0.20
        assert config.bonferroni_alpha == 0.025

    def test_custom_values(self):
        """Test that PipelineConfig accepts custom values."""
        config = PipelineConfig(
            data_dir="/custom/data",
            log_level="DEBUG",
            api_timeout=120,
        )
        assert config.data_dir == "/custom/data"
        assert config.log_level == "DEBUG"
        assert config.api_timeout == 120


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_from_yaml_file(self, tmp_path):
        """Test loading configuration from a YAML file."""
        config_data = {
            "data_dir": "/custom/data",
            "log_level": "DEBUG",
            "api_timeout": 120,
            "max_retries": 5,
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(str(config_file))
        assert config.data_dir == "/custom/data"
        assert config.log_level == "DEBUG"
        assert config.api_timeout == 120
        assert config.max_retries == 5

    def test_load_config_missing_file_raises_error(self, tmp_path):
        """Test that loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config(str(tmp_path / "nonexistent.yaml"))

    def test_load_config_invalid_yaml_raises_error(self, tmp_path):
        """Test that invalid YAML raises ValueError."""
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        with pytest.raises(ValueError):
            load_config(str(config_file))

    def test_load_config_empty_file_returns_defaults(self, tmp_path):
        """Test that an empty YAML file returns default configuration."""
        config_file = tmp_path / "empty.yaml"
        with open(config_file, "w") as f:
            f.write("")

        config = load_config(str(config_file))
        assert config.data_dir == "data"  # Default value

    def test_load_config_partial_yaml(self, tmp_path):
        """Test that partial YAML updates only specified fields."""
        config_data = {
            "log_level": "WARNING",
        }

        config_file = tmp_path / "partial.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(str(config_file))
        assert config.log_level == "WARNING"
        assert config.data_dir == "data"  # Should remain default


class TestLoadConfigFromEnv:
    """Tests for environment variable override functionality."""

    def test_env_override(self, tmp_path, monkeypatch):
        """Test that environment variables override YAML and defaults."""
        monkeypatch.setenv("PIPELINE_LOG_LEVEL", "ERROR")
        monkeypatch.setenv("PIPELINE_API_TIMEOUT", "300")
        monkeypatch.setenv("PIPELINE_ENABLE_CACHE", "false")

        # Create a minimal config file
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({"data_dir": "/yaml/data"}, f)

        config = load_config(str(config_file))
        assert config.log_level == "ERROR"
        assert config.api_timeout == 300
        assert config.enable_cache is False
        assert config.data_dir == "/yaml/data"  # From YAML

    def test_env_boolean_parsing(self, monkeypatch):
        """Test that boolean environment variables are parsed correctly."""
        monkeypatch.setenv("PIPELINE_ENABLE_CACHE", "true")
        config = PipelineConfig()
        from utils.config import _update_config_from_env
        _update_config_from_env(config)
        assert config.enable_cache is True

        monkeypatch.setenv("PIPELINE_ENABLE_CACHE", "false")
        config = PipelineConfig()
        _update_config_from_env(config)
        assert config.enable_cache is False

        monkeypatch.setenv("PIPELINE_ENABLE_CACHE", "1")
        config = PipelineConfig()
        _update_config_from_env(config)
        assert config.enable_cache is True

        monkeypatch.setenv("PIPELINE_ENABLE_CACHE", "0")
        config = PipelineConfig()
        _update_config_from_env(config)
        assert config.enable_cache is False

    def test_env_invalid_value_ignored(self, monkeypatch):
        """Test that invalid environment variable values are ignored."""
        monkeypatch.setenv("PIPELINE_API_TIMEOUT", "not_a_number")
        config = PipelineConfig()
        from utils.config import _update_config_from_env
        _update_config_from_env(config)
        assert config.api_timeout == 60  # Default value


class TestGetConfig:
    """Tests for get_config singleton functionality."""

    def test_get_config_returns_instance(self):
        """Test that get_config returns a PipelineConfig instance."""
        config = get_config()
        assert isinstance(config, PipelineConfig)

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        reset_config()  # Ensure clean state
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self):
        """Test that reset_config clears the singleton cache."""
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        # Should be different instances after reset
        assert config1 is not config2 or config1 != config2