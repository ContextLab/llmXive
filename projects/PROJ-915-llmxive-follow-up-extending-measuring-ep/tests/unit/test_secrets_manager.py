"""
Unit tests for secrets management functionality.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

# Import the module under test
from code.secrets_manager import (
    load_env_file,
    get_secret,
    validate_secrets,
    get_hf_token,
    get_prolific_api_key,
    SecretsManager,
    init_secrets,
    REQUIRED_SECRETS
)


class TestLoadEnvFile:
    """Tests for load_env_file function."""
    
    def test_load_env_file_exists(self, tmp_path):
        """Test loading from existing .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\nANOTHER_VAR=another_value")
        
        with patch('code.secrets_manager.load_dotenv') as mock_load_dotenv:
            result = load_env_file(str(env_file))
            
            assert result is True
            mock_load_dotenv.assert_called_once_with(str(env_file))
    
    def test_load_env_file_not_found(self, tmp_path):
        """Test behavior when .env file doesn't exist."""
        env_file = tmp_path / ".env"
        
        with patch('code.secrets_manager.load_dotenv') as mock_load_dotenv:
            result = load_env_file(str(env_file))
            
            assert result is False
            mock_load_dotenv.assert_not_called()


class TestGetSecret:
    """Tests for get_secret function."""
    
    def test_get_existing_secret(self):
        """Test retrieving an existing environment variable."""
        with patch.dict(os.environ, {"TEST_KEY": "test_value"}):
            result = get_secret("TEST_KEY", required=False)
            assert result == "test_value"
    
    def test_get_missing_required_secret(self):
        """Test that missing required secret raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required secret"):
                get_secret("NON_EXISTENT_KEY", required=True)
    
    def test_get_missing_optional_secret(self):
        """Test that missing optional secret returns None."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_secret("NON_EXISTENT_KEY", required=False)
            assert result is None
    
    def test_get_hf_token(self):
        """Test HuggingFace token retrieval."""
        with patch.dict(os.environ, {"HF_TOKEN": "hf_test_token"}):
            result = get_hf_token()
            assert result == "hf_test_token"
    
    def test_get_prolific_api_key_missing(self):
        """Test Prolific API key retrieval when not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_prolific_api_key()
            assert result is None


class TestValidateSecrets:
    """Tests for validate_secrets function."""
    
    def test_validate_all_present(self):
        """Test validation when all required secrets are present."""
        with patch.dict(os.environ, {
            "HF_TOKEN": "hf_test_token",
            "PROLIFIC_API_KEY": "prolific_test_key"
        }):
            results = validate_secrets()
            assert results["HF_TOKEN"] is True
            assert results["PROLIFIC_API_KEY"] is True
    
    def test_validate_missing_required(self):
        """Test validation raises error when required secret is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required secrets"):
                validate_secrets()
    
    def test_validate_empty_string_treated_as_missing(self):
        """Test that empty string is treated as missing."""
        with patch.dict(os.environ, {"HF_TOKEN": ""}):
            with pytest.raises(ValueError, match="Missing required secrets"):
                validate_secrets()


class TestSecretsManager:
    """Tests for SecretsManager class."""
    
    def test_context_manager_validates(self, tmp_path):
        """Test that context manager validates secrets."""
        env_file = tmp_path / ".env"
        env_file.write_text("HF_TOKEN=test_token\nPROLIFIC_API_KEY=test_key")
        
        with patch('code.secrets_manager.load_env_file', return_value=True):
            with SecretsManager(env_path=str(env_file), validate_on_enter=True) as sm:
                assert sm._validated is True
    
    def test_context_manager_without_validation(self):
        """Test context manager without automatic validation."""
        with SecretsManager(validate_on_enter=False) as sm:
            assert sm._validated is False
    
    def test_get_after_validation(self):
        """Test getting secrets after validation."""
        with patch.dict(os.environ, {"HF_TOKEN": "test_token"}):
            with SecretsManager(validate_on_enter=True) as sm:
                token = sm.get("HF_TOKEN", required=False)
                assert token == "test_token"
    
    def test_get_without_validation_raises(self):
        """Test that getting required secret without validation raises error."""
        with SecretsManager(validate_on_enter=False) as sm:
            with pytest.raises(RuntimeError, match="Secrets not validated"):
                sm.get("HF_TOKEN", required=True)
    
    def test_properties(self):
        """Test property accessors."""
        with patch.dict(os.environ, {"HF_TOKEN": "hf_token"}):
            with SecretsManager(validate_on_enter=True) as sm:
                assert sm.hf_token == "hf_token"
                
                # Prolific key is optional
                prolific_key = sm.prolific_api_key
                assert prolific_key is None  # Not set in env


class TestInitSecrets:
    """Tests for init_secrets function."""
    
    def test_init_secrets_basic(self):
        """Test basic initialization."""
        with patch('code.secrets_manager.load_env_file', return_value=True):
            sm = init_secrets()
            assert isinstance(sm, SecretsManager)
            assert sm._validated is False  # Default is no validation on init
    
    def test_init_secrets_with_path(self, tmp_path):
        """Test initialization with specific path."""
        env_file = tmp_path / ".env"
        env_file.write_text("HF_TOKEN=test_token")
        
        with patch('code.secrets_manager.load_env_file', return_value=True):
            sm = init_secrets(str(env_file))
            assert sm.env_path == str(env_file)
