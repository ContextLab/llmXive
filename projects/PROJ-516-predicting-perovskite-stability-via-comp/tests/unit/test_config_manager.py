"""
Unit tests for the configuration management module.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: The module is in code/utils/config_manager.py
# We need to adjust sys.path or assume tests are run with code/ in path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config_manager import load_dotenv_file, get_api_key, validate_environment, ConfigError

@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_content = """
    # Test environment
    MP_API_KEY=test_mp_key_12345
    NREL_API_KEY=test_nrel_key_67890
    EMPTY_VALUE=
    QUOTED_VALUE="quoted_value"
    SINGLE_QUOTED='single_quoted_value'
    """
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    return env_file

def test_load_dotenv_file_success(temp_env_file):
    """Test successful loading of .env file."""
    # Clear env vars first
    for key in ['MP_API_KEY', 'NREL_API_KEY', 'EMPTY_VALUE', 'QUOTED_VALUE', 'SINGLE_QUOTED']:
        os.environ.pop(key, None)
    
    result = load_dotenv_file(temp_env_file)
    assert result is True
    assert os.environ.get('MP_API_KEY') == 'test_mp_key_12345'
    assert os.environ.get('NREL_API_KEY') == 'test_nrel_key_67890'
    assert os.environ.get('EMPTY_VALUE') == ''
    assert os.environ.get('QUOTED_VALUE') == 'quoted_value'
    assert os.environ.get('SINGLE_QUOTED') == 'single_quoted_value'

def test_load_dotenv_file_not_found():
    """Test behavior when .env file does not exist."""
    result = load_dotenv_file(Path("/nonexistent/.env"))
    assert result is False

def test_get_api_key_success(temp_env_file):
    """Test retrieving an existing API key."""
    load_dotenv_file(temp_env_file)
    key = get_api_key('MP_API_KEY')
    assert key == 'test_mp_key_12345'

def test_get_api_key_missing_not_required():
    """Test retrieving a missing key when not required."""
    os.environ.pop('MISSING_KEY', None)
    key = get_api_key('MISSING_KEY', required=False)
    assert key is None

def test_get_api_key_missing_required():
    """Test retrieving a missing key when required."""
    os.environ.pop('MISSING_KEY', None)
    with pytest.raises(ConfigError, match="Required API key 'MISSING_KEY' is missing"):
        get_api_key('MISSING_KEY', required=True)

def test_validate_environment_success(temp_env_file):
    """Test successful environment validation."""
    load_dotenv_file(temp_env_file)
    status = validate_environment(['MP_API_KEY', 'NREL_API_KEY'])
    assert status['MP_API_KEY'] is True
    assert status['NREL_API_KEY'] is True

def test_validate_environment_failure(temp_env_file):
    """Test environment validation with missing keys."""
    load_dotenv_file(temp_env_file)
    os.environ.pop('NREL_API_KEY', None) # Remove one key
    with pytest.raises(ConfigError, match="The following required API keys are missing"):
        validate_environment(['MP_API_KEY', 'NREL_API_KEY'])
