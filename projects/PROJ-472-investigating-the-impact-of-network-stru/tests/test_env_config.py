"""
Tests for environment configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from code.utils.env_config import (
    load_environment,
    get_env_variable,
    get_data_root,
    get_simulation_seed,
    get_log_level,
    setup_env_config
)

class TestLoadEnvironment:
    def test_load_from_existing_env_file(self):
        """Test loading from an existing .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("TEST_VAR=test_value\nANOTHER_VAR=123")
            
            # Mock project_root to point to tmpdir
            result = load_environment(Path(tmpdir))
            
            assert result is True
            assert os.getenv("TEST_VAR") == "test_value"
            assert os.getenv("ANOTHER_VAR") == "123"

    def test_load_from_missing_env_file(self):
        """Test loading when .env file does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No .env file created
            result = load_environment(Path(tmpdir))
            
            assert result is False

class TestGetEnvVariable:
    def test_get_existing_variable(self):
        """Test retrieving an existing environment variable."""
        os.environ["TEST_VAR"] = "test_value"
        result = get_env_variable("TEST_VAR")
        assert result == "test_value"
        del os.environ["TEST_VAR"]

    def test_get_with_default(self):
        """Test retrieving a variable with a default value."""
        result = get_env_variable("NONEXISTENT_VAR", default="default_val")
        assert result == "default_val"

    def test_get_required_variable_missing(self):
        """Test that required variable raises error when missing."""
        with pytest.raises(ValueError):
            get_env_variable("NONEXISTENT_REQUIRED", required=True)

    def test_cast_to_int(self):
        """Test casting environment variable to int."""
        os.environ["INT_VAR"] = "42"
        result = get_env_variable("INT_VAR", cast_to=int)
        assert result == 42
        del os.environ["INT_VAR"]

    def test_cast_to_bool_true(self):
        """Test casting string 'true' to boolean."""
        os.environ["BOOL_VAR"] = "true"
        result = get_env_variable("BOOL_VAR", cast_to=bool)
        assert result is True
        del os.environ["BOOL_VAR"]

    def test_cast_to_bool_false(self):
        """Test casting string 'false' to boolean."""
        os.environ["BOOL_VAR"] = "false"
        result = get_env_variable("BOOL_VAR", cast_to=bool)
        assert result is False
        del os.environ["BOOL_VAR"]

class TestGetSimulationSeed:
    def test_get_default_seed(self):
        """Test that default seed is 42 when not set."""
        # Ensure env var is not set
        if "SIMULATION_SEED" in os.environ:
            del os.environ["SIMULATION_SEED"]
        
        result = get_simulation_seed()
        assert result == 42

    def test_get_custom_seed(self):
        """Test getting custom seed from environment."""
        os.environ["SIMULATION_SEED"] = "12345"
        result = get_simulation_seed()
        assert result == 12345
        del os.environ["SIMULATION_SEED"]

class TestSetupEnvConfig:
    def test_setup_config(self):
        """Test the main setup function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("SIMULATION_SEED=999\nDATA_ROOT=/custom/data")
            
            config = setup_env_config(Path(tmpdir))
            
            assert config["env_loaded"] is True
            assert config["simulation_seed"] == 999
            assert config["data_root"] == "/custom/data"
            assert "log_level" in config
