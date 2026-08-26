"""
Tests for the credentials management module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from utils.credentials import (
    load_dotenv_file,
    get_token_from_env,
    get_token_from_keyring,
    set_token_to_keyring,
    get_uk_biobank_token,
    get_uk_biobank_api_key,
    validate_credentials,
    ConfigError,
    ENV_FILE_NAME,
    KEYRING_SERVICE_NAME,
    KEYRING_USERNAME,
    ENV_TOKEN_VAR
)

class TestLoadDotenv:
    def test_load_dotenv_file_success(self):
        """Test successful loading of a valid .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ENV_FILE_NAME
            env_path.write_text(f"{ENV_TOKEN_VAR}=test_token_123\n")
            
            # Mock the project root to point to our temp dir
            with patch('utils.credentials.Path.__truediv__', return_value=env_path):
                with patch('utils.credentials.Path.exists', return_value=True):
                    # We need to patch load_dotenv to avoid actual file system access
                    with patch('utils.credentials.load_dotenv', return_value=True) as mock_load:
                        result = load_dotenv_file(Path(tmpdir))
                        assert result is True
                        mock_load.assert_called_once()

    def test_load_dotenv_file_missing(self):
        """Test handling of missing .env file."""
        with patch('utils.credentials.Path.exists', return_value=False):
            result = load_dotenv_file()
            assert result is False

class TestTokenRetrieval:
    def test_get_token_from_env_found(self):
        """Test retrieving token from environment variable."""
        with patch.dict(os.environ, {ENV_TOKEN_VAR: "test_token"}):
            token = get_token_from_env()
            assert token == "test_token"

    def test_get_token_from_env_missing(self):
        """Test handling of missing environment variable."""
        if ENV_TOKEN_VAR in os.environ:
            del os.environ[ENV_TOKEN_VAR]
        token = get_token_from_env()
        assert token is None

    def test_get_token_from_keyring_found(self):
        """Test retrieving token from keyring."""
        with patch('utils.credentials.keyring.get_password', return_value="keyring_token"):
            token = get_token_from_keyring()
            assert token == "keyring_token"

    def test_get_token_from_keyring_missing(self):
        """Test handling of missing keyring entry."""
        with patch('utils.credentials.keyring.get_password', return_value=None):
            token = get_token_from_keyring()
            assert token is None

    def test_get_token_from_keyring_error(self):
        """Test handling of keyring errors."""
        with patch('utils.credentials.keyring.get_password', side_effect=Exception("Keyring error")):
            token = get_token_from_keyring()
            assert token is None

class TestTokenStorage:
    def test_set_token_to_keyring_success(self):
        """Test successful token storage."""
        with patch('utils.credentials.keyring.set_password', return_value=None):
            result = set_token_to_keyring("test_token")
            assert result is True

    def test_set_token_to_keyring_failure(self):
        """Test handling of storage failure."""
        with patch('utils.credentials.keyring.set_password', side_effect=Exception("Storage error")):
            result = set_token_to_keyring("test_token")
            assert result is False

class TestGetUkBiobankToken:
    def test_token_from_env(self):
        """Test token retrieval prioritizes environment variable."""
        with patch.dict(os.environ, {ENV_TOKEN_VAR: "env_token"}):
            with patch('utils.credentials.get_token_from_keyring', return_value="keyring_token"):
                token = get_uk_biobank_token()
                assert token == "env_token"

    def test_token_from_keyring(self):
        """Test token retrieval falls back to keyring."""
        # Ensure env var is not set
        if ENV_TOKEN_VAR in os.environ:
            del os.environ[ENV_TOKEN_VAR]
            
        with patch('utils.credentials.get_token_from_env', return_value=None):
            with patch('utils.credentials.get_token_from_keyring', return_value="keyring_token"):
                token = get_uk_biobank_token()
                assert token == "keyring_token"

    def test_token_not_found_raises_error(self):
        """Test that missing token raises ConfigError."""
        with patch('utils.credentials.get_token_from_env', return_value=None):
            with patch('utils.credentials.get_token_from_keyring', return_value=None):
                with pytest.raises(ConfigError, match="UK Biobank access token not found"):
                    get_uk_biobank_token()

class TestValidateCredentials:
    def test_validate_success(self):
        """Test successful credential validation."""
        with patch('utils.credentials.get_uk_biobank_token', return_value="valid_token"):
            result = validate_credentials()
            assert result is True

    def test_validate_empty_token(self):
        """Test validation fails with empty token."""
        with patch('utils.credentials.get_uk_biobank_token', return_value=""):
            with pytest.raises(ConfigError, match="token is empty or invalid"):
                validate_credentials()

    def test_validate_missing_token(self):
        """Test validation fails with missing token."""
        with patch('utils.credentials.get_uk_biobank_token', side_effect=ConfigError("Not found")):
            with pytest.raises(ConfigError):
                validate_credentials()

class TestGetApikey:
    def test_get_api_key_found(self):
        """Test retrieving API key from environment."""
        with patch.dict(os.environ, {"UKB_API_KEY": "api_key_123"}):
            key = get_uk_biobank_api_key()
            assert key == "api_key_123"

    def test_get_api_key_missing(self):
        """Test handling of missing API key."""
        if "UKB_API_KEY" in os.environ:
            del os.environ["UKB_API_KEY"]
        key = get_uk_biobank_api_key()
        assert key is None

class TestInitConfig:
    def test_init_config_success(self):
        """Test successful config initialization."""
        with patch('utils.credentials.validate_credentials', return_value=True):
            # Should not raise
            from utils.credentials import init_config
            init_config()

    def test_init_config_failure(self):
        """Test config initialization fails with missing credentials."""
        with patch('utils.credentials.validate_credentials', side_effect=ConfigError("Missing")):
            with pytest.raises(ConfigError):
                from utils.credentials import init_config
                init_config()