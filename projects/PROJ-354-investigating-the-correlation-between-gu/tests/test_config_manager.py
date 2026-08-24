"""
Tests for environment configuration management.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from utils.config_manager import (
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
from utils.logging import get_logger

logger = get_logger(__name__)


class TestConfigManager:
    """Test cases for configuration management functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()
        self.test_env = {}

    def teardown_method(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_load_dotenv_file_with_existing_file(self, tmp_path):
        """Test loading from an existing .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\nANOTHER_VAR=another_value")
        
        with patch.dict(os.environ, {}, clear=True):
            result = load_dotenv_file(env_file)
            assert result is True
            assert os.getenv("TEST_VAR") == "test_value"
            assert os.getenv("ANOTHER_VAR") == "another_value"

    def test_load_dotenv_file_with_missing_file(self):
        """Test loading from a non-existent .env file."""
        with patch.dict(os.environ, {}, clear=True):
            result = load_dotenv_file(Path("/nonexistent/.env"))
            assert result is False

    def test_get_token_from_env(self):
        """Test retrieving token from environment variable."""
        os.environ["TEST_TOKEN"] = "test_token_value"
        
        token = get_token_from_env("TEST_TOKEN")
        assert token == "test_token_value"

    def test_get_token_from_env_missing(self):
        """Test retrieving non-existent token from environment variable."""
        token = get_token_from_env("NONEXISTENT_TOKEN")
        assert token is None

    @patch('utils.config_manager.keyring')
    def test_get_token_from_keyring(self, mock_keyring):
        """Test retrieving token from keyring."""
        mock_keyring.get_password.return_value = "keyring_token_value"
        
        token = get_token_from_keyring()
        assert token == "keyring_token_value"

    @patch('utils.config_manager.keyring')
    def test_get_token_from_keyring_not_found(self, mock_keyring):
        """Test keyring retrieval when token is not found."""
        mock_keyring.get_password.return_value = None
        
        token = get_token_from_keyring()
        assert token is None

    @patch('utils.config_manager.keyring')
    def test_set_token_to_keyring(self, mock_keyring):
        """Test storing token in keyring."""
        mock_keyring.set_password.return_value = None
        
        result = set_token_to_keyring("test_token")
        assert result is True
        mock_keyring.set_password.assert_called_once()

    @patch('utils.config_manager.keyring')
    def test_set_token_to_keyring_failure(self, mock_keyring):
        """Test storing token in keyring when it fails."""
        mock_keyring.set_password.side_effect = Exception("Keyring error")
        
        result = set_token_to_keyring("test_token")
        assert result is False

    def test_get_uk_biobank_token_from_env(self):
        """Test getting UK Biobank token from environment variable."""
        os.environ["UK_BIOBANK_TOKEN"] = "uk_token_value"
        
        token = get_uk_biobank_token()
        assert token == "uk_token_value"

    @patch('utils.config_manager.load_dotenv_file')
    @patch('utils.config_manager.get_token_from_env')
    @patch('utils.config_manager.get_token_from_keyring')
    def test_get_uk_biobank_token_from_keyring(
        self, mock_keyring, mock_env, mock_load
    ):
        """Test getting UK Biobank token from keyring when not in env."""
        mock_load.return_value = None
        mock_env.return_value = None
        mock_keyring.return_value = "keyring_uk_token"
        
        token = get_uk_biobank_token()
        assert token == "keyring_uk_token"

    @patch('utils.config_manager.load_dotenv_file')
    @patch('utils.config_manager.get_token_from_env')
    @patch('utils.config_manager.get_token_from_keyring')
    def test_get_uk_biobank_token_missing(
        self, mock_keyring, mock_env, mock_load
    ):
        """Test getting UK Biobank token when not found anywhere."""
        mock_load.return_value = None
        mock_env.return_value = None
        mock_keyring.return_value = None
        
        with pytest.raises(ConfigError):
            get_uk_biobank_token()

    @patch('utils.config_manager.load_dotenv_file')
    @patch('utils.config_manager.get_token_from_env')
    def test_get_uk_biobank_api_key(self, mock_env, mock_load):
        """Test getting UK Biobank API key."""
        mock_load.return_value = None
        mock_env.return_value = "api_key_value"
        
        # Need to patch the function in the module where it's used
        with patch('utils.config_manager.get_token_from_env', return_value="api_key_value"):
            api_key = get_uk_biobank_api_key()
            assert api_key == "api_key_value"

    @patch('utils.config_manager.validate_credentials')
    def test_init_config(self, mock_validate):
        """Test configuration initialization."""
        mock_validate.return_value = {"uk_biobank_token": True}
        
        result = init_config()
        assert result == {"uk_biobank_token": True}

    def test_validate_credentials(self):
        """Test credential validation."""
        # Set up a token
        os.environ["UK_BIOBANK_TOKEN"] = "test_token"
        
        results = validate_credentials()
        assert "uk_biobank_token" in results
        assert results["uk_biobank_token"] is True
        assert "uk_biobank_api_key" in results
        # API key is optional, so it might be False if not set
        assert isinstance(results["uk_biobank_api_key"], bool)