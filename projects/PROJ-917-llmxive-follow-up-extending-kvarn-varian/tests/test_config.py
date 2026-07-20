"""
Tests for configuration management.

These tests verify that the Config class properly initializes
with defaults, loads from environment, and validates inputs.
"""

import pytest
import os
import json
from pathlib import Path
import tempfile

from config import Config, get_config, set_config, reset_config


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_cpu_only(self):
        """Test that CPU_ONLY defaults to True."""
        config = Config()
        assert config.CPU_ONLY is True

    def test_default_epsilon_floor(self):
        """Test that EPSILON_FLOOR defaults to 1e-6."""
        config = Config()
        assert config.EPSILON_FLOOR == 1e-6

    def test_default_random_seed(self):
        """Test that RANDOM_SEED defaults to 42."""
        config = Config()
        assert config.RANDOM_SEED == 42

    def test_default_directories(self):
        """Test that default directories are set correctly."""
        config = Config()
        assert config.DATA_DIR == "data"
        assert config.MODEL_DIR == "data/models"
        assert config.OUTPUT_DIR == "data/analysis"

    def test_default_simulation_params(self):
        """Test that default simulation parameters are set correctly."""
        config = Config()
        assert config.MAX_STEPS == 1000
        assert config.BATCH_SIZE == 32


class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_epsilon_floor_negative(self):
        """Test that negative epsilon floor raises ValueError."""
        with pytest.raises(ValueError):
            Config(EPSILON_FLOOR=-1e-6)

    def test_invalid_epsilon_floor_zero(self):
        """Test that zero epsilon floor raises ValueError."""
        with pytest.raises(ValueError):
            Config(EPSILON_FLOOR=0)

    def test_invalid_random_seed_type(self):
        """Test that non-integer seed raises TypeError."""
        with pytest.raises(TypeError):
            Config(RANDOM_SEED="42")

    def test_invalid_log_level(self):
        """Test that invalid log level is handled gracefully."""
        # Should not raise, but log a warning
        config = Config(LOG_LEVEL="INVALID")
        assert config.LOG_LEVEL == "INVALID"


class TestConfigSerialization:
    """Test configuration serialization."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = Config()
        config_dict = config.to_dict()

        assert "CPU_ONLY" in config_dict
        assert "EPSILON_FLOOR" in config_dict
        assert "RANDOM_SEED" in config_dict
        assert config_dict["CPU_ONLY"] is True
        assert config_dict["EPSILON_FLOOR"] == 1e-6
        assert config_dict["RANDOM_SEED"] == 42

    def test_save_and_load_file(self):
        """Test saving and loading configuration from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.json"

            config = Config(RANDOM_SEED=123, EPSILON_FLOOR=1e-8)
            config.save_to_file(str(filepath))

            loaded_config = Config.load_from_file(str(filepath))

            assert loaded_config.RANDOM_SEED == 123
            assert loaded_config.EPSILON_FLOOR == 1e-8

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            Config.load_from_file("/nonexistent/path/config.json")


class TestConfigEnvironment:
    """Test configuration from environment variables."""

    def test_from_env_with_variables(self):
        """Test loading configuration from environment variables."""
        # Set environment variables
        os.environ["LLMXIVE_CPU_ONLY"] = "False"
        os.environ["LLMXIVE_EPSILON_FLOOR"] = "1e-8"
        os.environ["LLMXIVE_RANDOM_SEED"] = "999"

        try:
            config = Config.from_env()

            assert config.CPU_ONLY is False
            assert config.EPSILON_FLOOR == 1e-8
            assert config.RANDOM_SEED == 999
        finally:
            # Clean up environment variables
            for key in ["LLMXIVE_CPU_ONLY", "LLMXIVE_EPSILON_FLOOR", "LLMXIVE_RANDOM_SEED"]:
                os.environ.pop(key, None)

    def test_from_env_partial(self):
        """Test loading configuration with partial environment variables."""
        os.environ["LLMXIVE_RANDOM_SEED"] = "777"

        try:
            config = Config.from_env()

            # Should use env value
            assert config.RANDOM_SEED == 777
            # Should use default for others
            assert config.CPU_ONLY is True
            assert config.EPSILON_FLOOR == 1e-6
        finally:
            os.environ.pop("LLMXIVE_RANDOM_SEED", None)


class TestGlobalConfig:
    """Test global configuration management."""

    def setup_method(self):
        """Reset global config before each test."""
        reset_config()

    def teardown_method(self):
        """Clean up after each test."""
        reset_config()

    def test_get_config_creates_default(self):
        """Test that get_config creates a default config if none exists."""
        config = get_config()
        assert config is not None
        assert config.RANDOM_SEED == 42

    def test_set_config_updates_global(self):
        """Test that set_config updates the global configuration."""
        new_config = Config(RANDOM_SEED=123)
        set_config(new_config)

        retrieved_config = get_config()
        assert retrieved_config.RANDOM_SEED == 123

    def test_reset_config_clears_global(self):
        """Test that reset_config clears the global configuration."""
        set_config(Config(RANDOM_SEED=123))
        reset_config()

        # Should create a new default config
        config = get_config()
        assert config.RANDOM_SEED == 42