import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure code/ is in path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import (
    load_environment,
    validate_environment,
    get_fred_api_key,
    get_hf_token,
    get_gdelt_api_key,
)


def test_project_root_detection():
    """Test that the config module correctly identifies the project root."""
    # The config module uses __file__ to find the root.
    # We just verify the module can be imported without error.
    from config import _project_root
    assert _project_root.exists()
    assert _project_root.name == "PROJ-069-statistical-analysis-of-sentiment-drift-"


@patch("os.getenv")
def test_validate_environment_with_missing_keys(mock_getenv):
    """Test validation fails when FRED_API_KEY is missing."""
    mock_getenv.side_effect = lambda key: None
    assert validate_environment() is False


@patch("os.getenv")
def test_validate_environment_with_keys(mock_getenv):
    """Test validation passes when FRED_API_KEY is present."""
    def mock_get_side_effect(key):
        if key == "FRED_API_KEY":
            return "test_key"
        return None
    mock_getenv.side_effect = mock_get_side_effect
    assert validate_environment() is True


@patch("os.getenv")
def test_get_fred_api_key_success(mock_getenv):
    """Test successful retrieval of FRED API key."""
    mock_getenv.return_value = "test_key_123"
    key = get_fred_api_key()
    assert key == "test_key_123"


@patch("os.getenv")
def test_get_fred_api_key_missing(mock_getenv):
    """Test that get_fred_api_key raises ValueError when key is missing."""
    mock_getenv.return_value = None
    with pytest.raises(ValueError, match="FRED_API_KEY environment variable is not set"):
        get_fred_api_key()


@patch("os.getenv")
def test_get_hf_token_optional(mock_getenv):
    """Test that HF token returns None if not set."""
    mock_getenv.return_value = None
    assert get_hf_token() is None


@patch("os.getenv")
def test_get_hf_token_not_set(mock_getenv):
    """Test HF token retrieval when explicitly not set."""
    mock_getenv.return_value = None
    assert get_hf_token() is None


@patch("os.getenv")
def test_get_gdelt_api_key_not_set(mock_getenv):
    """Test GDELT key retrieval when not set."""
    mock_getenv.return_value = None
    assert get_gdelt_api_key() is None


@patch("os.getenv")
def test_get_gdelt_api_key_success(mock_getenv):
    """Test successful retrieval of GDELT API key."""
    mock_getenv.return_value = "gdelt_test_key"
    key = get_gdelt_api_key()
    assert key == "gdelt_test_key"


@patch("config._env_path")
@patch("config.load_dotenv")
def test_load_environment(mock_load_dotenv, mock_env_path):
    """Test that load_environment attempts to load the .env file."""
    mock_env_path.exists.return_value = True
    result = load_environment()
    mock_load_dotenv.assert_called_once()
    assert result is True
