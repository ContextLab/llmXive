"""
Unit tests for the config_manager module.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
from code.utils import config_manager
from code.utils.config_manager import ConfigError, get_api_key, validate_environment


class TestGetApiKey:
    def test_get_api_key_success(self, tmp_path):
        """Test retrieving an existing API key."""
        env_file = tmp_path / ".env"
        env_file.write_text("MATERIALS_PROJECT_API_KEY=test_key_123\n")

        with patch.object(config_manager, 'load_dotenv_file', return_value=True):
            with patch.dict(os.environ, {}, clear=True):
                # Simulate loading the env file into os.environ
                os.environ["MATERIALS_PROJECT_API_KEY"] = "test_key_123"

                key = config_manager.get_api_key("MATERIALS_PROJECT")
                assert key == "test_key_123"

    def test_get_api_key_missing(self, tmp_path):
        """Test that ConfigError is raised when key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure the variable is not set
            if "MATERIALS_PROJECT_API_KEY" in os.environ:
                del os.environ["MATERIALS_PROJECT_API_KEY"]

            with pytest.raises(ConfigError) as exc_info:
                config_manager.get_api_key("MATERIALS_PROJECT")

            assert "not found" in str(exc_info.value).lower()

    def test_get_api_key_unknown_service(self):
        """Test that ConfigError is raised for unknown service."""
        with pytest.raises(ConfigError) as exc_info:
            config_manager.get_api_key("UNKNOWN_SERVICE")

        assert "Unknown service" in str(exc_info.value)


class TestValidateEnvironment:
    def test_validate_environment_all_present(self):
        """Test validation when all required keys are present."""
        os.environ["MATERIALS_PROJECT_API_KEY"] = "fake_key"

        results = config_manager.validate_environment(["MATERIALS_PROJECT"])
        assert results["MATERIALS_PROJECT"] is True

    def test_validate_environment_missing(self):
        """Test validation when a required key is missing."""
        if "MATERIALS_PROJECT_API_KEY" in os.environ:
            del os.environ["MATERIALS_PROJECT_API_KEY"]

        results = config_manager.validate_environment(["MATERIALS_PROJECT"])
        assert results["MATERIALS_PROJECT"] is False
