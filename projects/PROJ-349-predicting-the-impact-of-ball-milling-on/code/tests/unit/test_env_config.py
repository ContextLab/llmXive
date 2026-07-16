"""
Unit tests for environment configuration management.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# We need to mock the actual loading to avoid side effects in tests
# and to test the logic without requiring a real .env file in the repo
from src.config.env_config import (
    load_environment,
    get_required_env_var,
    get_optional_env_var,
    ConfigError,
    ProjectConfig
)

class TestLoadEnvironment:
    def test_load_environment_file_exists(self, tmp_path):
        """Test loading a valid .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_KEY=test_value\n")
        
        with patch("src.config.env_config.load_dotenv", return_value=True) as mock_load:
            result = load_environment(str(env_file))
            mock_load.assert_called_once_with(str(env_file))
            assert result is True

    def test_load_environment_file_not_exists(self, tmp_path):
        """Test loading when .env file does not exist."""
        non_existent = tmp_path / "non_existent.env"
        
        # Should return False and not raise
        result = load_environment(str(non_existent))
        assert result is False

    def test_load_environment_dotenv_unavailable(self):
        """Test behavior when python-dotenv is not installed."""
        with patch("src.config.env_config.DOTENV_AVAILABLE", False):
            result = load_environment()
            assert result is False

class TestGetRequiredEnvVar:
    def test_get_required_var_success(self):
        """Test retrieving an existing required variable."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = get_required_env_var("TEST_VAR")
            assert result == "test_value"

    def test_get_required_var_missing(self):
        """Test that missing required variable raises ConfigError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError, match="Missing required environment variable"):
                get_required_env_var("NON_EXISTENT_VAR")

    def test_get_required_var_empty(self):
        """Test that empty required variable raises ConfigError."""
        with patch.dict(os.environ, {"EMPTY_VAR": ""}):
            with pytest.raises(ConfigError):
                get_required_env_var("EMPTY_VAR")

class TestGetOptionalEnvVar:
    def test_get_optional_var_exists(self):
        """Test retrieving an existing optional variable."""
        with patch.dict(os.environ, {"OPT_VAR": "opt_value"}):
            result = get_optional_env_var("OPT_VAR")
            assert result == "opt_value"

    def test_get_optional_var_missing_default(self):
        """Test retrieving missing optional variable with default."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_optional_env_var("MISSING_OPT", "default_val")
            assert result == "default_val"

    def test_get_optional_var_missing_no_default(self):
        """Test retrieving missing optional variable without default."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_optional_env_var("MISSING_OPT")
            assert result == ""

class TestProjectConfig:
    def test_config_initialization_missing_key(self):
        """Test that missing required key raises ConfigError during init."""
        # Ensure the required key is not set
        env_copy = os.environ.copy()
        env_copy.pop("MATERIALS_PROJECT_API_KEY", None)
        
        with patch.dict(os.environ, env_copy, clear=False):
            with patch("src.config.env_config.load_environment", return_value=False):
                with pytest.raises(ConfigError, match="Missing required environment variable: MATERIALS_PROJECT_API_KEY"):
                    ProjectConfig(load_env=False)

    def test_config_initialization_success(self, monkeypatch):
        """Test successful initialization with all required keys."""
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "fake_key_123")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("RANDOM_SEED", "12345")
        
        config = ProjectConfig(load_env=False)
        
        assert config.materials_project_api_key == "fake_key_123"
        assert config.random_seed == 12345
        # Check logging level was set (this is harder to assert directly, 
        # but we can check the basic attributes)
        assert hasattr(config, 'arxiv_user_agent')

    def test_config_optional_keys(self, monkeypatch):
        """Test that optional keys are handled correctly."""
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "key")
        monkeypatch.setenv("NIST_API_TOKEN", "nist_token")
        
        config = ProjectConfig(load_env=False)
        assert config.nist_api_token == "nist_token"
        
        # Test missing optional key
        monkeypatch.delenv("NIST_API_TOKEN", raising=False)
        config2 = ProjectConfig(load_env=False)
        assert config2.nist_api_token == ""

class TestGetConfigSingleton:
    def test_singleton_instance(self, monkeypatch):
        """Test that get_config returns the same instance."""
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "key")
        
        from src.config import env_config
        # Reset singleton for test
        env_config._config_instance = None
        
        config1 = env_config.get_config()
        config2 = env_config.get_config()
        
        assert config1 is config2
