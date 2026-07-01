"""
Unit tests for environment variable management (T009).
"""

import os
import pytest
from unittest.mock import patch

# Import the module under test
# Adjust import path based on project structure (src/ vs code/src/)
# Assuming the task creates code/src/config/env.py
from src.config.env import (
    EnvConfig,
    EnvironmentError,
    get_config,
    get_openneuro_api_key,
    get_data_dir,
)


class TestEnvConfigValidation:
    """Tests for EnvConfig validation logic."""

    def test_valid_environment(self):
        """Test that valid environment variables are loaded correctly."""
        with patch.dict(
            os.environ,
            {
                "OPENNEURO_API_KEY": "valid_key_123",
                "DATA_DIR": "/path/to/data",
            },
            clear=True,
        ):
            config = EnvConfig()
            assert config.openneuro_api_key == "valid_key_123"
            assert config.data_dir == "/path/to/data"

    def test_missing_api_key(self):
        """Test that missing OPENNEURO_API_KEY raises EnvironmentError."""
        with patch.dict(
            os.environ,
            {"DATA_DIR": "/path/to/data"},
            clear=True,
        ):
            with pytest.raises(EnvironmentError) as exc_info:
                EnvConfig()
            assert "OPENNEURO_API_KEY" in str(exc_info.value)

    def test_missing_data_dir(self):
        """Test that missing DATA_DIR raises EnvironmentError."""
        with patch.dict(
            os.environ,
            {"OPENNEURO_API_KEY": "valid_key"},
            clear=True,
        ):
            with pytest.raises(EnvironmentError) as exc_info:
                EnvConfig()
            assert "DATA_DIR" in str(exc_info.value)

    def test_empty_api_key(self):
        """Test that empty OPENNEURO_API_KEY raises EnvironmentError."""
        with patch.dict(
            os.environ,
            {
                "OPENNEURO_API_KEY": "",
                "DATA_DIR": "/path/to/data",
            },
            clear=True,
        ):
            with pytest.raises(EnvironmentError) as exc_info:
                EnvConfig()
            assert "OPENNEURO_API_KEY" in str(exc_info.value)

    def test_empty_data_dir(self):
        """Test that empty DATA_DIR raises EnvironmentError."""
        with patch.dict(
            os.environ,
            {
                "OPENNEURO_API_KEY": "valid_key",
                "DATA_DIR": "   ",
            },
            clear=True,
        ):
            with pytest.raises(EnvironmentError) as exc_info:
                EnvConfig()
            assert "DATA_DIR" in str(exc_info.value)

    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from values."""
        with patch.dict(
            os.environ,
            {
                "OPENNEURO_API_KEY": "  key_with_spaces  ",
                "DATA_DIR": "  /path/to/data  ",
            },
            clear=True,
        ):
            config = EnvConfig()
            assert config.openneuro_api_key == "key_with_spaces"
            assert config.data_dir == "/path/to/data"

    def test_to_dict_masks_key(self):
        """Test that to_dict masks the API key."""
        with patch.dict(
            os.environ,
            {
                "OPENNEURO_API_KEY": "secret_key",
                "DATA_DIR": "/data",
            },
            clear=True,
        ):
            config = EnvConfig()
            result = config.to_dict()
            assert result["openneuro_api_key"] == "****"
            assert result["data_dir"] == "/data"


class TestGlobalAccessors:
    """Tests for global accessor functions."""

    def setup_method(self):
        # Reset singleton before each test
        from src.config import env
        env._config_instance = None

    def test_get_config_returns_instance(self):
        """Test that get_config returns an EnvConfig instance."""
        with patch.dict(
            os.environ,
            {
                "OPENNEURO_API_KEY": "test_key",
                "DATA_DIR": "/test/data",
            },
            clear=True,
        ):
            config = get_config()
            assert isinstance(config, EnvConfig)

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        with patch.dict(
            os.environ,
            {
                "OPENNEURO_API_KEY": "test_key",
                "DATA_DIR": "/test/data",
            },
            clear=True,
        ):
            config1 = get_config()
            config2 = get_config()
            assert config1 is config2

    def test_get_openneuro_api_key(self):
        """Test the convenience function for API key."""
        with patch.dict(
            os.environ,
            {
                "OPENNEURO_API_KEY": "my_api_key",
                "DATA_DIR": "/test/data",
            },
            clear=True,
        ):
            key = get_openneuro_api_key()
            assert key == "my_api_key"

    def test_get_data_dir(self):
        """Test the convenience function for data dir."""
        with patch.dict(
            os.environ,
            {
                "OPENNEURO_API_KEY": "my_api_key",
                "DATA_DIR": "/my/data/path",
            },
            clear=True,
        ):
            path = get_data_dir()
            assert path == "/my/data/path"

    def test_get_config_fails_without_env(self):
        """Test that get_config raises error if env vars are missing."""
        # Ensure vars are not set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError):
                get_config()
