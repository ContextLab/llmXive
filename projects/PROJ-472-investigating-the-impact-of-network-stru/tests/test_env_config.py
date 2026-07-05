"""
Tests for environment configuration management (T008).

These tests verify that:
1. .env files are loaded correctly
2. Environment variables are retrieved with proper type conversion
3. Required variables raise appropriate errors
4. Default values are used when variables are missing
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from utils.env_config import (
    load_environment,
    get_env_variable,
    get_data_root,
    get_simulation_seed,
    get_log_level,
    setup_env_config,
    REQUIRED_VARS
)

class TestEnvLoading:
    """Tests for .env file loading functionality."""
    
    def test_load_environment_creates_vars(self, tmp_path):
        """Test that loading a .env file populates environment variables."""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=hello\nTEST_NUM=42\n")
        
        # Load the environment
        result = load_environment(env_file)
        
        assert result is True
        assert os.getenv("TEST_VAR") == "hello"
        assert os.getenv("TEST_NUM") == "42"
        
        # Clean up
        os.unsetenv("TEST_VAR")
        os.unsetenv("TEST_NUM")
        
    def test_load_environment_missing_file(self, tmp_path):
        """Test behavior when .env file does not exist."""
        non_existent = tmp_path / "nonexistent.env"
        
        result = load_environment(non_existent)
        
        assert result is False
        
    def test_load_environment_idempotent(self, tmp_path):
        """Test that loading environment multiple times is safe."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=first\n")
        
        load_environment(env_file)
        first_val = os.getenv("TEST_VAR")
        
        # Load again
        load_environment(env_file)
        second_val = os.getenv("TEST_VAR")
        
        assert first_val == second_val == "first"
        
        # Cleanup
        os.unsetenv("TEST_VAR")
        
class TestVariableRetrieval:
    """Tests for get_env_variable functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset environment for each test
        if "TEST_VAR" in os.environ:
            del os.environ["TEST_VAR"]
        if "TEST_INT" in os.environ:
            del os.environ["TEST_INT"]
            
    def test_get_env_variable_with_default(self):
        """Test retrieving a variable with a default value."""
        result = get_env_variable("NONEXISTENT_VAR", default="fallback")
        assert result == "fallback"
        
    def test_get_env_variable_required_missing(self):
        """Test that required missing variable raises error."""
        with pytest.raises(ValueError, match="Required environment variable"):
            get_env_variable("NONEXISTENT_VAR", required=True)
            
    def test_get_env_variable_type_conversion_int(self):
        """Test integer type conversion."""
        os.environ["TEST_INT"] = "123"
        result = get_env_variable("TEST_INT", default=0)
        assert result == 123
        assert isinstance(result, int)
        
    def test_get_env_variable_type_conversion_bool_true(self):
        """Test boolean type conversion for true values."""
        for val in ["true", "True", "TRUE", "1", "yes"]:
            os.environ["TEST_BOOL"] = val
            result = get_env_variable("TEST_BOOL", default=False)
            assert result is True
            del os.environ["TEST_BOOL"]
            
    def test_get_env_variable_type_conversion_bool_false(self):
        """Test boolean type conversion for false values."""
        for val in ["false", "False", "FALSE", "0", "no", "off"]:
            os.environ["TEST_BOOL"] = val
            result = get_env_variable("TEST_BOOL", default=True)
            assert result is False
            del os.environ["TEST_BOOL"]
            
    def test_get_env_variable_invalid_conversion(self):
        """Test handling of invalid type conversions."""
        os.environ["TEST_INT"] = "not_a_number"
        result = get_env_variable("TEST_INT", default=999)
        assert result == 999  # Should fall back to default
        
        del os.environ["TEST_INT"]
        
class TestConfigFunctions:
    """Tests for high-level configuration functions."""
    
    def setup_method(self):
        """Ensure required variables are set for setup_env_config."""
        os.environ["SIMULATION_SEED"] = "42"
        os.environ["LOG_LEVEL"] = "INFO"
        
    def teardown_method(self):
        """Clean up environment variables."""
        if "SIMULATION_SEED" in os.environ:
            del os.environ["SIMULATION_SEED"]
        if "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]
            
    def test_setup_env_config_returns_dict(self):
        """Test that setup_env_config returns a dictionary."""
        config = setup_env_config()
        assert isinstance(config, dict)
        assert "simulation_seed" in config
        assert "data_root" in config
        
    def test_setup_env_config_required_vars(self):
        """Test that required variables are present in config."""
        config = setup_env_config()
        assert config["simulation_seed"] == 42
        assert config["log_level"] == "INFO"
        
    def test_get_simulation_seed(self):
        """Test getting simulation seed."""
        os.environ["SIMULATION_SEED"] = "999"
        seed = get_simulation_seed()
        assert seed == 999
        assert isinstance(seed, int)
        del os.environ["SIMULATION_SEED"]
        
    def test_get_log_level(self):
        """Test getting log level."""
        os.environ["LOG_LEVEL"] = "DEBUG"
        level = get_log_level()
        assert level == "DEBUG"
        del os.environ["LOG_LEVEL"]
        
    def test_get_data_root_default(self):
        """Test that get_data_root returns a valid Path."""
        from utils.env_config import get_data_root
        data_root = get_data_root()
        assert isinstance(data_root, Path)
        assert data_root.exists()
        
class TestRequiredVariables:
    """Tests for required environment variable validation."""
    
    def test_required_vars_list(self):
        """Test that required variables are defined."""
        assert "SIMULATION_SEED" in REQUIRED_VARS
        assert "LOG_LEVEL" in REQUIRED_VARS
        
    def test_missing_required_var_in_setup(self):
        """Test that missing required variable causes setup to fail."""
        # Remove required variables
        if "SIMULATION_SEED" in os.environ:
            del os.environ["SIMULATION_SEED"]
            
        with pytest.raises(ValueError, match="Missing required environment variables"):
            setup_env_config()