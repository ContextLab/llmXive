"""
Tests for environment configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest
from code.utils.env_config import (
    load_environment,
    validate_adni_credentials,
    get_config,
    check_env,
    REQUIRED_ENV_KEYS,
    OPTIONAL_ENV_KEYS
)


class TestEnvConfig:
    """Test suite for environment configuration functions."""

    def test_load_environment_with_valid_file(self):
        """Test loading environment from a valid .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("ADNI_USERNAME=test_user\n")
            f.write("ADNI_PASSWORD=test_pass\n")
            f.write("ADNI_PROJECT_ID=test_project\n")
            f.write("LONI_IDGK_URL=https://test.loni.usc.edu\n")
            env_path = Path(f.name)

        try:
            result = load_environment(env_path)
            assert result is True
            assert os.getenv("ADNI_USERNAME") == "test_user"
            assert os.getenv("ADNI_PASSWORD") == "test_pass"
        finally:
            env_path.unlink()

    def test_load_environment_missing_file(self):
        """Test loading environment when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_environment(Path("/nonexistent/.env"))

    def test_validate_adni_credentials_missing_keys(self):
        """Test validation fails when required keys are missing."""
        # Clear all required keys
        for key in REQUIRED_ENV_KEYS:
            os.environ.pop(key, None)

        with pytest.raises(ValueError) as excinfo:
            validate_adni_credentials()

        assert "Missing required ADNI environment variables" in str(excinfo.value)

    def test_validate_adni_credentials_empty_keys(self):
        """Test validation fails when required keys are empty."""
        # Set all required keys to empty
        for key in REQUIRED_ENV_KEYS:
            os.environ[key] = ""

        with pytest.raises(ValueError) as excinfo:
            validate_adni_credentials()

        assert "Empty ADNI environment variables" in str(excinfo.value)

    def test_validate_adni_credentials_valid(self):
        """Test validation passes when all required keys are present and non-empty."""
        # Set valid values for all required keys
        for key in REQUIRED_ENV_KEYS:
            os.environ[key] = "test_value"

        try:
            result = validate_adni_credentials()
            assert result is True
        finally:
            # Clean up
            for key in REQUIRED_ENV_KEYS:
                os.environ.pop(key, None)

    def test_get_config(self):
        """Test retrieving configuration values."""
        # Set valid values
        for key in REQUIRED_ENV_KEYS:
            os.environ[key] = "test_value"
        os.environ["ADNI_DATA_DIR"] = "/custom/path"

        try:
            config = get_config()
            
            # Check required keys
            for key in REQUIRED_ENV_KEYS:
                assert key in config
                assert config[key] == "test_value"
            
            # Check optional key with custom value
            assert config["ADNI_DATA_DIR"] == "/custom/path"
            
            # Check optional key with default value
            assert config["LOG_LEVEL"] == "INFO"
        finally:
            # Clean up
            for key in REQUIRED_ENV_KEYS:
                os.environ.pop(key, None)
            os.environ.pop("ADNI_DATA_DIR", None)

    def test_check_env_missing_keys(self):
        """Test check_env when required keys are missing."""
        # Clear all required keys
        for key in REQUIRED_ENV_KEYS:
            os.environ.pop(key, None)

        result = check_env()

        assert result["valid"] is False
        assert len(result["missing"]) == len(REQUIRED_ENV_KEYS)
        assert len(result["empty"]) == 0

    def test_check_env_empty_keys(self):
        """Test check_env when required keys are empty."""
        # Set all required keys to empty
        for key in REQUIRED_ENV_KEYS:
            os.environ[key] = ""

        try:
            result = check_env()

            assert result["valid"] is False
            assert len(result["missing"]) == 0
            assert len(result["empty"]) == len(REQUIRED_ENV_KEYS)
        finally:
            # Clean up
            for key in REQUIRED_ENV_KEYS:
                os.environ.pop(key, None)

    def test_check_env_valid(self):
        """Test check_env when all required keys are present."""
        # Set valid values
        for key in REQUIRED_ENV_KEYS:
            os.environ[key] = "test_value"

        try:
            result = check_env()

            assert result["valid"] is True
            assert len(result["missing"]) == 0
            assert len(result["empty"]) == 0
            assert len(result["loaded_keys"]) >= len(REQUIRED_ENV_KEYS)
        finally:
            # Clean up
            for key in REQUIRED_ENV_KEYS:
                os.environ.pop(key, None)
