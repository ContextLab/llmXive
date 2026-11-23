"""
Unit tests for the config_loader module.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the module to test
from code.config_loader import load, get_config_value, DEFAULTS


class TestConfigLoader:
    """Tests for the config_loader module."""

    def test_load_missing_file_uses_defaults(self, caplog):
        """Test that loading a missing .env file returns defaults and logs a warning."""
        # Use a path that definitely doesn't exist
        result = load(env_path="/nonexistent/path/.env")
        
        assert isinstance(result, dict)
        assert result["LOG_LEVEL"] == "INFO"
        assert "not found" in caplog.text or "warning" in caplog.text.lower()

    def test_load_existing_file(self):
        """Test that loading an existing .env file works correctly."""
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_VAR=test_value\n")
            f.write("LOG_LEVEL=DEBUG\n")
            temp_path = f.name

        try:
            # Clear os.environ for the specific key to ensure we get the file value
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]
            if "LOG_LEVEL" in os.environ:
                del os.environ["LOG_LEVEL"]

            result = load(env_path=temp_path)
            
            assert result["TEST_VAR"] == "test_value"
            assert result["LOG_LEVEL"] == "DEBUG"
        finally:
            os.unlink(temp_path)

    def test_env_var_overrides_file(self):
        """Test that environment variables override .env file values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("LOG_LEVEL=DEBUG\n")
            temp_path = f.name

        try:
            # Set an env var
            os.environ["LOG_LEVEL"] = "WARNING"
            
            result = load(env_path=temp_path)
            
            # Env var should take precedence
            assert result["LOG_LEVEL"] == "WARNING"
        finally:
            os.unlink(temp_path)
            if "LOG_LEVEL" in os.environ:
                del os.environ["LOG_LEVEL"]

    def test_get_config_value(self):
        """Test retrieving a specific config value."""
        # Ensure defaults are loaded
        load()
        
        # Test getting a default value
        level = get_config_value("LOG_LEVEL")
        assert level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        # Test getting a non-existent key with default
        custom = get_config_value("NON_EXISTENT_KEY", "my_default")
        assert custom == "my_default"

    def test_load_returns_string_values(self):
        """Test that all returned values are strings."""
        result = load(env_path="/nonexistent")
        for key, value in result.items():
            assert isinstance(value, str), f"Value for {key} is not a string: {type(value)}"
