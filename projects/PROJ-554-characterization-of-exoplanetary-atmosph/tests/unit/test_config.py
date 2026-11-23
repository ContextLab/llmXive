"""
Unit tests for the configuration management module.
"""
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import random

# Import the module under test
from code.config import load_env_vars, set_random_seed, get_config, validate_config


class TestLoadEnvVars:
    def test_load_from_existing_file(self):
        """Test loading from an existing .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_VAR=test_value\n")
            f.write("ANOTHER_VAR=123\n")
            temp_path = f.name
        
        try:
            result = load_env_vars(temp_path)
            assert result is True
            assert os.getenv("TEST_VAR") == "test_value"
            assert os.getenv("ANOTHER_VAR") == "123"
        finally:
            os.unlink(temp_path)
            # Clean up environment
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]
            if "ANOTHER_VAR" in os.environ:
                del os.environ["ANOTHER_VAR"]

    def test_load_from_nonexistent_file(self):
        """Test loading from a non-existent .env file."""
        result = load_env_vars("/nonexistent/path/.env")
        assert result is False

    def test_load_default_path(self):
        """Test loading from the default path (project root)."""
        # This should not raise an error even if .env doesn't exist
        result = load_env_vars()
        # Returns True if loaded, False if not found (both acceptable here)
        assert isinstance(result, bool)


class TestSetRandomSeed:
    def test_set_seed_explicit(self):
        """Test setting seed with an explicit value."""
        seed_value = 12345
        result = set_random_seed(seed_value)
        
        assert result == seed_value
        assert random.random() < 1.0  # Just to ensure randomness is active
        
        # Reset to known state
        random.seed(seed_value)
        val1 = random.random()
        np.random.seed(seed_value)
        val2 = np.random.random()
        
        # Verify reproducibility
        random.seed(seed_value)
        assert random.random() == val1
        np.random.seed(seed_value)
        assert np.random.random() == val2

    def test_set_seed_from_env(self, monkeypatch):
        """Test setting seed from environment variable."""
        monkeypatch.setenv("RANDOM_SEED", "99999")
        result = set_random_seed()
        
        assert result == 99999

    def test_set_seed_default(self, monkeypatch):
        """Test default seed when no env var is set."""
        if "RANDOM_SEED" in os.environ:
            monkeypatch.delenv("RANDOM_SEED")
        
        result = set_random_seed()
        assert result == 42


class TestGetConfig:
    def test_get_config_structure(self):
        """Test that get_config returns expected structure."""
        config = get_config()
        
        assert "random_seed" in config
        assert "api_keys" in config
        assert "paths" in config
        assert "cpu_threads" in config
        assert "memory_limit_gb" in config
        
        # Check nested structure
        assert "nasa_exoplanet_archive" in config["api_keys"]
        assert "project_root" in config["paths"]

    def test_get_config_paths_exist(self):
        """Test that configured paths exist."""
        config = get_config()
        
        for key, path_str in config["paths"].items():
            assert Path(path_str).exists(), f"Path {path_str} does not exist"


class TestValidateConfig:
    def test_validate_valid_config(self):
        """Test validation of a valid configuration."""
        config = get_config()
        result = validate_config(config)
        assert result is True

    def test_validate_invalid_seed(self):
        """Test validation with invalid seed."""
        config = get_config()
        config["random_seed"] = "not_a_number"
        result = validate_config(config)
        assert result is False

    def test_validate_invalid_threads(self):
        """Test validation with invalid CPU threads."""
        config = get_config()
        config["cpu_threads"] = -1
        result = validate_config(config)
        assert result is False

    def test_validate_invalid_memory(self):
        """Test validation with invalid memory limit."""
        config = get_config()
        config["memory_limit_gb"] = 0
        result = validate_config(config)
        assert result is False