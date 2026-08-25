"""
Tests for the environment configuration manager.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
# Note: Using relative import structure compatible with the project layout
from code.utils.config_manager import (
    load_dotenv_file,
    get_token_from_env,
    get_token_from_keyring,
    set_token_to_keyring,
    get_uk_biobank_token,
    get_uk_biobank_api_key,
    validate_credentials,
    init_config,
    ConfigError
)

class TestConfigManager:
    """Test suite for config_manager utilities."""

    @patch('code.utils.config_manager.load_dotenv')
    @patch('code.utils.config_manager.Path.exists', return_value=True)
    def test_load_dotenv_file_success(self, mock_exists, mock_load_dotenv, tmp_path):
        """Test successful loading of a .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=value\n")
        
        result = load_dotenv_file(env_file)
        
        assert result is True
        mock_load_dotenv.assert_called_once_with(dotenv_path=env_file, override=True)

    @patch('code.utils.config_manager.Path.exists', return_value=False)
    def test_load_dotenv_file_not_found(self, mock_exists, tmp_path):
        """Test loading when .env file does not exist."""
        result = load_dotenv_file(tmp_path / "nonexistent.env")
        
        assert result is False

    def test_get_token_from_env_found(self, monkeypatch):
        """Test retrieving token from environment variable."""
        monkeypatch.setenv("TEST_TOKEN", "secret_123")
        
        token = get_token_from_env("TEST_TOKEN")
        
        assert token == "secret_123"

    def test_get_token_from_env_missing(self, monkeypatch):
        """Test retrieving token when env var is missing."""
        if "TEST_MISSING_TOKEN" in monkeypatch:
            monkeypatch.delenv("TEST_MISSING_TOKEN", raising=False)
        
        token = get_token_from_env("TEST_MISSING_TOKEN")
        
        assert token is None

    @patch('code.utils.config_manager.keyring.get_password')
    def test_get_token_from_keyring_found(self, mock_get_password):
        """Test retrieving token from keyring."""
        mock_get_password.return_value = "keyring_secret"
        
        token = get_token_from_keyring("test_service", "test_user")
        
        assert token == "keyring_secret"
        mock_get_password.assert_called_once_with("test_service", "test_user")

    @patch('code.utils.config_manager.keyring.get_password')
    def test_get_token_from_keyring_missing(self, mock_get_password):
        """Test retrieving token when keyring returns None."""
        mock_get_password.return_value = None
        
        token = get_token_from_keyring("test_service", "test_user")
        
        assert token is None

    @patch('code.utils.config_manager.keyring.set_password')
    def test_set_token_to_keyring_success(self, mock_set_password):
        """Test setting token in keyring."""
        set_token_to_keyring("my_secret", "test_service", "test_user")
        
        mock_set_password.assert_called_once_with("test_service", "test_user", "my_secret")

    @patch('code.utils.config_manager.keyring.set_password', side_effect=Exception("Keyring error"))
    def test_set_token_to_keyring_failure(self, mock_set_password):
        """Test failure when setting token in keyring."""
        with pytest.raises(ConfigError):
            set_token_to_keyring("my_secret", "test_service", "test_user")

    @patch('code.utils.config_manager.get_token_from_env', return_value="env_token")
    @patch('code.utils.config_manager.get_token_from_keyring', return_value="keyring_token")
    def test_get_uk_biobank_token_priority_env(self, mock_keyring, mock_env):
        """Test that environment variable takes priority over keyring."""
        token = get_uk_biobank_token()
        
        assert token == "env_token"
        mock_env.assert_called_once_with("UK_BIOBANK_TOKEN")
        # Keyring should not be called if env is found
        assert not mock_keyring.called

    @patch('code.utils.config_manager.get_token_from_env', return_value=None)
    @patch('code.utils.config_manager.get_token_from_keyring', return_value="keyring_token")
    def test_get_uk_biobank_token_fallback_keyring(self, mock_keyring, mock_env):
        """Test fallback to keyring when env is missing."""
        token = get_uk_biobank_token()
        
        assert token == "keyring_token"
        mock_env.assert_called_once_with("UK_BIOBANK_TOKEN")
        mock_keyring.assert_called_once()

    @patch('code.utils.config_manager.get_token_from_env', return_value=None)
    @patch('code.utils.config_manager.get_token_from_keyring', return_value=None)
    def test_get_uk_biobank_token_raises_error(self, mock_keyring, mock_env):
        """Test that ConfigError is raised when no token is found."""
        with pytest.raises(ConfigError):
            get_uk_biobank_token()

    @patch('code.utils.config_manager.get_uk_biobank_token', return_value="valid_token")
    @patch('code.utils.config_manager.get_uk_biobank_api_key', return_value="valid_key")
    def test_validate_credentials_success(self, mock_api_key, mock_token):
        """Test successful validation of all credentials."""
        result = validate_credentials()
        
        assert result["uk_biobank_token"] is True
        assert result["uk_biobank_api_key"] is True

    @patch('code.utils.config_manager.get_uk_biobank_token', side_effect=ConfigError("Missing"))
    @patch('code.utils.config_manager.get_uk_biobank_api_key', return_value="valid_key")
    def test_validate_credentials_partial_failure(self, mock_api_key, mock_token):
        """Test validation when some credentials are missing."""
        result = validate_credentials()
        
        assert result["uk_biobank_token"] is False
        assert result["uk_biobank_api_key"] is True