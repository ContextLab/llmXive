import os
import pytest
from unittest.mock import patch
from src.config.env import (
    EnvironmentError,
    EnvConfig,
    get_config,
    get_openneuro_api_key,
    get_data_dir
)


class TestEnvConfigValidation:
    """Tests for environment variable validation logic."""

    def test_missing_required_key_raises_error(self):
        """Test that missing OPENNEURO_API_KEY raises EnvironmentError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError) as exc_info:
                get_openneuro_api_key()
            
            assert "OPENNEURO_API_KEY" in str(exc_info.value)
            assert "not set or is empty" in str(exc_info.value)

    def test_empty_required_key_raises_error(self):
        """Test that empty OPENNEURO_API_KEY raises EnvironmentError."""
        with patch.dict(os.environ, {"OPENNEURO_API_KEY": ""}):
            with pytest.raises(EnvironmentError) as exc_info:
                get_openneuro_api_key()
            
            assert "OPENNEURO_API_KEY" in str(exc_info.value)

    def test_whitespace_only_key_raises_error(self):
        """Test that whitespace-only OPENNEURO_API_KEY raises EnvironmentError."""
        with patch.dict(os.environ, {"OPENNEURO_API_KEY": "   "}):
            with pytest.raises(EnvironmentError) as exc_info:
                get_openneuro_api_key()
            
            assert "OPENNEURO_API_KEY" in str(exc_info.value)

    def test_missing_data_dir_raises_error(self):
        """Test that missing DATA_DIR raises EnvironmentError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError) as exc_info:
                get_data_dir()
            
            assert "DATA_DIR" in str(exc_info.value)

    def test_valid_api_key_returns_stripped_value(self):
        """Test that valid API key is returned with whitespace stripped."""
        test_key = "  sk-test-12345  "
        with patch.dict(os.environ, {"OPENNEURO_API_KEY": test_key}):
            result = get_openneuro_api_key()
            assert result == "sk-test-12345"

    def test_valid_data_dir_returns_stripped_value(self):
        """Test that valid data dir is returned with whitespace stripped."""
        test_dir = "  /path/to/data  "
        with patch.dict(os.environ, {"DATA_DIR": test_dir}):
            result = get_data_dir()
            assert result == "/path/to/data"

    def test_get_config_returns_envconfig_object(self):
        """Test that get_config returns a properly populated EnvConfig."""
        with patch.dict(os.environ, {
            "OPENNEURO_API_KEY": "test-key",
            "DATA_DIR": "/test/data"
        }):
            config = get_config()
            assert isinstance(config, EnvConfig)
            assert config.openneuro_api_key == "test-key"
            assert config.data_dir == "/test/data"

    def test_get_config_validates_both_variables(self):
        """Test that get_config fails if either variable is missing."""
        # Missing API key
        with patch.dict(os.environ, {"DATA_DIR": "/test/data"}):
            with pytest.raises(EnvironmentError):
                get_config()

        # Missing DATA_DIR
        with patch.dict(os.environ, {"OPENNEURO_API_KEY": "test-key"}):
            with pytest.raises(EnvironmentError):
                get_config()


class TestGlobalAccessors:
    """Tests for the global accessor functions."""

    def test_get_openneuro_api_key_integration(self):
        """Integration test for get_openneuro_api_key with valid env."""
        test_key = "integration-test-key-999"
        with patch.dict(os.environ, {"OPENNEURO_API_KEY": test_key}):
            assert get_openneuro_api_key() == test_key

    def test_get_data_dir_integration(self):
        """Integration test for get_data_dir with valid env."""
        test_dir = "/integration/test/dir"
        with patch.dict(os.environ, {"DATA_DIR": test_dir}):
            assert get_data_dir() == test_dir

    def test_env_error_inheritance(self):
        """Test that EnvironmentError is a proper Exception subclass."""
        assert issubclass(EnvironmentError, Exception)
        
        try:
            raise EnvironmentError("Test error message")
        except Exception as e:
            assert str(e) == "Test error message"