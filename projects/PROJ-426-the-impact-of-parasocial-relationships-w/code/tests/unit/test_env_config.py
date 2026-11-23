"""
Unit tests for environment configuration management.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure src is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.env_config import (
    EnvConfig, EnvConfigError, init_env_config, get_env_config,
    setup_environment_from_file, validate_and_setup_environment
)

class TestEnvConfigInitialization:
    """Tests for EnvConfig class initialization."""

    def test_init_creates_directories(self, tmp_path):
        """Test that initialization creates required directories."""
        # Create a temporary .env file
        env_content = f"""
        DATA_ROOT_DIR={tmp_path}/data
        DATA_RAW_DIR={tmp_path}/data/raw
        DATA_PROCESSED_DIR={tmp_path}/data/processed
        DATA_RESULTS_DIR={tmp_path}/data/results
        DATA_VALIDATION_DIR={tmp_path}/data/validation
        DATA_LEXICONS_DIR={tmp_path}/data/lexicons
        """
        env_file = tmp_path / "test.env"
        env_file.write_text(env_content)

        # Initialize config
        config = EnvConfig(env_file)

        # Verify directories were created
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data/raw").exists()
        assert (tmp_path / "data/processed").exists()
        assert (tmp_path / "data/results").exists()
        assert (tmp_path / "data/validation").exists()
        assert (tmp_path / "data/lexicons").exists()

    def test_init_missing_required_vars_raises_error(self, tmp_path):
        """Test that missing required variables raise an error."""
        env_file = tmp_path / "test.env"
        env_file.write_text("DATA_ROOT_DIR=/some/path\n") # Missing others

        with pytest.raises(EnvConfigError, match="Missing required environment variables"):
            EnvConfig(env_file)

    def test_init_creates_missing_directories(self, tmp_path):
        """Test that missing directories are created automatically."""
        env_content = f"""
        DATA_ROOT_DIR={tmp_path}/data
        DATA_RAW_DIR={tmp_path}/data/raw
        DATA_PROCESSED_DIR={tmp_path}/data/processed
        DATA_RESULTS_DIR={tmp_path}/data/results
        DATA_VALIDATION_DIR={tmp_path}/data/validation
        DATA_LEXICONS_DIR={tmp_path}/data/lexicons
        """
        env_file = tmp_path / "test.env"
        env_file.write_text(env_content)

        # Only create root, let config create the rest
        (tmp_path / "data").mkdir()

        config = EnvConfig(env_file)

        # Verify subdirectories were created
        assert (tmp_path / "data/raw").exists()

class TestEnvConfigMethods:
    """Tests for EnvConfig instance methods."""

    @pytest.fixture
    def valid_env_file(self, tmp_path):
        """Fixture providing a valid .env file."""
        env_content = f"""
        DATA_ROOT_DIR={tmp_path}/data
        DATA_RAW_DIR={tmp_path}/data/raw
        DATA_PROCESSED_DIR={tmp_path}/data/processed
        DATA_RESULTS_DIR={tmp_path}/data/results
        DATA_VALIDATION_DIR={tmp_path}/data/validation
        DATA_LEXICONS_DIR={tmp_path}/data/lexicons
        TEST_API_KEY=secret123
        """
        env_file = tmp_path / "test.env"
        env_file.write_text(env_content)
        return env_file

    def test_get_path(self, valid_env_file):
        """Test get_path method returns Path object."""
        config = EnvConfig(valid_env_file)
        path = config.get_path("DATA_ROOT_DIR")
        assert isinstance(path, Path)
        assert "data" in str(path)

    def test_get_path_missing_required(self, valid_env_file):
        """Test get_path raises error for missing required var."""
        config = EnvConfig(valid_env_file)
        with pytest.raises(EnvConfigError, match="Required environment variable"):
            config.get_path("NON_EXISTENT_VAR")

    def test_get_path_with_default(self, valid_env_file):
        """Test get_path returns default if var missing and default provided."""
        config = EnvConfig(valid_env_file)
        path = config.get_path("NON_EXISTENT_VAR", default="/fallback/path")
        assert str(path) == "/fallback/path"

    def test_get_api_key(self, valid_env_file):
        """Test get_api_key returns the key."""
        config = EnvConfig(valid_env_file)
        key = config.get_api_key("TEST_API_KEY")
        assert key == "secret123"

    def test_get_api_key_missing_required(self, valid_env_file):
        """Test get_api_key raises error for missing required key."""
        config = EnvConfig(valid_env_file)
        with pytest.raises(EnvConfigError, match="Required API key"):
            config.get_api_key("MISSING_KEY", required=True)

    def test_get_api_key_not_required(self, valid_env_file):
        """Test get_api_key returns None for missing optional key."""
        config = EnvConfig(valid_env_file)
        key = config.get_api_key("MISSING_KEY", required=False)
        assert key is None

    def test_to_dict_excludes_sensitive(self, valid_env_file):
        """Test to_dict excludes sensitive keys."""
        config = EnvConfig(valid_env_file)
        config_dict = config.to_dict()

        assert "DATA_ROOT_DIR" in config_dict
        assert "TEST_API_KEY" not in config_dict

class TestSingletonPattern:
    """Tests for the singleton pattern in env_config module."""

    def test_init_env_config_creates_instance(self, tmp_path):
        """Test init_env_config creates and returns instance."""
        env_content = f"""
        DATA_ROOT_DIR={tmp_path}/data
        DATA_RAW_DIR={tmp_path}/data/raw
        DATA_PROCESSED_DIR={tmp_path}/data/processed
        DATA_RESULTS_DIR={tmp_path}/data/results
        DATA_VALIDATION_DIR={tmp_path}/data/validation
        DATA_LEXICONS_DIR={tmp_path}/data/lexicons
        """
        env_file = tmp_path / "test.env"
        env_file.write_text(env_content)

        # Reset singleton
        import src.utils.env_config as ec_module
        ec_module._env_config_instance = None

        config = init_env_config(env_file)
        assert isinstance(config, EnvConfig)

    def test_get_env_config_returns_same_instance(self, tmp_path):
        """Test get_env_config returns the same instance."""
        env_content = f"""
        DATA_ROOT_DIR={tmp_path}/data
        DATA_RAW_DIR={tmp_path}/data/raw
        DATA_PROCESSED_DIR={tmp_path}/data/processed
        DATA_RESULTS_DIR={tmp_path}/data/results
        DATA_VALIDATION_DIR={tmp_path}/data/validation
        DATA_LEXICONS_DIR={tmp_path}/data/lexicons
        """
        env_file = tmp_path / "test.env"
        env_file.write_text(env_content)

        import src.utils.env_config as ec_module
        ec_module._env_config_instance = None

        config1 = init_env_config(env_file)
        config2 = get_env_config()

        assert config1 is config2

    def test_get_env_config_raises_if_not_init(self):
        """Test get_env_config raises error if not initialized."""
        import src.utils.env_config as ec_module
        ec_module._env_config_instance = None

        with pytest.raises(EnvConfigError, match="Environment configuration not initialized"):
            get_env_config()

class TestValidationAndSetup:
    """Tests for validation and setup functions."""

    def test_validate_and_setup_environment(self, tmp_path):
        """Test validate_and_setup_environment returns correct structure."""
        env_content = f"""
        DATA_ROOT_DIR={tmp_path}/data
        DATA_RAW_DIR={tmp_path}/data/raw
        DATA_PROCESSED_DIR={tmp_path}/data/processed
        DATA_RESULTS_DIR={tmp_path}/data/results
        DATA_VALIDATION_DIR={tmp_path}/data/validation
        DATA_LEXICONS_DIR={tmp_path}/data/lexicons
        """
        env_file = tmp_path / "test.env"
        env_file.write_text(env_content)

        import src.utils.env_config as ec_module
        ec_module._env_config_instance = None

        setup_environment_from_file(env_file)
        result = validate_and_setup_environment()

        assert result["status"] == "SUCCESS"
        assert "paths" in result
        assert "api_keys_status" in result
        assert "dotenv_available" in result

        # Check paths exist in result
        assert "data_root" in result["paths"]
        assert "data_raw" in result["paths"]
        assert "data_processed" in result["paths"]
        assert "data_results" in result["paths"]
        assert "data_validation" in result["paths"]
        assert "data_lexicons" in result["paths"]

    def test_validate_with_missing_api_keys(self, tmp_path):
        """Test validation handles missing optional API keys."""
        env_content = f"""
        DATA_ROOT_DIR={tmp_path}/data
        DATA_RAW_DIR={tmp_path}/data/raw
        DATA_PROCESSED_DIR={tmp_path}/data/processed
        DATA_RESULTS_DIR={tmp_path}/data/results
        DATA_VALIDATION_DIR={tmp_path}/data/validation
        DATA_LEXICONS_DIR={tmp_path}/data/lexicons
        """
        env_file = tmp_path / "test.env"
        env_file.write_text(env_content)

        import src.utils.env_config as ec_module
        ec_module._env_config_instance = None

        setup_environment_from_file(env_file)
        result = validate_and_setup_environment()

        assert result["api_keys_status"]["PUSHSHIFT_API_KEY"] == "MISSING"
        assert result["api_keys_status"]["ZENODO_API_TOKEN"] == "MISSING"
