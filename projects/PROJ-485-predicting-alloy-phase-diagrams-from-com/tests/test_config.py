"""
Tests for environment configuration management (T009).
Verifies Constitution Principle II: Data source URLs are centrally managed.
"""
import os
import sys
import tempfile
import pytest
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.config import (
    ConfigManager,
    get_config,
    reset_config,
    validate_data_sources,
    DEFAULT_CONFIG
)
from utils.error_codes import ErrorCode

class TestConfigManager:
    """Test suite for ConfigManager class."""

    def test_default_initialization(self):
        """Test initialization with default values."""
        config = ConfigManager()
        assert config.get("NIST_JANAF_URL") == DEFAULT_CONFIG["NIST_JANAF_URL"]
        assert config.get("SGTE_URL") == DEFAULT_CONFIG["SGTE_URL"]
        assert config.get("LOG_LEVEL") == "INFO"

    def test_env_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {"NIST_JANAF_URL": "https://custom-nist-url.com"}):
            reset_config()
            config = ConfigManager()
            assert config.get("NIST_JANAF_URL") == "https://custom-nist-url.com"

    def test_yaml_file_loading(self):
        """Test loading configuration from YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("NIST_JANAF_URL: https://yaml-config-url.com\n")
            f.write("MAX_RETRIES: 5\n")
            config_path = f.name

        try:
            reset_config()
            config = ConfigManager(config_path)
            assert config.get("NIST_JANAF_URL") == "https://yaml-config-url.com"
            assert config.get("MAX_RETRIES") == 5
        finally:
            os.unlink(config_path)

    def test_get_required_missing_key(self):
        """Test that get_required raises ValueError for missing keys."""
        config = ConfigManager()
        with pytest.raises(ValueError, match="Required configuration key missing"):
            config.get_required("NON_EXISTENT_KEY")

    def test_source_urls(self):
        """Test getting source URLs dictionary."""
        config = ConfigManager()
        urls = config.get_source_urls()
        assert "NIST_JANAF" in urls
        assert "SGTE" in urls
        assert urls["NIST_JANAF"] == DEFAULT_CONFIG["NIST_JANAF_URL"]

    def test_is_source_available(self):
        """Test source availability check."""
        config = ConfigManager()
        assert config.is_source_available("NIST_JANAF")
        assert config.is_source_available("SGTE")
        
        # Test with empty URL
        config._config["CUSTOM_URL"] = ""
        assert not config.is_source_available("CUSTOM")

    def test_path_creation(self):
        """Test that non-existent paths are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_path = os.path.join(tmpdir, "new", "sub", "path")
            assert not os.path.exists(new_path)
            
            config = ConfigManager()
            config._config["TEST_PATH"] = new_path
            config._validate()
            
            assert os.path.exists(new_path)

class TestGlobalConfig:
    """Test suite for global config functions."""

    def test_singleton_pattern(self):
        """Test that get_config returns the same instance."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self):
        """Test resetting the global config instance."""
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2

    def test_validate_data_sources(self):
        """Test data source validation."""
        reset_config()
        # With default config, sources should be configured
        assert validate_data_sources() is True

        # Test with missing sources
        reset_config()
        with patch.dict(os.environ, {"NIST_JANAF_URL": "", "SGTE_URL": ""}):
            reset_config()
            # This should return False as sources are empty
            result = validate_data_sources()
            assert result is False

class TestConfigIntegration:
    """Integration tests for configuration management."""

    def test_config_persistence_across_calls(self):
        """Test that config persists across multiple get_config calls."""
        reset_config()
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            config1 = get_config()
            assert config1.get("LOG_LEVEL") == "DEBUG"
            
            config2 = get_config()
            assert config2.get("LOG_LEVEL") == "DEBUG"

    def test_config_with_all_env_vars(self):
        """Test configuration with all environment variables set."""
        env_vars = {
            "NIST_JANAF_URL": "https://env-nist.com",
            "SGTE_URL": "https://env-sgte.com",
            "LOCAL_DATA_PATH": "/tmp/env-data",
            "LOG_LEVEL": "WARNING",
            "MAX_RETRIES": "10",
            "BACKOFF_FACTOR": "3.5",
            "TIMEOUT_SECONDS": "60"
        }
        
        with patch.dict(os.environ, env_vars):
            reset_config()
            config = get_config()
            
            assert config.get("NIST_JANAF_URL") == "https://env-nist.com"
            assert config.get("SGTE_URL") == "https://env-sgte.com"
            assert config.get("LOG_LEVEL") == "WARNING"
            assert config.get("MAX_RETRIES") == 10
            assert config.get("BACKOFF_FACTOR") == 3.5
            assert config.get("TIMEOUT_SECONDS") == 60
