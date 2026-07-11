"""
Tests for environment configuration management.

These tests verify that PYTHONHASHSEED and random seeds are properly set
and that the environment is configured for reproducible research.
"""

import os
import random
import tempfile
from pathlib import Path

import numpy as np
import pytest
import yaml

# Import the module under test
from environment_config import (
    load_environment_config,
    set_python_hash_seed,
    set_random_seeds,
    validate_seed_environment,
    initialize_environment,
    create_default_config_file,
    DEFAULT_SEED,
    DEFAULT_HASH_SEED,
)


class TestLoadEnvironmentConfig:
    def test_load_default_config_when_file_not_exists(self):
        """Test that default config is returned when file doesn't exist."""
        config = load_environment_config("/nonexistent/path/config.yaml")
        assert config["random_seed"] == DEFAULT_SEED
        assert config["hash_seed"] == DEFAULT_HASH_SEED
        assert config["numpy_seed"] == DEFAULT_SEED

    def test_load_config_from_file(self):
        """Test loading configuration from a YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "random_seed": 123,
                "hash_seed": "456",
                "numpy_seed": 789
            }
            yaml.dump(config_data, f)
            f.flush()

            config = load_environment_config(f.name)
            assert config["random_seed"] == 123
            assert config["hash_seed"] == "456"
            assert config["numpy_seed"] == 789

            os.unlink(f.name)

    def test_load_config_with_missing_keys(self):
        """Test that missing keys are filled with defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "random_seed": 999
            }
            yaml.dump(config_data, f)
            f.flush()

            config = load_environment_config(f.name)
            assert config["random_seed"] == 999
            assert config["hash_seed"] == DEFAULT_HASH_SEED
            assert config["numpy_seed"] == DEFAULT_SEED

            os.unlink(f.name)


class TestSetPythonHashSeed:
    def test_set_hash_seed(self):
        """Test setting PYTHONHASHSEED."""
        # Clear existing env var if present
        original = os.environ.pop("PYTHONHASHSEED", None)

        set_python_hash_seed("999")
        assert os.environ.get("PYTHONHASHSEED") == "999"

        # Restore original
        if original:
            os.environ["PYTHONHASHSEED"] = original
        else:
            os.environ.pop("PYTHONHASHSEED", None)

    def test_set_hash_seed_from_config(self):
        """Test setting PYTHONHASHSEED from config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "hash_seed": "777",
                "random_seed": 42,
                "numpy_seed": 42
            }
            yaml.dump(config_data, f)
            f.flush()

            # Clear existing env var
            original = os.environ.pop("PYTHONHASHSEED", None)

            config = load_environment_config(f.name)
            set_python_hash_seed(config.get("hash_seed"))
            assert os.environ.get("PYTHONHASHSEED") == "777"

            os.unlink(f.name)

            # Restore original
            if original:
                os.environ["PYTHONHASHSEED"] = original


class TestSetRandomSeeds:
    def test_set_random_seeds(self):
        """Test setting random seeds for Python and NumPy."""
        config = {
            "random_seed": 12345,
            "numpy_seed": 12345
        }

        set_random_seeds(config)

        # Generate a random number
        val1 = random.random()
        val2 = np.random.random()

        # Reset seeds
        set_random_seeds(config)

        # Generate again
        val3 = random.random()
        val4 = np.random.random()

        # Should be identical
        assert val1 == val3
        assert val2 == val4

    def test_set_random_seeds_default_config(self):
        """Test setting random seeds with default config."""
        # This should work without errors
        set_random_seeds()


class TestValidateSeedEnvironment:
    def test_validate_with_hash_seed_set(self):
        """Test validation when PYTHONHASHSEED is set."""
        original = os.environ.get("PYTHONHASHSEED")
        os.environ["PYTHONHASHSEED"] = "42"

        result = validate_seed_environment()
        assert result is True

        if original:
            os.environ["PYTHONHASHSEED"] = original
        else:
            os.environ.pop("PYTHONHASHSEED", None)

    def test_validate_without_hash_seed(self):
        """Test validation when PYTHONHASHSEED is not set."""
        original = os.environ.pop("PYTHONHASHSEED", None)

        result = validate_seed_environment()
        assert result is False

        if original:
            os.environ["PYTHONHASHSEED"] = original


class TestInitializeEnvironment:
    def test_initialize_environment(self):
        """Test full environment initialization."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "random_seed": 54321,
                "hash_seed": "54321",
                "numpy_seed": 54321
            }
            yaml.dump(config_data, f)
            f.flush()

            # Clear existing env vars
            original_hash = os.environ.pop("PYTHONHASHSEED", None)

            config = initialize_environment(f.name)

            assert config["random_seed"] == 54321
            assert os.environ.get("PYTHONHASHSEED") == "54321"

            os.unlink(f.name)

            if original_hash:
                os.environ["PYTHONHASHSEED"] = original_hash


class TestCreateDefaultConfigFile:
    def test_create_default_config_file(self):
        """Test creating a default configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_config.yaml"
            created_path = create_default_config_file(str(output_path))

            assert created_path.exists()
            assert created_path == output_path

            with open(created_path, 'r') as f:
                config = yaml.safe_load(f)

            assert config["random_seed"] == DEFAULT_SEED
            assert config["hash_seed"] == DEFAULT_HASH_SEED
            assert "description" in config