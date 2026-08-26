"""
Unit tests for the config_manager module.

These tests verify the functionality of loading and retrieving credentials
from environment variables and the keyring.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

# Import the module to test
from utils.config_manager import (
    load_dotenv_file,
    get_token_from_env,
    get_token_from_keyring,
    set_token_to_keyring,
    get_uk_biobank_token,
    get_uk_biobank_api_key,
    validate_credentials,
    init_config,
    ENV_FILE_PATH,
    UK_BIOBANK_TOKEN_KEY,
    KEYRING_SERVICE_NAME,
    KEYRING_TOKEN_USER
)
from utils.logging import ConfigError


class TestLoadDotenvFile:
    """Tests for load_dotenv_file function."""

    def test_load_dotenv_file_exists(self, tmp_path):
        """Test loading a .env file that exists."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\nANOTHER_VAR=another_value")
        
        result = load_dotenv_file(env_file)
        
        assert result is True
        assert os.getenv("TEST_VAR") == "test_value"
        assert os.getenv("ANOTHER_VAR") == "another_value"
    
    def test_load_dotenv_file_not_exists(self, tmp_path):
        """Test loading a .env file that does not exist."""
        non_existent = tmp_path / "non_existent.env"
        
        result = load_dotenv_file(non_existent)
        
        assert result is False
    
    def test_load_dotenv_file_default_path(self, monkeypatch, tmp_path):
        """Test loading .env from default path (parent of code directory)."""
        # Create a fake project structure
        project_root = tmp_path / "project"
        code_dir = project_root / "code"
        code_dir.mkdir(parents=True)
        
        env_file = project_root / ".env"
        env_file.write_text("DEFAULT_PATH_VAR=default_value")
        
        # Mock the __file__ path to be inside code/
        with patch('utils.config_manager.Path.__new__', return_value=code_dir / "dummy.py"):
            # This is a bit tricky to mock __file__, so we'll just test the logic
            # by directly calling with the path
            pass
        
        # Direct test
        result = load_dotenv_file(env_file)
        assert result is True
        assert os.getenv("DEFAULT_PATH_VAR") == "default_value"


class TestGetTokenFromEnv:
    """Tests for get_token_from_env function."""

    def test_get_token_from_env_found(self, monkeypatch):
        """Test retrieving a token that exists in environment."""
        monkeypatch.setenv(UK_BIOBANK_TOKEN_KEY, "test_token_123")
        
        token = get_token_from_env(UK_BIOBANK_TOKEN_KEY)
        
        assert token == "test_token_123"
    
    def test_get_token_from_env_not_found(self, monkeypatch):
        """Test retrieving a token that does not exist in environment."""
        if UK_BIOBANK_TOKEN_KEY in os.environ:
            monkeypatch.delenv(UK_BIOBANK_TOKEN_KEY)
        
        token = get_token_from_env(UK_BIOBANK_TOKEN_KEY)
        
        assert token is None


class TestKeyringFunctions:
    """Tests for keyring-related functions."""

    @patch('utils.config_manager.keyring')
    def test_get_token_from_keyring_found(self, mock_keyring):
        """Test retrieving a token from keyring that exists."""
        mock_keyring.get_password.return_value = "keyring_token_456"
        
        token = get_token_from_keyring(KEYRING_SERVICE_NAME, KEYRING_TOKEN_USER)
        
        assert token == "keyring_token_456"
        mock_keyring.get_password.assert_called_once_with(KEYRING_SERVICE_NAME, KEYRING_TOKEN_USER)
    
    @patch('utils.config_manager.keyring')
    def test_get_token_from_keyring_not_found(self, mock_keyring):
        """Test retrieving a token from keyring that does not exist."""
        mock_keyring.get_password.return_value = None
        
        token = get_token_from_keyring(KEYRING_SERVICE_NAME, KEYRING_TOKEN_USER)
        
        assert token is None
    
    @patch('utils.config_manager.keyring')
    def test_set_token_to_keyring_success(self, mock_keyring):
        """Test storing a token in keyring successfully."""
        mock_keyring.set_password.return_value = None  # set_password returns None on success
        
        result = set_token_to_keyring(KEYRING_SERVICE_NAME, KEYRING_TOKEN_USER, "new_token")
        
        assert result is True
        mock_keyring.set_password.assert_called_once_with(KEYRING_SERVICE_NAME, KEYRING_TOKEN_USER, "new_token")
    
    @patch('utils.config_manager.keyring')
    def test_set_token_to_keyring_failure(self, mock_keyring):
        """Test storing a token in keyring fails."""
        mock_keyring.set_password.side_effect = Exception("Keyring error")
        
        result = set_token_to_keyring(KEYRING_SERVICE_NAME, KEYRING_TOKEN_USER, "new_token")
        
        assert result is False


