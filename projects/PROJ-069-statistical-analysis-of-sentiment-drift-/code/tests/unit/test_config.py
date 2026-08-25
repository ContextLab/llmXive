import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from config import (
    get_fred_api_key,
    get_hf_token,
    get_gdelt_api_key,
    validate_environment,
    load_environment,
    main
)

def test_project_root_detection():
    """Test that PROJECT_ROOT is correctly detected relative to config.py"""
    from config import PROJECT_ROOT
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.exists()

def test_validate_environment_with_missing_keys(capsys):
    """Test that validate_environment raises KeyError when FRED_API_KEY is missing"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(KeyError) as excinfo:
            validate_environment()
        assert "FRED_API_KEY" in str(excinfo.value)

def test_validate_environment_with_keys(capsys):
    """Test that validate_environment passes when FRED_API_KEY is present"""
    with patch.dict(os.environ, {"FRED_API_KEY": "test_key_123"}):
        result = validate_environment()
        assert result is True

def test_get_fred_api_key_success():
    """Test successful retrieval of FRED API key"""
    with patch.dict(os.environ, {"FRED_API_KEY": "my_secret_key"}):
        key = get_fred_api_key()
        assert key == "my_secret_key"

def test_get_fred_api_key_missing():
    """Test that get_fred_api_key raises KeyError when missing"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(KeyError):
            get_fred_api_key()

def test_get_hf_token_optional():
    """Test that get_hf_token returns None when not set"""
    with patch.dict(os.environ, {}, clear=True):
        token = get_hf_token()
        assert token is None

def test_get_hf_token_not_set():
    """Test that get_hf_token returns the value when set"""
    with patch.dict(os.environ, {"HF_TOKEN": "hf_test_token"}):
        token = get_hf_token()
        assert token == "hf_test_token"

def test_get_gdelt_api_key_not_set():
    """Test that get_gdelt_api_key returns None when not set"""
    with patch.dict(os.environ, {}, clear=True):
        key = get_gdelt_api_key()
        assert key is None

def test_get_gdelt_api_key_success():
    """Test that get_gdelt_api_key returns the value when set"""
    with patch.dict(os.environ, {"GDELT_API_KEY": "gdelt_key_123"}):
        key = get_gdelt_api_key()
        assert key == "gdelt_key_123"

def test_load_environment():
    """Test that load_environment returns a dict with correct keys"""
    with patch.dict(os.environ, {
        "FRED_API_KEY": "fred123",
        "HF_TOKEN": "hf456",
        "GDELT_API_KEY": "gdelt789"
    }):
        config = load_environment()
        assert "fred_api_key" in config
        assert "hf_token" in config
        assert "gdelt_api_key" in config
        assert config["fred_api_key"] == "fred123"
        assert config["hf_token"] == "hf456"
        assert config["gdelt_api_key"] == "gdelt789"