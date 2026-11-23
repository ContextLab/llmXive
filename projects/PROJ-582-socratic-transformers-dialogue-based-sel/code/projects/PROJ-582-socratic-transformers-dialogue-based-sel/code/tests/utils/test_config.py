"""
Tests for the configuration management module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.config import (
    SocraticConfig,
    load_config_from_env,
    get_config,
    set_global_config,
    set_seed,
    init_project,
)


class TestSocraticConfig:
    """Tests for the SocraticConfig dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = SocraticConfig()
        assert config.seed == 42
        assert config.log_level == "INFO"
        assert config.max_tokens == 512
        assert config.batch_size == 1
        assert config.gradient_accumulation_steps == 4
        assert config.learning_rate == 2e-5
        assert config.num_epochs == 3
        assert config.use_4bit is True
        assert config.cpu_offload is True
        assert "gsm8k" in config.datasets
        assert "math" in config.datasets

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = SocraticConfig(seed=123, log_level="DEBUG")
        config_dict = config.to_dict()

        assert config_dict["seed"] == 123
        assert config_dict["log_level"] == "DEBUG"
        assert isinstance(config_dict["project_root"], str)
        assert isinstance(config_dict["data_dir"], str)

    def test_paths_are_absolute(self):
        """Test that all paths are absolute."""
        config = SocraticConfig()
        assert config.project_root.is_absolute()
        assert config.data_dir.is_absolute()
        assert config.model_cache_dir.is_absolute()
        assert config.output_dir.is_absolute()


class TestLoadConfigFromEnv:
    """Tests for loading configuration from environment variables."""

    def test_seed_from_env(self):
        """Test that seed is loaded from environment variable."""
        with patch.dict(os.environ, {"SOCRATIC_SEED": "999"}):
            config = load_config_from_env()
            assert config.seed == 999

    def test_log_level_from_env(self):
        """Test that log level is loaded from environment variable."""
        with patch.dict(os.environ, {"SOCRATIC_LOG_LEVEL": "WARNING"}):
            config = load_config_from_env()
            assert config.log_level == "WARNING"

    def test_max_tokens_from_env(self):
        """Test that max tokens is loaded from environment variable."""
        with patch.dict(os.environ, {"SOCRATIC_MAX_TOKENS": "1024"}):
            config = load_config_from_env()
            assert config.max_tokens == 1024

    def test_batch_size_from_env(self):
        """Test that batch size is loaded from environment variable."""
        with patch.dict(os.environ, {"SOCRATIC_BATCH_SIZE": "8"}):
            config = load_config_from_env()
            assert config.batch_size == 8

    def test_use_4bit_from_env(self):
        """Test that use_4bit is loaded from environment variable."""
        with patch.dict(os.environ, {"SOCRATIC_USE_4BIT": "false"}):
            config = load_config_from_env()
            assert config.use_4bit is False

        with patch.dict(os.environ, {"SOCRATIC_USE_4BIT": "1"}):
            config = load_config_from_env()
            assert config.use_4bit is True

    def test_datasets_from_env(self):
        """Test that datasets are loaded from environment variable."""
        with patch.dict(os.environ, {"SOCRATIC_DATASETS": "custom1, custom2"}):
            config = load_config_from_env()
            assert "custom1" in config.datasets
            assert "custom2" in config.datasets

    def test_multiple_env_vars(self):
        """Test loading multiple environment variables at once."""
        env_vars = {
            "SOCRATIC_SEED": "777",
            "SOCRATIC_LOG_LEVEL": "ERROR",
            "SOCRATIC_MAX_TOKENS": "2048",
            "SOCRATIC_BATCH_SIZE": "4",
            "SOCRATIC_LEARNING_RATE": "1e-4",
        }
        with patch.dict(os.environ, env_vars):
            config = load_config_from_env()
            assert config.seed == 777
            assert config.log_level == "ERROR"
            assert config.max_tokens == 2048
            assert config.batch_size == 4
            assert config.learning_rate == 1e-4


class TestGlobalConfig:
    """Tests for global configuration management."""

    def test_get_config_initializes(self):
        """Test that get_config initializes the global config if needed."""
        # Clear global config
        set_global_config(None)
        config = get_config()
        assert config is not None
        assert isinstance(config, SocraticConfig)

    def test_set_global_config(self):
        """Test setting a custom global config."""
        custom_config = SocraticConfig(seed=12345)
        set_global_config(custom_config)

        retrieved_config = get_config()
        assert retrieved_config.seed == 12345

    def test_get_config_caches(self):
        """Test that get_config caches the config."""
        set_global_config(None)
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2


class TestSetSeed:
    """Tests for seed setting functionality."""

    def test_set_seed_with_value(self):
        """Test setting seed with a specific value."""
        set_seed(42)
        # Verify random module seed
        assert random.randint(0, 100) == random.randint(0, 100)  # This will fail if seeds are different
        # Reset and test again
        set_seed(42)
        val1 = random.randint(0, 100)
        set_seed(42)
        val2 = random.randint(0, 100)
        assert val1 == val2

    def test_set_seed_uses_global_config(self):
        """Test that set_seed uses global config seed when no value provided."""
        custom_config = SocraticConfig(seed=99999)
        set_global_config(custom_config)

        set_seed()  # Should use config seed
        val1 = random.randint(0, 100000)

        set_seed()  # Reset and get again
        val2 = random.randint(0, 100000)

        assert val1 == val2


class TestInitProject:
    """Tests for project initialization."""

    def test_creates_directories(self, tmp_path):
        """Test that init_project creates necessary directories."""
        # Create a temporary project structure
        with patch("src.utils.config.PROJECT_ROOT", tmp_path):
            set_global_config(None)
            init_project()

            config = get_config()
            assert config.data_dir.exists()
            assert (config.data_dir / "raw").exists()
            assert (config.data_dir / "processed").exists()
            assert (config.data_dir / "results").exists()
            assert config.model_cache_dir.exists()
            assert config.output_dir.exists()