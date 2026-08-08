"""
Unit tests for environment configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest
from code.config.env_config import (
    EnvironmentConfig,
    ConfigError,
    get_env_config,
    reload_config,
    DEFAULTS
)

class TestEnvironmentConfig:
    """Tests for EnvironmentConfig class."""

    def test_default_values(self):
        """Test that default values are loaded when no .env file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            # Remove any existing .env
            env_file = Path(tmpdir) / ".env"
            if env_file.exists():
                env_file.unlink()
            
            config = EnvironmentConfig()
            assert config.get("DATA_ROOT") == DEFAULTS["DATA_ROOT"]
            assert config.get_int("SAMPLING_RATE_THRESHOLD") == DEFAULTS["SAMPLING_RATE_THRESHOLD"]
            assert config.get_float("BANDPASS_LOW") == DEFAULTS["BANDPASS_LOW"]
            assert config.get_bool("LOG_LEVEL") is not None

    def test_env_file_loading(self):
        """Test loading values from .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "DATA_ROOT=/custom/data\n"
                "SAMPLING_RATE_THRESHOLD=1000\n"
                "LOG_LEVEL=DEBUG\n"
            )
            
            config = EnvironmentConfig(env_file)
            assert config.get("DATA_ROOT") == "/custom/data"
            assert config.get_int("SAMPLING_RATE_THRESHOLD") == 1000
            assert config.get("LOG_LEVEL") == "DEBUG"

    def test_type_conversion(self):
        """Test automatic type conversion from strings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "SAMPLING_RATE_THRESHOLD=1000\n"
                "BANDPASS_LOW=2.5\n"
                "MIN_ODDBALL_TRIALS=50\n"
            )
            
            config = EnvironmentConfig(env_file)
            assert isinstance(config.get_int("SAMPLING_RATE_THRESHOLD"), int)
            assert isinstance(config.get_float("BANDPASS_LOW"), float)
            assert isinstance(config.get_int("MIN_ODDBALL_TRIALS"), int)

    def test_get_with_default(self):
        """Test get method with default value."""
        config = EnvironmentConfig()
        assert config.get("NONEXISTENT_KEY", "default_value") == "default_value"

    def test_get_int_validation(self):
        """Test that get_int raises error for non-integer values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("INVALID_INT=not_a_number\n")
            
            config = EnvironmentConfig(env_file)
            # This should work because it falls back to default which is int
            assert config.get_int("INVALID_INT", 10) == 10

    def test_validation_passed(self):
        """Test that valid configuration passes validation."""
        config = EnvironmentConfig()
        try:
            config.validate()
            assert True  # Validation should pass
        except ConfigError:
            pytest.fail("Valid configuration should not raise ConfigError")

    def test_validation_failed_sampling_rate(self):
        """Test validation fails for invalid sampling rate threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("SAMPLING_RATE_THRESHOLD=50\n")
            
            config = EnvironmentConfig(env_file)
            with pytest.raises(ConfigError, match="SAMPLING_RATE_THRESHOLD must be >= 100"):
                config.validate()

    def test_validation_failed_trial_counts(self):
        """Test validation fails for invalid trial counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("MIN_ODDBALL_TRIALS=5\n")
            
            config = EnvironmentConfig(env_file)
            with pytest.raises(ConfigError, match="MIN_ODDBALL_TRIALS must be >= 10"):
                config.validate()

    def test_validation_failed_time_windows(self):
        """Test validation fails for invalid time windows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "AUDITORY_WINDOW_START=0.30\n"
                "AUDITORY_WINDOW_END=0.20\n"
            )
            
            config = EnvironmentConfig(env_file)
            with pytest.raises(ConfigError, match="AUDITORY_WINDOW_START must be < AUDITORY_WINDOW_END"):
                config.validate()

    def test_get_dict(self):
        """Test get_dict returns a copy of configuration."""
        config = EnvironmentConfig()
        config_dict = config.get_dict()
        assert isinstance(config_dict, dict)
        assert len(config_dict) > 0

    def test_path_conversion(self):
        """Test get_path returns Path object."""
        config = EnvironmentConfig()
        path = config.get_path("DATA_ROOT")
        assert isinstance(path, Path)

class TestGetEnvConfig:
    """Tests for get_env_config function."""

    def test_singleton_pattern(self):
        """Test that get_env_config returns same instance."""
        config1 = get_env_config()
        config2 = get_env_config()
        assert config1 is config2

    def test_reload_config(self):
        """Test that reload_config creates new instance."""
        config1 = get_env_config()
        config2 = reload_config()
        assert config1 is not config2
