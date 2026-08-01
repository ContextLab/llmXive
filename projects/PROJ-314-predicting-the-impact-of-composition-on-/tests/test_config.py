"""
Unit tests for configuration management (T011).
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the module under test
# Note: We need to handle the import carefully since config.py imports from .
import sys
from unittest.mock import patch, MagicMock

@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_content = """
    TEST_VAR=test_value
    TEST_INT=42
    TEST_FLOAT=3.14
    TEST_BOOL=true
    HF_TOKEN=hf_test_token_123
    DATA_SOURCE_URL=https://test.example.com/data.csv
    LOG_LEVEL=DEBUG
    """
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    return env_file

@pytest.fixture
def mock_project_root(tmp_path):
    """Mock the PROJECT_ROOT to point to temp directory."""
    # We need to mock the config module's behavior
    with patch('code.config.PROJECT_ROOT', tmp_path):
        yield tmp_path

def test_env_loading(mock_project_root, temp_env_file):
    """
    Test that environment variables are loaded from .env file.
    T011 Requirement: Implement load_env() in code/__init__.py (moved to config.py)
    and verify it works.
    """
    # Force re-initialization
    import importlib
    import code.config
    
    # Reset the module state
    code.config._initialized = False
    code.config._config = {}
    
    # Load the environment
    result = code.config.load_environment()
    
    # Verify loading succeeded
    assert result is True, "load_environment() should return True when .env exists"
    
    # Verify variables are accessible via os.getenv
    assert os.getenv("TEST_VAR") == "test_value"
    assert os.getenv("HF_TOKEN") == "hf_test_token_123"
    assert os.getenv("DATA_SOURCE_URL") == "https://test.example.com/data.csv"
    assert os.getenv("LOG_LEVEL") == "DEBUG"

def test_initialize_config(mock_project_root, temp_env_file):
    """Test that initialize_config() loads and sets up defaults."""
    import importlib
    import code.config
    
    # Reset state
    code.config._initialized = False
    code.config._config = {}
    
    # Initialize
    config = code.config.initialize_config()
    
    # Verify structure
    assert "project_root" in config
    assert "data_dir" in config
    assert "log_level" in config
    assert config["log_level"] == "DEBUG"  # From .env
    assert config["hf_token"] == "hf_test_token_123"  # From .env

def test_get_config_value(mock_project_root, temp_env_file):
    """Test get_config_value() retrieves correct values."""
    import code.config
    
    code.config._initialized = False
    code.config._config = {}
    code.config.initialize_config()
    
    # Test existing key
    assert code.config.get_config_value("log_level") == "DEBUG"
    
    # Test missing key with default
    assert code.config.get_config_value("nonexistent", "default") == "default"
    
    # Test missing key without default
    assert code.config.get_config_value("nonexistent") is None

def test_get_int_config(mock_project_root, temp_env_file):
    """Test get_int_config() correctly parses integers."""
    import code.config
    
    code.config._initialized = False
    code.config._config = {}
    code.config.initialize_config()
    
    # Test valid int
    assert code.config.get_int_config("test_int") == 42
    
    # Test missing with default
    assert code.config.get_int_config("missing_int", 10) == 10
    
    # Test invalid conversion
    code.config._config["bad_int"] = "not_a_number"
    assert code.config.get_int_config("bad_int", 99) == 99

def test_get_float_config(mock_project_root, temp_env_file):
    """Test get_float_config() correctly parses floats."""
    import code.config
    
    code.config._initialized = False
    code.config._config = {}
    code.config.initialize_config()
    
    # Test valid float
    assert code.config.get_float_config("test_float") == 3.14
    
    # Test missing with default
    assert code.config.get_float_config("missing_float", 2.71) == 2.71

def test_get_bool_config(mock_project_root, temp_env_file):
    """Test get_bool_config() correctly parses booleans."""
    import code.config
    
    code.config._initialized = False
    code.config._config = {}
    code.config.initialize_config()
    
    # Test true values
    code.config._config["bool_true"] = "true"
    assert code.config.get_bool_config("bool_true") is True
    
    code.config._config["bool_one"] = "1"
    assert code.config.get_bool_config("bool_one") is True
    
    # Test false values
    code.config._config["bool_false"] = "false"
    assert code.config.get_bool_config("bool_false") is False
    
    # Test missing with default
    assert code.config.get_bool_config("missing_bool", True) is True

def test_get_api_key(mock_project_root, temp_env_file):
    """Test get_api_key() retrieves service-specific keys."""
    import code.config
    
    code.config._initialized = False
    code.config._config = {}
    code.config.initialize_config()
    
    # Test HF token
    assert code.config.get_api_key("hf") == "hf_test_token_123"
    
    # Test non-existent service
    assert code.config.get_api_key("nonexistent") is None

def test_get_data_source_url(mock_project_root, temp_env_file):
    """Test get_data_source_url() retrieves the configured URL."""
    import code.config
    
    code.config._initialized = False
    code.config._config = {}
    code.config.initialize_config()
    
    expected_url = "https://test.example.com/data.csv"
    assert code.config.get_data_source_url() == expected_url

def test_missing_env_file(tmp_path):
    """Test behavior when .env file is missing."""
    # Create a temp directory without .env
    with patch('code.config.PROJECT_ROOT', tmp_path):
        import importlib
        import code.config
        
        code.config._initialized = False
        code.config._config = {}
        
        # Should return False and not raise
        result = code.config.load_environment()
        assert result is False
        
        # Should still initialize with defaults
        config = code.config.initialize_config()
        assert config is not None