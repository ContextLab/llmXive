"""
Tests for the environment variable loading utilities.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.env_loader import (
    load_env_vars,
    get_model_path,
    validate_token,
    REQUIRED_VARS,
    OPTIONAL_VARS
)

@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "HF_TOKEN=hf_test_token_1234567890\n"
        "HF_HOME=/tmp/test_hf_home\n"
        "MODEL_PATH=/tmp/test_model_path\n"
    )
    return str(env_file)

@patch('utils.env_loader.os.getenv')
def test_load_env_vars_missing_required(mock_getenv):
    """Test that load_env_vars raises ValueError when required vars are missing."""
    mock_getenv.return_value = None  # Simulate missing env vars
    
    with pytest.raises(ValueError) as exc_info:
        load_env_vars()
    
    assert "Missing required environment variables" in str(exc_info.value)
    assert "HF_TOKEN" in str(exc_info.value)

@patch('utils.env_loader.os.getenv')
def test_load_env_vars_success(mock_getenv):
    """Test successful loading of environment variables."""
    def mock_get_side_effect(var):
        values = {
            'HF_TOKEN': 'hf_valid_token_1234567890',
            'HF_HOME': '/custom/hf/home',
            'MODEL_PATH': '/custom/model/path'
        }
        return values.get(var)
    
    mock_getenv.side_effect = mock_get_side_effect
    
    result = load_env_vars()
    
    assert 'HF_TOKEN' in result
    assert 'HF_HOME' in result
    assert 'MODEL_PATH' in result
    assert result['HF_TOKEN'] == 'hf_valid_token_1234567890'

def test_validate_token_valid():
    """Test validation of a valid token."""
    assert validate_token("hf_valid_token_1234567890") is True

def test_validate_token_invalid_format():
    """Test validation of an invalid token format."""
    assert validate_token("invalid_token") is False
    assert validate_token("hf_short") is False
    assert validate_token("") is False
    assert validate_token(None) is False

@patch('utils.env_loader.os.getenv')
def test_validate_token_from_env(mock_getenv):
    """Test token validation when reading from environment variable."""
    mock_getenv.return_value = 'hf_env_token_1234567890'
    
    assert validate_token() is True

@patch('utils.env_loader.os.getenv')
@patch('utils.env_loader.Path.mkdir')
def test_get_model_path_default(mock_mkdir, mock_getenv):
    """Test getting default model path."""
    mock_getenv.return_value = None  # No env vars set
    
    path = get_model_path()
    
    # Should default to ~/.cache/huggingface/hub
    assert path.parts[-3:] == ('.cache', 'huggingface', 'hub')
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

@patch('utils.env_loader.os.getenv')
@patch('utils.env_loader.Path.mkdir')
def test_get_model_path_with_hf_home(mock_mkdir, mock_getenv):
    """Test model path with HF_HOME set."""
    mock_getenv.side_effect = lambda var: '/custom/hf/home' if var == 'HF_HOME' else None
    
    path = get_model_path()
    
    assert str(path) == '/custom/hf/home/hub'

@patch('utils.env_loader.os.getenv')
@patch('utils.env_loader.Path.mkdir')
def test_get_model_path_with_model_path_override(mock_mkdir, mock_getenv):
    """Test model path with MODEL_PATH override."""
    mock_getenv.side_effect = lambda var: '/explicit/model/path' if var == 'MODEL_PATH' else None
    
    path = get_model_path()
    
    assert str(path) == '/explicit/model/path'

@patch('utils.env_loader.os.getenv')
@patch('utils.env_loader.Path.mkdir')
def test_get_model_path_with_model_name(mock_mkdir, mock_getenv):
    """Test model path with specific model name."""
    mock_getenv.return_value = None
    
    path = get_model_path("codellama-7b")
    
    assert path.name == "codellama-7b"
    assert path.parent.parts[-3:] == ('.cache', 'huggingface', 'hub')

def test_load_env_vars_with_file(temp_env_file):
    """Test loading environment variables from a specific .env file."""
    # Clear existing env vars
    for var in REQUIRED_VARS + OPTIONAL_VARS:
        if var in os.environ:
            del os.environ[var]
    
    result = load_env_vars(temp_env_file)
    
    assert 'HF_TOKEN' in result
    assert result['HF_TOKEN'] == 'hf_test_token_1234567890'
    assert result['HF_HOME'] == '/tmp/test_hf_home'
    assert result['MODEL_PATH'] == '/tmp/test_model_path'
