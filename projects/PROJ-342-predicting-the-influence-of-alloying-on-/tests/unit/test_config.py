"""
Unit tests for the configuration management module.

Verifies that:
- Config loads from .env and config.yaml correctly.
- Default values are used when files are missing.
- DOI retrieval works as expected.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config.config import Config, ConfigError, get_config


class TestConfigClass:
    """Tests for the Config class."""

    def test_init_defaults(self, tmp_path):
        """Test that Config initializes with correct default paths."""
        # Create a temporary directory to act as project root
        # We mock the paths to point to our temp dir
        env_path = tmp_path / ".env"
        yaml_path = tmp_path / "config.yaml"
        
        config = Config(env_path=env_path, yaml_path=yaml_path)
        
        assert config.env_path == env_path
        assert config.yaml_path == yaml_path
        assert not config._loaded

    def test_load_missing_files(self, tmp_path):
        """Test loading when config files do not exist."""
        env_path = tmp_path / ".env"
        yaml_path = tmp_path / "config.yaml"
        
        config = Config(env_path=env_path, yaml_path=yaml_path)
        
        # Should not raise, just log warnings
        config.load()
        
        assert config._loaded
        # Should return defaults
        dois = config.get_zenodo_dois()
        assert dois["primary"] == "10.5281/zenodo.10043838"
        assert dois["fallback"] == "10.5281/zenodo.11023456"
        
        assert config.get_seed() == 42

    def test_load_with_env_file(self, tmp_path):
        """Test loading environment variables from a .env file."""
        env_path = tmp_path / ".env"
        env_path.write_text("TEST_VAR=value123\nTEST_VAR_2=456")
        
        yaml_path = tmp_path / "config.yaml"
        
        config = Config(env_path=env_path, yaml_path=yaml_path)
        config.load()
        
        assert os.getenv("TEST_VAR") == "value123"
        assert os.getenv("TEST_VAR_2") == "456"

    def test_load_with_yaml_file(self, tmp_path):
        """Test loading configuration from a yaml file."""
        env_path = tmp_path / ".env"
        yaml_path = tmp_path / "config.yaml"
        
        yaml_content = """
        random_seed: 12345
        resource_limits:
          max_time_hours: 10
          max_memory_gb: 16
        """
        yaml_path.write_text(yaml_content)
        
        config = Config(env_path=env_path, yaml_path=yaml_path)
        config.load()
        
        assert config.get_seed() == 12345
        assert config.get_limits()["max_time_hours"] == 10
        assert config.get_limits()["max_memory_gb"] == 16

    def test_doi_override_via_env(self, tmp_path):
        """Test that DOIs can be overridden via .env."""
        env_path = tmp_path / ".env"
        env_path.write_text("ZENODO_PRIMARY_DOI=10.0000/override\n")
        
        yaml_path = tmp_path / "config.yaml"
        
        config = Config(env_path=env_path, yaml_path=yaml_path)
        config.load()
        
        dois = config.get_zenodo_dois()
        assert dois["primary"] == "10.0000/override"
        assert dois["fallback"] == "10.5281/zenodo.11023456" # Fallback should be default


def test_get_config_singleton():
    """Test that get_config returns a Config instance."""
    config = get_config()
    assert isinstance(config, Config)
