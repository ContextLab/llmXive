"""
Tests for environment variable management.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: In a real run, ensure code/ is in sys.path
from code.env_manager import (
    load_env_vars,
    get_env_var,
    get_data_path,
    validate_data_paths,
    get_silso_url,
    get_sorce_url,
    get_model_artifacts_path,
    setup_environment
)

@pytest.fixture
def mock_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATA_ROOT=/tmp/test_data\n"
        "DATA_RAW_DIR=/tmp/test_data/raw\n"
        "DATA_PROCESSED_DIR=/tmp/test_data/processed\n"
        "MODEL_ARTIFACTS_DIR=/tmp/test_models\n"
        "SILSO_URL=http://test.com/silso\n"
        "SORCE_URL=http://test.com/sorce\n"
        "VALIDATE_PATHS=true\n"
        "LOG_LEVEL=DEBUG\n"
    )
    return env_file

def test_load_env_vars_creates_cache(mock_env_file):
    """Test that load_env_vars populates the internal cache."""
    # Reset state
    import code.env_manager as em
    em._IS_LOADED = False
    em._ENV_VARS = {}

    result = load_env_vars(mock_env_file)
    
    assert em._IS_LOADED is True
    assert "DATA_ROOT" in result
    assert result["DATA_ROOT"] == "/tmp/test_data"

def test_get_env_var_with_default():
    """Test getting an env var with a default value."""
    # Ensure loaded
    import code.env_manager as em
    if not em._IS_LOADED:
        em.load_env_vars()
    
    # Test existing var
    val = get_env_var("NONEXISTENT_VAR", default="fallback")
    assert val == "fallback"

def test_get_env_var_required_missing():
    """Test that required=True raises ValueError if missing."""
    import code.env_manager as em
    em._IS_LOADED = True # Pretend loaded
    em._ENV_VARS = {} # Empty cache

    with pytest.raises(ValueError, match="Required environment variable"):
        get_env_var("MISSING_REQUIRED_VAR", required=True)

def test_get_data_path():
    """Test constructing data paths."""
    import code.env_manager as em
    em._IS_LOADED = True
    em._ENV_VARS = {"DATA_ROOT": "/my/data"}
    
    root = get_data_path()
    assert str(root) == "/my/data"
    
    sub = get_data_path("raw")
    assert str(sub) == "/my/data/raw"

def test_validate_data_paths_creates_dirs(tmp_path):
    """Test that validate_data_paths creates missing directories."""
    import code.env_manager as em
    
    # Setup mock env
    em._IS_LOADED = True
    em._ENV_VARS = {
        "DATA_RAW_DIR": str(tmp_path / "raw"),
        "DATA_PROCESSED_DIR": str(tmp_path / "processed"),
        "MODEL_ARTIFACTS_DIR": str(tmp_path / "models"),
        "VALIDATE_PATHS": "true"
    }
    
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "processed").exists()
    
    result = validate_data_paths()
    
    assert result is True
    assert (tmp_path / "raw").exists()
    assert (tmp_path / "processed").exists()

def test_get_silso_url():
    """Test retrieving SILSO URL."""
    import code.env_manager as em
    em._IS_LOADED = True
    em._ENV_VARS = {"SILSO_URL": "http://example.com/silso"}
    
    url = get_silso_url()
    assert url == "http://example.com/silso"

def test_get_sorce_url():
    """Test retrieving SORCE URL."""
    import code.env_manager as em
    em._IS_LOADED = True
    em._ENV_VARS = {"SORCE_URL": "http://example.com/sorce"}
    
    url = get_sorce_url()
    assert url == "http://example.com/sorce"

def test_get_model_artifacts_path():
    """Test retrieving model artifacts path."""
    import code.env_manager as em
    em._IS_LOADED = True
    em._ENV_VARS = {"MODEL_ARTIFACTS_DIR": "/custom/models"}
    
    path = get_model_artifacts_path()
    assert str(path) == "/custom/models"

def test_setup_environment():
    """Test the main setup function."""
    import code.env_manager as em
    em._IS_LOADED = False
    em._ENV_VARS = {}
    
    # Mock validate_data_paths to avoid filesystem checks in test
    with patch.object(em, 'validate_data_paths', return_value=True):
        setup_environment()
    
    assert em._IS_LOADED is True