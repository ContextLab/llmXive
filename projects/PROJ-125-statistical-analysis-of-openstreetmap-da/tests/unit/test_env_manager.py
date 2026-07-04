"""
Unit tests for environment variable management.
"""

import os
import tempfile
from pathlib import Path
import pytest

# Mock the dotenv import if not present in test environment to avoid import errors
# but the actual code handles the ImportError gracefully.
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

from code.utils.env_manager import (
    get_api_key,
    get_config_value,
    validate_required_keys,
    load_environment,
    DEFAULT_ENV_PATH
)


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    content = (
        "OVERPASS_API_KEY=test_overpass_key_123\n"
        "AWS_ACCESS_KEY_ID=test_aws_key_456\n"
        "MAX_BLOCKS=50\n"
        "DEBUG_MODE=true\n"
        "FLOAT_VAL=3.14\n"
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(content)
        path = Path(f.name)
    yield path
    path.unlink()


def test_load_environment_success(temp_env_file):
    """Test loading a valid .env file."""
    if not HAS_DOTENV:
        pytest.skip("python-dotenv not installed")
    
    # Clear any existing keys to ensure we test the load
    if "OVERPASS_API_KEY" in os.environ:
        del os.environ["OVERPASS_API_KEY"]
    
    result = load_environment(temp_env_file)
    assert result is True
    assert os.getenv("OVERPASS_API_KEY") == "test_overpass_key_123"


def test_load_environment_missing_file():
    """Test loading a non-existent .env file."""
    fake_path = Path("/non/existent/path/.env")
    result = load_environment(fake_path)
    # Should return False and log warning, not crash
    assert result is False


def test_get_api_key_success(temp_env_file):
    """Test retrieving an API key after loading."""
    if not HAS_DOTENV:
        pytest.skip("python-dotenv not installed")
    
    load_environment(temp_env_file)
    key = get_api_key("OVERPASS", required=False)
    assert key == "test_overpass_key_123"


def test_get_api_key_missing_required(temp_env_file):
    """Test that missing required key raises ValueError."""
    if not HAS_DOTENV:
        pytest.skip("python-dotenv not installed")
    
    load_environment(temp_env_file)
    # Request a key that doesn't exist
    with pytest.raises(ValueError, match="Required API key"):
        get_api_key("NONEXISTENT_SERVICE", required=True)


def test_get_config_value_types(temp_env_file):
    """Test type casting for config values."""
    if not HAS_DOTENV:
        pytest.skip("python-dotenv not installed")
    
    load_environment(temp_env_file)
    
    # Integer
    val = get_config_value("MAX_BLOCKS", cast_type=int)
    assert val == 50
    
    # Float
    val = get_config_value("FLOAT_VAL", cast_type=float)
    assert abs(val - 3.14) < 0.001
    
    # Boolean
    val = get_config_value("DEBUG_MODE", cast_type=bool)
    assert val is True
    
    # Default value
    val = get_config_value("MISSING_KEY", default="default_val")
    assert val == "default_val"


def test_validate_required_keys(temp_env_file):
    """Test validation of multiple keys."""
    if not HAS_DOTENV:
        pytest.skip("python-dotenv not installed")
    
    load_environment(temp_env_file)
    
    # Valid set
    assert validate_required_keys(["OVERPASS", "AWS"]) is True
    
    # Invalid set
    assert validate_required_keys(["OVERPASS", "MISSING_SERVICE"]) is False
