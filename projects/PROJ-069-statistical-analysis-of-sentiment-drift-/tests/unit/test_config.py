import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from config import (
    load_environment,
    get_fred_api_key,
    get_hf_token,
    get_gdelt_api_key,
    validate_environment,
    PROJECT_ROOT,
    ENV_FILE
)

class TestProjectRootDetection:
    def test_project_root_detection(self):
        """Test that PROJECT_ROOT is correctly identified as the parent of code/"""
        assert PROJECT_ROOT == Path(__file__).resolve().parent.parent.parent
        assert PROJECT_ROOT.exists()
        assert (PROJECT_ROOT / "code").exists()

class TestLoadEnvironment:
    @patch('config.load_dotenv')
    def test_load_environment_with_existing_file(self, mock_load_dotenv):
        """Test loading environment when .env file exists"""
        mock_load_dotenv.return_value = True
        
        with patch.object(ENV_FILE.__class__, 'exists', return_value=True):
            result = load_environment()
            assert result is True
            mock_load_dotenv.assert_called_once()

    @patch('config.load_dotenv')
    def test_load_environment_with_missing_file(self, mock_load_dotenv):
        """Test loading environment when .env file doesn't exist"""
        with patch.object(ENV_FILE.__class__, 'exists', return_value=False):
            result = load_environment()
            assert result is False
            mock_load_dotenv.assert_not_called()

class TestGetFredApiKey:
    @patch.dict(os.environ, {"FRED_API_KEY": "test_key_123"})
    def test_get_fred_api_key_success(self):
        """Test successful retrieval of FRED API key"""
        key = get_fred_api_key()
        assert key == "test_key_123"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_fred_api_key_missing(self):
        """Test retrieval when FRED API key is not set"""
        key = get_fred_api_key()
        assert key is None

class TestGetHfToken:
    @patch.dict(os.environ, {"HF_TOKEN": "hf_test_token"})
    def test_get_hf_token_success(self):
        """Test successful retrieval of HF token"""
        token = get_hf_token()
        assert token == "hf_test_token"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_hf_token_not_set(self):
        """Test retrieval when HF token is not set"""
        token = get_hf_token()
        assert token is None

    def test_get_hf_token_optional(self):
        """Test that HF token is treated as optional in validation"""
        with patch.dict(os.environ, {"FRED_API_KEY": "test_key"}):
            is_valid, missing = validate_environment()
            assert is_valid is True
            assert "HF_TOKEN" not in missing

class TestGetGdeltApiKey:
    @patch.dict(os.environ, {"GDELT_API_KEY": "gdelt_test_key"})
    def test_get_gdelt_api_key_success(self):
        """Test successful retrieval of GDELT API key"""
        key = get_gdelt_api_key()
        assert key == "gdelt_test_key"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_gdelt_api_key_not_set(self):
        """Test retrieval when GDELT API key is not set"""
        key = get_gdelt_api_key()
        assert key is None

class TestValidateEnvironment:
    @patch.dict(os.environ, {"FRED_API_KEY": "test_key"})
    def test_validate_environment_with_keys(self):
        """Test validation when all required keys are present"""
        is_valid, missing = validate_environment()
        assert is_valid is True
        assert len(missing) == 0

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_environment_with_missing_keys(self):
        """Test validation when required keys are missing"""
        is_valid, missing = validate_environment()
        assert is_valid is False
        assert "FRED_API_KEY" in missing

    @patch.dict(os.environ, {"FRED_API_KEY": "test_key", "HF_TOKEN": "test_token"})
    def test_validate_environment_with_optional_keys(self):
        """Test validation when optional keys are also present"""
        is_valid, missing = validate_environment()
        assert is_valid is True
        assert len(missing) == 0

    def test_validate_environment_returns_tuple(self):
        """Test that validate_environment returns a tuple of (bool, list)"""
        is_valid, missing = validate_environment()
        assert isinstance(is_valid, bool)
        assert isinstance(missing, list)