import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from config_env import (
    setup_environment,
    get_env_value,
    get_env_int,
    get_env_float,
    get_env_bool,
    validate_required_env_vars,
    create_env_template,
    get_env_config
)

@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    content = """
TEST_STRING=hello world
TEST_INT=42
TEST_FLOAT=3.14
TEST_BOOL=true
QUOTED_STRING="quoted value"
SINGLE_QUOTED='single quoted'
"""
    env_file.write_text(content)
    return env_file

class TestSetupEnvironment:
    def test_load_env_file(self, temp_env_file, tmp_path):
        """Test that environment variables are loaded from .env file."""
        # Clear any existing env vars
        for key in ["TEST_STRING", "TEST_INT", "TEST_FLOAT", "TEST_BOOL"]:
            os.environ.pop(key, None)
        
        setup_environment(temp_env_file)
        
        assert os.environ.get("TEST_STRING") == "hello world"
        assert os.environ.get("TEST_INT") == "42"
        assert os.environ.get("TEST_FLOAT") == "3.14"
        assert os.environ.get("TEST_BOOL") == "true"

    def test_missing_env_file(self, tmp_path, caplog):
        """Test behavior when .env file is missing."""
        missing_path = tmp_path / "nonexistent.env"
        setup_environment(missing_path)
        
        assert "not found" in caplog.text

    def test_comments_and_empty_lines(self, tmp_path):
        """Test that comments and empty lines are ignored."""
        env_file = tmp_path / ".env"
        content = """
# This is a comment
VALID_VAR=value

# Another comment
ANOTHER_VAR=another value
"""
        env_file.write_text(content)
        
        # Clear existing
        os.environ.pop("VALID_VAR", None)
        os.environ.pop("ANOTHER_VAR", None)
        
        setup_environment(env_file)
        
        assert os.environ.get("VALID_VAR") == "value"
        assert os.environ.get("ANOTHER_VAR") == "another value"

class TestGetEnvValue:
    def test_get_existing_value(self):
        """Test getting an existing environment variable."""
        os.environ["TEST_VAR"] = "test_value"
        result = get_env_value("TEST_VAR")
        assert result == "test_value"
        os.environ.pop("TEST_VAR")

    def test_get_default_value(self):
        """Test getting default value when key is missing."""
        result = get_env_value("MISSING_VAR", default="default_value")
        assert result == "default_value"

    def test_required_missing_raises(self):
        """Test that required=True raises ValueError when missing."""
        with pytest.raises(ValueError, match="Required environment variable"):
            get_env_value("MISSING_VAR", required=True)

    def test_required_present_no_error(self):
        """Test that required=True doesn't raise when present."""
        os.environ["TEST_VAR"] = "value"
        result = get_env_value("TEST_VAR", required=True)
        assert result == "value"
        os.environ.pop("TEST_VAR")

class TestGetEnvInt:
    def test_valid_int(self):
        """Test getting a valid integer."""
        os.environ["TEST_INT"] = "42"
        result = get_env_int("TEST_INT")
        assert result == 42
        os.environ.pop("TEST_INT")

    def test_invalid_int_raises(self):
        """Test that non-integer value raises ValueError."""
        os.environ["TEST_INT"] = "not_a_number"
        with pytest.raises(ValueError, match="must be an integer"):
            get_env_int("TEST_INT")
        os.environ.pop("TEST_INT")

    def test_default_value(self):
        """Test getting default integer value."""
        result = get_env_int("MISSING_INT", default=10)
        assert result == 10

class TestGetEnvFloat:
    def test_valid_float(self):
        """Test getting a valid float."""
        os.environ["TEST_FLOAT"] = "3.14"
        result = get_env_float("TEST_FLOAT")
        assert result == pytest.approx(3.14)
        os.environ.pop("TEST_FLOAT")

    def test_invalid_float_raises(self):
        """Test that non-float value raises ValueError."""
        os.environ["TEST_FLOAT"] = "not_a_float"
        with pytest.raises(ValueError, match="must be a float"):
            get_env_float("TEST_FLOAT")
        os.environ.pop("TEST_FLOAT")

class TestGetEnvBool:
    def test_true_values(self):
        """Test various true value representations."""
        true_values = ["true", "1", "yes", "on", "TRUE", "True"]
        for val in true_values:
            os.environ["TEST_BOOL"] = val
            result = get_env_bool("TEST_BOOL")
            assert result is True
            os.environ.pop("TEST_BOOL")

    def test_false_values(self):
        """Test various false value representations."""
        false_values = ["false", "0", "no", "off", "FALSE", "False"]
        for val in false_values:
            os.environ["TEST_BOOL"] = val
            result = get_env_bool("TEST_BOOL")
            assert result is False
            os.environ.pop("TEST_BOOL")

    def test_invalid_bool_raises(self):
        """Test that invalid boolean value raises ValueError."""
        os.environ["TEST_BOOL"] = "maybe"
        with pytest.raises(ValueError, match="must be a boolean"):
            get_env_bool("TEST_BOOL")
        os.environ.pop("TEST_BOOL")

class TestValidateRequiredEnvVars:
    def test_all_present(self):
        """Test validation when all variables are present."""
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "value2"
        
        result = validate_required_env_vars(["VAR1", "VAR2"])
        
        assert result["valid"] is True
        assert result["missing"] == []
        
        os.environ.pop("VAR1")
        os.environ.pop("VAR2")

    def test_some_missing_raises(self):
        """Test that validation raises when variables are missing."""
        os.environ["VAR1"] = "value1"
        
        with pytest.raises(ValueError, match="Missing required environment variables"):
            validate_required_env_vars(["VAR1", "VAR2", "VAR3"])
        
        os.environ.pop("VAR1")

class TestGetEnvConfig:
    def test_returns_dict(self):
        """Test that get_env_config returns a dictionary with expected structure."""
        # Set some environment variables
        os.environ["DATA_DIR"] = "custom_data"
        os.environ["RANDOM_SEED"] = "123"
        os.environ["MAX_MEMORY_GB"] = "10"
        
        config = get_env_config()
        
        assert isinstance(config, dict)
        assert "paths" in config
        assert "seeds" in config
        assert config["paths"]["data_dir"] == "custom_data"
        assert config["seeds"]["random_seed"] == 123
        assert config["limits"]["max_memory_gb"] == 10
        
        # Cleanup
        os.environ.pop("DATA_DIR")
        os.environ.pop("RANDOM_SEED")
        os.environ.pop("MAX_MEMORY_GB")