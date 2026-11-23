"""
Tests for environment configuration management.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.environment_config import (
    get_hf_token,
    get_hf_cache_path,
    validate_hf_environment,
    set_hf_environment,
    load_environment_variables
)
from code.config import get_path_absolute

@pytest.fixture
def mock_env_vars():
    """Fixture to set up mock environment variables."""
    with patch.dict(os.environ, {
        "HF_TOKEN": "test_token_12345",
        "HF_HOME": "/tmp/test_hf_cache"
    }):
        yield

def test_get_hf_token_from_env(mock_env_vars):
    """Test retrieving token from environment variable."""
    token = get_hf_token()
    assert token == "test_token_12345"

def test_get_hf_token_not_found():
    """Test behavior when token is not found."""
    with patch.dict(os.environ, {}, clear=True):
        token = get_hf_token()
        assert token is None

def test_get_hf_cache_path_default():
    """Test default cache path when HF_HOME is not set."""
    with patch.dict(os.environ, {}, clear=True):
        # Remove any existing HF_HOME
        if "HF_HOME" in os.environ:
            del os.environ["HF_HOME"]
        
        cache_path = get_hf_cache_path()
        expected = Path.home() / ".cache" / "huggingface"
        assert cache_path == expected

def test_get_hf_cache_path_custom(mock_env_vars):
    """Test custom cache path when HF_HOME is set."""
    cache_path = get_hf_cache_path()
    assert cache_path == Path("/tmp/test_hf_cache")

def test_validate_hf_environment_success(mock_env_vars):
    """Test successful validation of HF environment."""
    # Ensure the cache directory can be created
    cache_path = Path("/tmp/test_hf_cache")
    cache_path.mkdir(parents=True, exist_ok=True)
    
    result = validate_hf_environment()
    assert result is True

def test_validate_hf_environment_no_token():
    """Test validation fails when token is missing."""
    with patch.dict(os.environ, {}, clear=True):
        result = validate_hf_environment()
        assert result is False

def test_load_environment_variables_file_exists(tmp_path):
    """Test loading from .env file when it exists."""
    env_file = tmp_path / ".env"
    env_file.write_text("HF_TOKEN=test_from_file\nHF_HOME=/tmp/test_env")
    
    with patch.dict(os.environ, {}, clear=True):
        with patch("code.environment_config.get_path_absolute", return_value=tmp_path):
            result = load_environment_variables()
            assert result is True
            assert os.getenv("HF_TOKEN") == "test_from_file"

def test_load_environment_variables_file_not_exists():
    """Test loading when .env file does not exist."""
    with patch("code.environment_config.get_path_absolute", return_value=Path("/nonexistent")):
        result = load_environment_variables()
        assert result is False
