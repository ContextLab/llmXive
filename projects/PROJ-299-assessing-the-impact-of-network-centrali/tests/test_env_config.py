import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config.env_config import (
    load_environment,
    validate_adni_credentials,
    get_config,
    check_env,
    REQUIRED_ADNI_KEYS,
    ENV_FILE_PATH
)

class TestLoadEnvironment:
    def test_load_environment_success(self, tmp_path):
        """Test that load_environment returns True when .env exists."""
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\n")
        
        with patch("config.env_config.ENV_FILE_PATH", env_file):
            with patch("config.env_config.load_dotenv") as mock_load:
                result = load_environment()
                assert result is True
                mock_load.assert_called_once()

    def test_load_environment_missing(self, tmp_path):
        """Test that load_environment returns False when .env is missing."""
        missing_env = tmp_path / "nonexistent.env"
        
        with patch("config.env_config.ENV_FILE_PATH", missing_env):
            with patch("config.env_config.load_dotenv") as mock_load:
                result = load_environment()
                assert result is False
                mock_load.assert_not_called()

class TestValidateAdniCredentials:
    def test_validate_missing_keys(self):
        """Test validation fails when required keys are missing."""
        # Ensure keys are not set in the current process env for this test
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as excinfo:
                validate_adni_credentials()
            
            assert "Missing required ADNI environment variables" in str(excinfo.value)
            for key in REQUIRED_ADNI_KEYS:
                assert key in str(excinfo.value)

    def test_validate_empty_keys(self):
        """Test validation fails when keys are present but empty."""
        env_vars = {key: "" for key in REQUIRED_ADNI_KEYS}
        
        with patch.dict(os.environ, env_vars, clear=False):
            with pytest.raises(ValueError) as excinfo:
                validate_adni_credentials()
            
            assert "Missing required ADNI environment variables" in str(excinfo.value)

    def test_validate_success(self):
        """Test validation succeeds when all keys are present and non-empty."""
        env_vars = {key: "valid_value" for key in REQUIRED_ADNI_KEYS}
        
        with patch.dict(os.environ, env_vars, clear=False):
            result = validate_adni_credentials()
            
            assert result["valid"] is True
            assert result["missing"] == []
            assert len(result["values"]) == len(REQUIRED_ADNI_KEYS)
            # Check masking logic
            for val in result["values"].values():
                assert "****" in val or "***" in val

class TestGetConfig:
    def test_get_config_existing(self):
        """Test retrieving an existing config value."""
        with patch.dict(os.environ, {"TEST_KEY": "test_value"}):
            assert get_config("TEST_KEY") == "test_value"

    def test_get_config_missing_default(self):
        """Test retrieving a missing config value with default."""
        assert get_config("NON_EXISTENT_KEY", "default_fallback") == "default_fallback"

    def test_get_config_missing_no_default(self):
        """Test retrieving a missing config value without default."""
        assert get_config("NON_EXISTENT_KEY") is None

class TestCheckEnv:
    def test_check_env_success(self):
        """Test check_env passes when environment is valid."""
        env_vars = {key: "valid_value" for key in REQUIRED_ADNI_KEYS}
        
        with patch.dict(os.environ, env_vars, clear=False):
            # Should not raise
            check_env()

    def test_check_env_failure(self):
        """Test check_env raises ValueError when environment is invalid."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                check_env()
