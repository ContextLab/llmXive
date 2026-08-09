import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

# Import the module under test
from code.utils.env_config import (
    load_environment,
    validate_adni_credentials,
    get_config,
    check_env,
    REQUIRED_ADNI_KEYS
)

class TestEnvConfig:
    """Tests for environment configuration management."""

    def test_load_environment_missing_file(self):
        """Test that load_environment raises FileNotFoundError for missing .env."""
        with pytest.raises(FileNotFoundError):
            load_environment(Path("/nonexistent/.env"))

    def test_load_environment_success(self):
        """Test successful loading of a valid .env file."""
        env_content = (
            "ADNI_USERNAME=test_user\n"
            "ADNI_PASSWORD=test_pass\n"
            "ADNI_PROJECT_ID=project_123\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            temp_path = Path(f.name)

        try:
            result = load_environment(temp_path)
            assert result is True  # dotenv returns True if file was found and loaded
            assert os.getenv("ADNI_USERNAME") == "test_user"
            assert os.getenv("ADNI_PASSWORD") == "test_pass"
            assert os.getenv("ADNI_PROJECT_ID") == "project_123"
        finally:
            # Cleanup
            os.unlink(temp_path)
            # Clear env vars for other tests
            for key in ["ADNI_USERNAME", "ADNI_PASSWORD", "ADNI_PROJECT_ID"]:
                if key in os.environ:
                    del os.environ[key]

    def test_validate_adni_credentials_missing(self):
        """Test that validation fails when required keys are missing."""
        # Ensure env vars are not set
        for key in REQUIRED_ADNI_KEYS:
            if key in os.environ:
                del os.environ[key]

        with pytest.raises(ValueError) as exc_info:
            validate_adni_credentials()
        
        assert "Missing or empty required ADNI credentials" in str(exc_info.value)
        for key in REQUIRED_ADNI_KEYS:
            assert key in str(exc_info.value)

    def test_validate_adni_credentials_success(self):
        """Test that validation succeeds when all required keys are present."""
        # Set mock credentials
        os.environ["ADNI_USERNAME"] = "test_user"
        os.environ["ADNI_PASSWORD"] = "test_pass"
        os.environ["ADNI_PROJECT_ID"] = "project_123"

        try:
            creds = validate_adni_credentials()
            assert creds["ADNI_USERNAME"] == "test_user"
            assert creds["ADNI_PASSWORD"] == "test_pass"
            assert creds["ADNI_PROJECT_ID"] == "project_123"
        finally:
            # Cleanup
            for key in REQUIRED_ADNI_KEYS:
                if key in os.environ:
                    del os.environ[key]

    def test_validate_adni_credentials_empty(self):
        """Test that validation fails when required keys are empty strings."""
        os.environ["ADNI_USERNAME"] = ""
        os.environ["ADNI_PASSWORD"] = "   "  # whitespace only
        os.environ["ADNI_PROJECT_ID"] = ""

        with pytest.raises(ValueError) as exc_info:
            validate_adni_credentials()
        
        assert "Missing or empty required ADNI credentials" in str(exc_info.value)

    def test_get_config_success(self):
        """Test that get_config returns the full configuration dictionary."""
        os.environ["ADNI_USERNAME"] = "test_user"
        os.environ["ADNI_PASSWORD"] = "test_pass"
        os.environ["ADNI_PROJECT_ID"] = "project_123"

        try:
            config = get_config()
            assert "adni" in config
            assert config["adni"]["ADNI_USERNAME"] == "test_user"
            assert "data_paths" in config
            assert "logging" in config
        finally:
            for key in REQUIRED_ADNI_KEYS:
                if key in os.environ:
                    del os.environ[key]

    def test_check_env_true(self):
        """Test that check_env returns True when credentials are valid."""
        os.environ["ADNI_USERNAME"] = "test_user"
        os.environ["ADNI_PASSWORD"] = "test_pass"
        os.environ["ADNI_PROJECT_ID"] = "project_123"

        try:
            assert check_env() is True
        finally:
            for key in REQUIRED_ADNI_KEYS:
                if key in os.environ:
                    del os.environ[key]

    def test_check_env_false(self):
        """Test that check_env returns False when credentials are missing."""
        # Ensure env vars are not set
        for key in REQUIRED_ADNI_KEYS:
            if key in os.environ:
                del os.environ[key]
        
        assert check_env() is False
