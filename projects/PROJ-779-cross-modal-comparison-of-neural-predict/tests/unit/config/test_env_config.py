"""
Unit tests for environment configuration management (T010).
"""
import os
import tempfile
from pathlib import Path
import pytest

from code.config.env_config import (
    EnvironmentConfig,
    ConfigError,
    get_env_config,
    reload_config
)


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig class."""

    def test_load_from_env_file(self, tmp_path):
        """Test loading configuration from a custom .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "SAMPLING_RATE_THRESHOLD=600\n"
            "MIN_ODDBALL_TRIALS=150\n"
            "LOG_LEVEL=DEBUG\n"
        )

        config = EnvironmentConfig(env_file)

        assert config.get("SAMPLING_RATE_THRESHOLD") == 600
        assert config.get("MIN_ODDBALL_TRIALS") == 150
        assert config.get("LOG_LEVEL") == "DEBUG"

    def test_defaults_when_no_env_file(self):
        """Test that defaults are used when .env file is missing."""
        # Use a non-existent path to force defaults
        config = EnvironmentConfig(Path("/nonexistent/.env"))

        assert config.get("SAMPLING_RATE_THRESHOLD") == 500
        assert config.get("MIN_ODDBALL_TRIALS") == 100
        assert config.get("MIN_STANDARD_TRIALS") == 300
        assert config.get("LOG_LEVEL") == "INFO"

    def test_real_data_only_default(self):
        """Test that REAL_DATA_ONLY defaults to True."""
        config = EnvironmentConfig(Path("/nonexistent/.env"))
        assert config.get("REAL_DATA_ONLY") is True

    def test_real_data_only_false_in_env(self, tmp_path):
        """Test that REAL_DATA_ONLY can be set to False in env (for testing)."""
        env_file = tmp_path / ".env"
        env_file.write_text("REAL_DATA_ONLY=false\n")

        config = EnvironmentConfig(env_file)
        assert config.get("REAL_DATA_ONLY") is False

    def test_invalid_sampling_rate(self, tmp_path):
        """Test that invalid sampling rate raises ConfigError."""
        env_file = tmp_path / ".env"
        env_file.write_text("SAMPLING_RATE_THRESHOLD=50\n")

        with pytest.raises(ConfigError, match="SAMPLING_RATE_THRESHOLD must be >= 100 Hz"):
            EnvironmentConfig(env_file)

    def test_invalid_min_trials(self, tmp_path):
        """Test that invalid trial counts raise ConfigError."""
        env_file = tmp_path / ".env"
        env_file.write_text("MIN_ODDBALL_TRIALS=5\n")

        with pytest.raises(ConfigError, match="MIN_ODDBALL_TRIALS must be >= 10"):
            EnvironmentConfig(env_file)

    def test_as_dict(self, tmp_path):
        """Test that as_dict returns a copy of config."""
        env_file = tmp_path / ".env"
        env_file.write_text("LOG_LEVEL=WARN\n")

        config = EnvironmentConfig(env_file)
        d = config.as_dict()

        assert "LOG_LEVEL" in d
        assert d["LOG_LEVEL"] == "WARN"

        # Modify returned dict should not affect config
        d["LOG_LEVEL"] = "ERROR"
        assert config.get("LOG_LEVEL") == "WARN"


class TestGetEnvConfig:
    """Tests for get_env_config singleton function."""

    def test_singleton_behavior(self, tmp_path):
        """Test that get_env_config returns the same instance."""
        env_file = tmp_path / ".env"
        env_file.write_text("LOG_LEVEL=INFO\n")

        config1 = get_env_config(env_file)
        config2 = get_env_config(env_file)

        assert config1 is config2

    def test_reload_creates_new_instance(self, tmp_path):
        """Test that reload_config creates a new instance."""
        env_file = tmp_path / ".env"
        env_file.write_text("LOG_LEVEL=INFO\n")

        config1 = get_env_config(env_file)
        config2 = reload_config(env_file)

        assert config1 is not config2
        # Both should have same values though
        assert config1.get("LOG_LEVEL") == config2.get("LOG_LEVEL")
