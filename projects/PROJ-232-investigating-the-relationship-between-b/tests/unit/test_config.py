"""
Unit tests for environment configuration management.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.utils.config import (
    EnvironmentConfig,
    ConfigError,
    get_config,
    reload_config,
)


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig class."""

    def test_load_from_system_env(self, monkeypatch):
        """Test loading configuration from system environment variables."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "test_key_123")
        monkeypatch.setenv("DATA_DIR", "/custom/data")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        config = EnvironmentConfig()

        assert config.openneuro_api_key == "test_key_123"
        assert config.data_dir == Path("/custom/data")
        assert config.log_level == "DEBUG"

    def test_missing_required_variable(self, monkeypatch):
        """Test that missing required variable raises ConfigError."""
        # Clear any existing OPENNEURO_API_KEY
        monkeypatch.delenv("OPENNEURO_API_KEY", raising=False)

        with pytest.raises(ConfigError) as exc_info:
            EnvironmentConfig()

        assert "OPENNERO_API_KEY" in str(exc_info.value) or "OPENNEURO_API_KEY" in str(exc_info.value)

    def test_default_values(self, monkeypatch):
        """Test that optional variables get default values."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "test_key")

        config = EnvironmentConfig()

        assert config.data_dir == Path("./data").resolve()
        assert config.output_dir == Path("./data/output").resolve()
        assert config.log_level == "INFO"
        assert config.seed == 42

    def test_get_with_default(self, monkeypatch):
        """Test get method with default value."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "test_key")

        config = EnvironmentConfig()

        # Existing key
        assert config.get("OPENNEURO_API_KEY") == "test_key"

        # Non-existing key with default
        assert config.get("NON_EXISTENT_KEY", "default_val") == "default_val"

        # Non-existing key without default (should raise)
        with pytest.raises(ConfigError):
            config.get("NON_EXISTENT_KEY")

    def test_get_int(self, monkeypatch):
        """Test get_int method."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "test_key")
        monkeypatch.setenv("SEED", "12345")

        config = EnvironmentConfig()

        assert config.get_int("SEED") == 12345
        assert config.get_int("NON_EXISTENT", 999) == 999

        # Invalid integer
        monkeypatch.setenv("BAD_INT", "not_a_number")
        config2 = EnvironmentConfig()
        with pytest.raises(ConfigError):
            config2.get_int("BAD_INT")

    def test_get_float(self, monkeypatch):
        """Test get_float method."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "test_key")
        monkeypatch.setenv("FLOAT_VAL", "3.14159")

        config = EnvironmentConfig()

        assert abs(config.get_float("FLOAT_VAL") - 3.14159) < 0.0001
        assert config.get_float("NON_EXISTENT", 2.71) == 2.71

    def test_get_path(self, monkeypatch):
        """Test get_path method."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "test_key")
        monkeypatch.setenv("CUSTOM_PATH", "/some/path")

        config = EnvironmentConfig()

        assert config.get_path("CUSTOM_PATH") == Path("/some/path")
        assert config.get_path("NON_EXISTENT", "/default/path") == Path("/default/path")

    def test_ensure_directories(self, tmp_path, monkeypatch):
        """Test that ensure_directories creates missing directories."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "test_key")
        monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "output"))
        monkeypatch.setenv("FIGURES_DIR", str(tmp_path / "figures"))

        config = EnvironmentConfig()
        config.ensure_directories()

        assert (tmp_path / "data").exists()
        assert (tmp_path / "output").exists()
        assert (tmp_path / "figures").exists()

    def test_to_dict_masks_secrets(self, monkeypatch):
        """Test that to_dict masks sensitive values."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "secret_key_123")
        monkeypatch.setenv("DATA_DIR", "/data")

        config = EnvironmentConfig()
        config_dict = config.to_dict()

        assert config_dict["OPENNEURO_API_KEY"] == "***"
        assert config_dict["DATA_DIR"] == "/data"

    def test_load_from_env_file(self, tmp_path):
        """Test loading configuration from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OPENNEURO_API_KEY=file_key_456\n"
            "DATA_DIR=/file/data\n"
            "LOG_LEVEL=WARNING\n"
            'QUOTED_KEY="quoted_value"\n'
            "SINGLE_QUOTED='single_quoted_value'\n"
        )

        config = EnvironmentConfig(env_file)

        assert config.openneuro_api_key == "file_key_456"
        assert config.data_dir == Path("/file/data")
        assert config.log_level == "WARNING"

    def test_env_file_with_comments(self, tmp_path):
        """Test that .env file parsing ignores comments."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# This is a comment\n"
            "OPENNEURO_API_KEY=comment_test_key\n"
            "# Another comment\n"
            "DATA_DIR=/comment/data\n"
        )

        config = EnvironmentConfig(env_file)

        assert config.openneuro_api_key == "comment_test_key"

    def test_env_file_empty_lines(self, tmp_path):
        """Test that .env file parsing ignores empty lines."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "\n"
            "OPENNEURO_API_KEY=empty_line_key\n"
            "\n"
            "DATA_DIR=/empty/data\n"
            "\n"
        )

        config = EnvironmentConfig(env_file)

        assert config.openneuro_api_key == "empty_line_key"

class TestGlobalConfig:
    """Tests for global config functions."""

    def test_get_config_singleton(self, monkeypatch):
        """Test that get_config returns singleton instance."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "singleton_test_key")

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_reload_config(self, monkeypatch):
        """Test that reload_config creates new instance."""
        monkeypatch.setenv("OPENNEURO_API_KEY", "reload_test_key")

        config1 = reload_config()
        config2 = reload_config()

        assert config1 is not config2

    def test_get_config_creates_if_none(self, monkeypatch):
        """Test that get_config creates instance if none exists."""
        # Reset global instance
        import src.utils.config as config_module
        config_module._config_instance = None

        monkeypatch.setenv("OPENNEURO_API_KEY", "new_instance_key")

        config = get_config()

        assert config is not None
        assert config.openneuro_api_key == "new_instance_key"
