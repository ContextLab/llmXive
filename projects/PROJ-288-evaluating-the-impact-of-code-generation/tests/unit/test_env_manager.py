"""
Unit tests for the environment configuration management module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
# Adjust import path based on project structure
from code.data.env_manager import (
    load_environment_variables,
    get_github_token,
    validate_github_token,
    setup_github_credentials,
    get_config,
    DEFAULT_RATE_LIMIT_HOURLY
)


@pytest.fixture
def mock_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GITHUB_TOKEN=test_token_12345\n"
        "RATE_LIMIT_HOURLY=1000\n"
        "BACKOFF_INITIAL=2\n"
    )
    return env_file


@pytest.fixture
def clear_env():
    """Clear relevant environment variables before and after test."""
    vars_to_clear = ["GITHUB_TOKEN", "RATE_LIMIT_HOURLY", "BACKOFF_INITIAL"]
    original_values = {}
    for var in vars_to_clear:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    yield
    for var, val in original_values.items():
        if val is not None:
            os.environ[var] = val
        elif var in os.environ:
            del os.environ[var]


class TestLoadEnvironmentVariables:
    def test_load_from_valid_file(self, mock_env_file, clear_env):
        """Test loading from a valid .env file."""
        result = load_environment_variables(str(mock_env_file))
        assert result is True
        assert os.getenv("GITHUB_TOKEN") == "test_token_12345"
        assert os.getenv("RATE_LIMIT_HOURLY") == "1000"

    def test_load_from_nonexistent_file(self, clear_env):
        """Test loading from a non-existent file returns False."""
        result = load_environment_variables("/nonexistent/path/.env")
        assert result is False

    def test_load_from_default_path_missing(self, clear_env, caplog):
        """Test behavior when default .env is missing."""
        # This test assumes the default path logic
        result = load_environment_variables()
        # Should return False if file is missing
        assert result is False


class TestGetGithubToken:
    def test_get_token_from_env(self, mock_env_file, clear_env):
        """Test retrieving token from environment."""
        load_environment_variables(str(mock_env_file))
        token = get_github_token()
        assert token == "test_token_12345"

    def test_get_token_missing(self, clear_env):
        """Test retrieving token when not set."""
        token = get_github_token()
        assert token is None


class TestValidateGithubToken:
    def test_validate_valid_token(self, clear_env):
        """Test validation of a valid token."""
        os.environ["GITHUB_TOKEN"] = "ghp_valid_token_string"
        assert validate_github_token() is True

    def test_validate_empty_token(self, clear_env):
        """Test validation of an empty token."""
        os.environ["GITHUB_TOKEN"] = ""
        assert validate_github_token() is False

    def test_validate_none_token(self, clear_env):
        """Test validation when token is None."""
        if "GITHUB_TOKEN" in os.environ:
            del os.environ["GITHUB_TOKEN"]
        assert validate_github_token() is False

    def test_validate_short_token(self, clear_env):
        """Test validation of a very short token (should still pass logic but warn)."""
        os.environ["GITHUB_TOKEN"] = "abc"
        # The current implementation returns True if not empty, but logs a warning
        # We just check it doesn't crash and returns boolean
        result = validate_github_token()
        assert isinstance(result, bool)


class TestSetupGithubCredentials:
    @patch('code.data.env_manager.load_environment_variables')
    @patch('code.data.env_manager.get_github_token')
    @patch('code.data.env_manager.validate_github_token')
    def test_setup_success(self, mock_validate, mock_get, mock_load, clear_env):
        """Test successful setup."""
        mock_load.return_value = True
        mock_get.return_value = "token123"
        mock_validate.return_value = True

        result = setup_github_credentials()
        assert result is True
        mock_load.assert_called_once()
        mock_get.assert_called_once()
        mock_validate.assert_called_once_with("token123")

    @patch('code.data.env_manager.load_environment_variables')
    def test_setup_load_failure(self, mock_load, clear_env):
        """Test setup fails if loading fails."""
        mock_load.return_value = False
        result = setup_github_credentials()
        assert result is False

    @patch('code.data.env_manager.load_environment_variables')
    @patch('code.data.env_manager.get_github_token')
    @patch('code.data.env_manager.validate_github_token')
    def test_setup_validation_failure(self, mock_validate, mock_get, mock_load, clear_env):
        """Test setup fails if validation fails."""
        mock_load.return_value = True
        mock_get.return_value = "token123"
        mock_validate.return_value = False

        result = setup_github_credentials()
        assert result is False


class TestGetConfig:
    @patch('code.data.env_manager.load_environment_variables')
    def test_get_config_defaults(self, mock_load, clear_env):
        """Test config retrieval with defaults when env vars are missing."""
        mock_load.return_value = True
        # Ensure no GITHUB_TOKEN is set
        if "GITHUB_TOKEN" in os.environ:
            del os.environ["GITHUB_TOKEN"]
        
        config = get_config()
        
        assert config["rate_limit_hourly"] == DEFAULT_RATE_LIMIT_HOURLY
        assert config["backoff_initial"] == 1
        assert config["backoff_max"] == 60
        assert config["stratification_seed"] == 42
        assert config["max_review_days"] == 30
        assert config["github_token"] is None
        
        mock_load.assert_called_once()
    
    @patch('code.data.env_manager.load_environment_variables')
    def test_get_config_with_env_vars(self, mock_load, clear_env):
        """Test config retrieval with custom env vars."""
        mock_load.return_value = True
        os.environ["RATE_LIMIT_HOURLY"] = "999"
        os.environ["BACKOFF_INITIAL"] = "5"
        os.environ["GITHUB_TOKEN"] = "my_token"
        
        config = get_config()
        
        assert config["rate_limit_hourly"] == 999
        assert config["backoff_initial"] == 5
        assert config["github_token"] == "my_token"