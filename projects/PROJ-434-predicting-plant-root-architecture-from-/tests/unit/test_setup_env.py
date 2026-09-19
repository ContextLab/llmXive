"""
Unit tests for environment configuration management.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_env import (
    create_default_env_file,
    validate_required_env_vars,
    validate_optional_env_vars,
    load_environment,
    get_env,
    get_config,
    validate_config,
    REQUIRED_ENV_VARS,
    OPTIONAL_ENV_VARS
)

@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text("RUN_MODE=test\nRANDOM_SEED=123\n")
    return env_file

@pytest.fixture
def clean_env():
    """Clean environment variables before and after test."""
    # Save current state
    saved_env = {}
    for var in ["RUN_MODE", "RANDOM_SEED", "PERMUTATION_ITERATIONS", "SOILGRIDS_API_KEY", "ZENODO_API_TOKEN"]:
        if var in os.environ:
            saved_env[var] = os.environ[var]
        if var in os.environ:
            del os.environ[var]
    
    yield
  
    # Restore state
    for var, value in saved_env.items():
        os.environ[var] = value
    for var in saved_env:
        if var in os.environ:
            del os.environ[var]

def test_create_default_env_file(tmp_path, clean_env):
    """Test creation of default .env file."""
    env_file = tmp_path / ".env"
    
    # File should not exist initially
    assert not env_file.exists()
    
    # Create the file
    result = create_default_env_file(env_file)
    
    # Verify file was created
    assert result is True
    assert env_file.exists()
    
    # Verify content
    content = env_file.read_text()
    assert "RUN_MODE=production" in content
    assert "RANDOM_SEED=42" in content
    assert "PERMUTATION_ITERATIONS=1000" in content

def test_create_default_env_file_already_exists(tmp_path, clean_env):
    """Test that create_default_env_file returns True if file exists."""
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING=content\n")
    
    result = create_default_env_file(env_file)
    
    assert result is True
    assert env_file.read_text() == "EXISTING=content\n"

def test_validate_required_env_vars_missing(clean_env):
    """Test validation with missing required variables."""
    # No environment variables set
    missing = validate_required_env_vars()
    
    assert "RUN_MODE" in missing

def test_validate_required_env_vars_present(clean_env):
    """Test validation with all required variables present."""
    os.environ["RUN_MODE"] = "production"
    
    missing = validate_required_env_vars()
    
    assert len(missing) == 0

def test_validate_optional_env_vars(clean_env):
    """Test validation of optional variables."""
    # Set one optional variable
    os.environ["SOILGRIDS_API_KEY"] = "test_key"
    
    missing = validate_optional_env_vars()
    
    assert "SOILGRIDS_API_KEY" not in missing
    assert "ZENODO_API_TOKEN" in missing

def test_load_environment_creates_file(tmp_path, clean_env):
    """Test that load_environment creates a default file if missing."""
    env_file = tmp_path / ".env"
    
    with patch('setup_env.ENV_FILE_PATH', env_file):
        result = load_environment()
    
    assert result is True
    assert env_file.exists()

def test_load_environment_existing_file(tmp_path, clean_env):
    """Test loading from an existing .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("RUN_MODE=test\nRANDOM_SEED=999\n")
    
    with patch('setup_env.ENV_FILE_PATH', env_file):
        with patch('setup_env.load_dotenv') as mock_load_dotenv:
            result = load_environment()
    
    assert result is True
    mock_load_dotenv.assert_called_once_with(env_file)

def test_get_env_with_value(clean_env):
    """Test get_env with a set variable."""
    os.environ["TEST_VAR"] = "test_value"
    
    result = get_env("TEST_VAR")
    
    assert result == "test_value"

def test_get_env_without_value(clean_env):
    """Test get_env with an unset variable."""
    result = get_env("NONEXISTENT_VAR")
    
    assert result is None

def test_get_env_with_default(clean_env):
    """Test get_env with a default value."""
    result = get_env("NONEXISTENT_VAR", "default_value")
    
    assert result == "default_value"

def test_get_config_success(clean_env, tmp_path):
    """Test successful configuration loading."""
    env_file = tmp_path / ".env"
    env_file.write_text("RUN_MODE=test\nRANDOM_SEED=123\n")
    
    with patch('setup_env.ENV_FILE_PATH', env_file):
        config = get_config()
    
    assert config["run_mode"] == "test"
    assert config["random_seed"] == 123
    assert config["permutation_iterations"] == 1000

def test_get_config_missing_required(clean_env, tmp_path):
    """Test get_config with missing required variables."""
    env_file = tmp_path / ".env"
    env_file.write_text("# Empty file\n")
    
    with patch('setup_env.ENV_FILE_PATH', env_file):
        with pytest.raises(ValueError, match="Missing required environment variables"):
            get_config()

def test_validate_config_valid():
    """Test validation of valid configuration."""
    config = {
        "run_mode": "production",
        "random_seed": 42,
        "permutation_iterations": 1000,
        "soilgrids_api_key": None,
        "zenodo_api_token": None,
        "missing_optional_vars": {}
    }
    
    assert validate_config(config) is True

def test_validate_config_invalid_run_mode():
    """Test validation with invalid run_mode."""
    config = {
        "run_mode": "invalid_mode",
        "random_seed": 42,
        "permutation_iterations": 1000,
        "soilgrids_api_key": None,
        "zenodo_api_token": None,
        "missing_optional_vars": {}
    }
    
    assert validate_config(config) is False

def test_validate_config_invalid_random_seed():
    """Test validation with invalid random_seed."""
    config = {
        "run_mode": "production",
        "random_seed": -1,
        "permutation_iterations": 1000,
        "soilgrids_api_key": None,
        "zenodo_api_token": None,
        "missing_optional_vars": {}
    }
    
    assert validate_config(config) is False

def test_validate_config_invalid_permutation_iterations():
    """Test validation with invalid permutation_iterations."""
    config = {
        "run_mode": "production",
        "random_seed": 42,
        "permutation_iterations": 0,
        "soilgrids_api_key": None,
        "zenodo_api_token": None,
        "missing_optional_vars": {}
    }
    
    assert validate_config(config) is False