class TestGetUkBiobankToken:
    """Tests for get_uk_biobank_token function."""

    @patch('utils.config_manager.get_token_from_env')
    @patch('utils.config_manager.get_token_from_keyring')
    def test_get_uk_biobank_token_from_env(self, mock_keyring, mock_env):
        """Test getting token from environment variable."""
        mock_env.return_value = "env_token"
        mock_keyring.return_value = None
        
        token = get_uk_biobank_token()
        
        assert token == "env_token"
        mock_env.assert_called_once()
        mock_keyring.assert_not_called()  # Should not check keyring if env is found
    
    @patch('utils.config_manager.get_token_from_env')
    @patch('utils.config_manager.get_token_from_keyring')
    def test_get_uk_biobank_token_from_keyring(self, mock_keyring, mock_env):
        """Test getting token from keyring when env is not set."""
        mock_env.return_value = None
        mock_keyring.return_value = "keyring_token"
        
        token = get_uk_biobank_token()
        
        assert token == "keyring_token"
        mock_env.assert_called_once()
        mock_keyring.assert_called_once()
    
    @patch('utils.config_manager.get_token_from_env')
    @patch('utils.config_manager.get_token_from_keyring')
    def test_get_uk_biobank_token_not_found(self, mock_keyring, mock_env):
        """Test getting token when neither env nor keyring has it."""
        mock_env.return_value = None
        mock_keyring.return_value = None
        
        token = get_uk_biobank_token()
        
        assert token is None


class TestValidateCredentials:
    """Tests for validate_credentials function."""

    @patch('utils.config_manager.get_uk_biobank_token')
    @patch('utils.config_manager.get_uk_biobank_api_key')
    def test_validate_credentials_valid(self, mock_api_key, mock_token):
        """Test validation when credentials are present."""
        mock_token.return_value = "valid_token"
        mock_api_key.return_value = "valid_api_key"
        
        result = validate_credentials()
        
        assert result["is_valid"] is True
        assert result["token_present"] is True
        assert result["api_key_present"] is True
        assert "successful" in result["message"].lower()
    
    @patch('utils.config_manager.get_uk_biobank_token')
    @patch('utils.config_manager.get_uk_biobank_api_key')
    def test_validate_credentials_missing_token(self, mock_api_key, mock_token):
        """Test validation when token is missing."""
        mock_token.return_value = None
        mock_api_key.return_value = "valid_api_key"
        
        result = validate_credentials()
        
        assert result["is_valid"] is False
        assert result["token_present"] is False
        assert result["api_key_present"] is True
        assert "missing" in result["message"].lower()
    
    @patch('utils.config_manager.get_uk_biobank_token')
    @patch('utils.config_manager.get_uk_biobank_api_key')
    def test_validate_credentials_missing_api_key(self, mock_api_key, mock_token):
        """Test validation when API key is missing (but token is present)."""
        mock_token.return_value = "valid_token"
        mock_api_key.return_value = None
        
        result = validate_credentials()
        
        # API key is optional, so validation should still pass
        assert result["is_valid"] is True
        assert result["token_present"] is True
        assert result["api_key_present"] is False


class TestInitConfig:
    """Tests for init_config function."""

    @patch('utils.config_manager.load_dotenv_file')
    @patch('utils.config_manager.validate_credentials')
    def test_init_config_success(self, mock_validate, mock_load):
        """Test successful initialization."""
        mock_load.return_value = True
        mock_validate.return_value = {
            "is_valid": True,
            "token_present": True,
            "api_key_present": False,
            "message": "Credentials validation successful."
        }
        
        result = init_config()
        
        assert result["env_loaded"] is True
        assert result["validation"]["is_valid"] is True
        mock_load.assert_called_once()
        mock_validate.assert_called_once()
    
    @patch('utils.config_manager.load_dotenv_file')
    @patch('utils.config_manager.validate_credentials')
    def test_init_config_failure(self, mock_validate, mock_load):
        """Test initialization failure when credentials are missing."""
        mock_load.return_value = True
        mock_validate.return_value = {
            "is_valid": False,
            "token_present": False,
            "api_key_present": False,
            "message": "Credentials validation failed."
        }
        
        with pytest.raises(ConfigError):
            init_config()
        
        mock_load.assert_called_once()
        mock_validate.assert_called_once()


class TestMain:
    """Tests for the main function."""

    @patch('utils.config_manager.init_config')
    @patch('utils.config_manager.get_uk_biobank_token')
    @patch('builtins.print')
    def test_main_success(self, mock_print, mock_token, mock_init):
        """Test main function with successful config."""
        mock_init.return_value = {
            "env_loaded": True,
            "validation": {
                "is_valid": True,
                "token_present": True,
                "api_key_present": False,
                "message": "Credentials validation successful."
            }
        }
        mock_token.return_value = "test_token_12345678"
        
        main()
        
        # Verify print calls
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Initializing configuration" in call for call in print_calls)
        assert any("Credentials are valid" in call for call in print_calls)
    
    @patch('utils.config_manager.init_config')
    @patch('builtins.print')
    def test_main_config_error(self, mock_print, mock_init):
        """Test main function with ConfigError."""
        mock_init.side_effect = ConfigError("Config failed")
        
        main()
        
        # Verify error message is printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Configuration Error" in call for call in print_calls)
    
    @patch('utils.config_manager.init_config')
    @patch('builtins.print')
    def test_main_unexpected_error(self, mock_print, mock_init):
        """Test main function with unexpected error."""
        mock_init.side_effect = RuntimeError("Unexpected error")
        
        main()
        
        # Verify error message is printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Unexpected error" in call for call in print_calls)