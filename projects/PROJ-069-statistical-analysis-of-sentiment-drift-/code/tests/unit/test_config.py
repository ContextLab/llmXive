import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    load_environment,
    get_fred_api_key,
    get_hf_token,
    get_gdelt_api_key,
    validate_environment,
    main
)


def test_project_root_detection(tmp_path):
    """Test that project root is correctly detected."""
    # Create a temporary directory with a .env file
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_KEY=test_value\n")
    
    with patch('pathlib.Path.cwd', return_value=tmp_path):
        result = load_environment()
        assert result == tmp_path


def test_validate_environment_with_missing_keys():
    """Test validation fails when required keys are missing."""
    # Clear the environment
    with patch.dict(os.environ, {}, clear=True):
        assert not validate_environment(["FRED_API_KEY"])


def test_validate_environment_with_keys():
    """Test validation succeeds when required keys are present."""
    with patch.dict(os.environ, {"FRED_API_KEY": "test_key"}):
        assert validate_environment(["FRED_API_KEY"])


def test_get_fred_api_key_success():
    """Test successful retrieval of FRED API key."""
    with patch.dict(os.environ, {"FRED_API_KEY": "my_secret_key"}):
        key = get_fred_api_key()
        assert key == "my_secret_key"


def test_get_fred_api_key_missing():
    """Test KeyError when FRED API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(KeyError, match="FRED_API_KEY"):
            get_fred_api_key()


def test_get_hf_token_optional():
    """Test HF token retrieval when set."""
    with patch.dict(os.environ, {"HF_TOKEN": "hf_test_token"}):
        token = get_hf_token()
        assert token == "hf_test_token"


def test_get_hf_token_not_set():
    """Test HF token returns None when not set."""
    with patch.dict(os.environ, {}, clear=True):
        token = get_hf_token()
        assert token is None


def test_get_gdelt_api_key_optional():
    """Test GDELT API key retrieval when set."""
    with patch.dict(os.environ, {"GDELT_API_KEY": "gdelt_test_key"}):
        key = get_gdelt_api_key()
        assert key == "gdelt_test_key"


def test_get_gdelt_api_key_not_set():
    """Test GDELT API key returns None when not set."""
    with patch.dict(os.environ, {}, clear=True):
        key = get_gdelt_api_key()
        assert key is None