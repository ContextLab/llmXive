"""
Tests for the environment variable management module (env_manager.py).

These tests verify that:
1. Environment variables are loaded correctly from .env files
2. Default paths are constructed correctly
3. Path validation works as expected
4. Fallback mechanisms function properly
"""

import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the module under test
from code import env_manager

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure simulating a project."""
    temp_dir = tempfile.mkdtemp()
    
    # Create a minimal project structure
    code_dir = Path(temp_dir) / "code"
    code_dir.mkdir()
    data_dir = Path(temp_dir) / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    (code_dir / "models").mkdir()
    (code_dir / "analysis").mkdir()
    
    # Create a dummy .env file
    env_content = """
    DATA_ROOT_PATH=/custom/data/root
    DATA_RAW_PATH=/custom/data/raw
    DATA_PROCESSED_PATH=/custom/data/processed
    MODEL_ARTIFACTS_PATH=/custom/code/models/artifacts
    DATA_FIGURES_PATH=/custom/data/figures
    """
    env_file = code_dir / ".env"
    env_file.write_text(env_content)
    
    # Create a dummy __init__.py
    (code_dir / "__init__.py").write_text("")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_get_project_root(temp_project_dir):
    """Test that project root is correctly identified."""
    # Change to the temp directory
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_dir)
        # Reset the cached project root
        env_manager._PROJECT_ROOT = None
        
        root = env_manager._get_project_root()
        assert root == Path(temp_project_dir)
    finally:
        os.chdir(original_cwd)

def test_load_env_vars_from_file(temp_project_dir):
    """Test loading environment variables from a .env file."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_dir)
        
        # Load env vars
        env_vars = env_manager.load_env_vars()
        
        assert "DATA_ROOT_PATH" in env_vars
        assert env_vars["DATA_ROOT_PATH"] == "/custom/data/root"
        assert env_vars["DATA_RAW_PATH"] == "/custom/data/raw"
    finally:
        os.chdir(original_cwd)

def test_get_env_var_fallback():
    """Test the fallback chain for getting environment variables."""
    # Set a real env var
    os.environ["TEST_VAR"] = "from_os_environ"
    
    # Test priority: passed dict > os.environ > default
    result = env_manager.get_env_var("TEST_VAR", default="default_value", env_vars={"TEST_VAR": "from_dict"})
    assert result == "from_dict"
    
    result = env_manager.get_env_var("TEST_VAR", default="default_value")
    assert result == "from_os_environ"
    
    result = env_manager.get_env_var("NON_EXISTENT_VAR", default="default_value")
    assert result == "default_value"
    
    # Cleanup
    del os.environ["TEST_VAR"]

def test_get_data_path_defaults(temp_project_dir):
    """Test that data paths default correctly when env vars are not set."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_dir)
        env_manager._PROJECT_ROOT = None  # Reset cache
        
        # Clear any existing env vars for these keys
        for key in [env_manager.ENV_DATA_ROOT, env_manager.ENV_DATA_RAW, env_manager.ENV_DATA_PROCESSED]:
            if key in os.environ:
                del os.environ[key]
        
        # Test default paths
        root = env_manager.get_data_path(env_var_name=env_manager.ENV_DATA_ROOT, default=env_manager.DEFAULT_DATA_ROOT)
        assert root == Path(temp_project_dir) / "data"
        
        raw = env_manager.get_data_path(env_var_name=env_manager.ENV_DATA_RAW, default=env_manager.DEFAULT_DATA_RAW)
        assert raw == Path(temp_project_dir) / "data" / "raw"
    finally:
        os.chdir(original_cwd)

def test_validate_data_paths(temp_project_dir):
    """Test path validation."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_dir)
        env_manager._PROJECT_ROOT = None  # Reset cache
        
        # The temp directory has the required structure
        results = env_manager.validate_data_paths()
        
        # All paths should exist in the temp setup
        assert results["data_root"] is True
        assert results["data_raw"] is True
        assert results["data_processed"] is True
    finally:
        os.chdir(original_cwd)

def test_get_silso_url():
    """Test getting the SILSO URL."""
    url = env_manager.get_silso_url()
    assert url is not None
    assert "sidc.be" in url

def test_get_sorce_url():
    """Test getting the SORCE URL."""
    url = env_manager.get_sorce_url()
    assert url is not None
    assert "colorado.edu" in url or "lasp" in url
