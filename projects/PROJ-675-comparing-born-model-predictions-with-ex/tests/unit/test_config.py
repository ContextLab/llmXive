"""
Unit tests for the configuration management module (T006).

Verifies that config loading, seed setting, and path resolution work correctly.
"""
import os
import tempfile
from pathlib import Path
import yaml

import pytest

# Import the module under test
# We assume the test is run from the project root or code is in PYTHONPATH
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import (
    load_config,
    initialize_environment,
    ConfigError,
    DEFAULT_CONFIG
)


class TestConfigLoading:
    """Tests for load_config function."""

    def test_load_default_when_missing(self, tmp_path):
        """Test that defaults are returned if config file is missing."""
        # Change to a temp directory with no config.yaml
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            cfg = load_config()
            assert cfg["random_seed"] == DEFAULT_CONFIG["random_seed"]
            assert cfg["log_level"] == DEFAULT_CONFIG["log_level"]
        finally:
            os.chdir(original_cwd)

    def test_load_from_file(self, tmp_path):
        """Test loading configuration from a specific file."""
        config_content = {
            "data_path": "custom_data",
            "code_path": "custom_code",
            "random_seed": 123,
            "log_level": "DEBUG"
        }
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        cfg = load_config(config_file)
        assert cfg["data_path"] == "custom_data"
        assert cfg["random_seed"] == 123
        assert cfg["log_level"] == "DEBUG"

    def test_missing_required_field(self, tmp_path):
        """Test that missing required fields raise ConfigError."""
        config_content = {
            "data_path": "data",
            "code_path": "code"
            # Missing random_seed and log_level
        }
        config_file = tmp_path / "bad_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ConfigError, match="Missing required config fields"):
            load_config(config_file)

    def test_invalid_seed_type(self, tmp_path):
        """Test that non-integer seed raises ConfigError."""
        config_content = {
            "data_path": "data",
            "code_path": "code",
            "random_seed": "not_an_int",
            "log_level": "INFO"
        }
        config_file = tmp_path / "bad_seed.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ConfigError, match="random_seed must be an integer"):
            load_config(config_file)

    def test_invalid_log_level(self, tmp_path):
        """Test that invalid log level raises ConfigError."""
        config_content = {
            "data_path": "data",
            "code_path": "code",
            "random_seed": 42,
            "log_level": "VERBOSE"
        }
        config_file = tmp_path / "bad_level.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ConfigError, match="log_level must be one of"):
            load_config(config_file)


class TestEnvironmentInitialization:
    """Tests for initialize_environment function."""

    def test_sets_random_seeds(self, tmp_path):
        """Test that initialization sets random seeds."""
        config_content = {
            "data_path": "data",
            "code_path": "code",
            "random_seed": 999,
            "log_level": "INFO"
        }
        config_file = tmp_path / "seed_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            cfg = initialize_environment(config_file)
            # Verify seed is in config
            assert cfg["random_seed"] == 999
            
            # Verify random module seed
            r1 = random.random()
            # Reset and check again
            random.seed(999)
            r2 = random.random()
            assert r1 == r2
        finally:
            os.chdir(original_cwd)

    def test_resolves_paths(self, tmp_path):
        """Test that relative paths are resolved to absolute."""
        config_content = {
            "data_path": "data",
            "code_path": "code",
            "random_seed": 42,
            "log_level": "INFO"
        }
        config_file = tmp_path / "path_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            cfg = initialize_environment(config_file)
            # Check that path objects are absolute and point to correct subdirs
            assert cfg["data_path_obj"].is_absolute()
            assert cfg["code_path_obj"].is_absolute()
            assert cfg["data_path_obj"].name == "data"
            assert cfg["code_path_obj"].name == "code"
        finally:
            os.chdir(original_cwd)

import random