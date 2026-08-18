import os
import pytest
from pathlib import Path
import tempfile
import json

from utils.config import ConfigManager, get_config


class TestConfigManager:
    """Unit tests for the ConfigManager class."""

    @pytest.fixture
    def temp_env_file(self, tmp_path):
        """Create a temporary .env file for testing."""
        env_content = """
        TEST_VAR=test_value
        DATA_PATH_RAW=test/raw
        API_KEY_TEST=secret123
        DEBUG_MODE=True
        """
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)
        return env_file

    @pytest.fixture
    def config_manager(self, temp_env_file):
        """Create a ConfigManager instance with test env file."""
        return ConfigManager(env_file=temp_env_file)

    def test_env_loading(self, config_manager):
        """Test that environment variables are loaded from .env file."""
        assert config_manager.get("TEST_VAR") == "test_value"
        assert config_manager.get("DATA_PATH_RAW") == "test/raw"
        assert config_manager.get("API_KEY_TEST") == "secret123"
        assert config_manager.get("DEBUG_MODE") is True

    def test_default_values(self, temp_env_file):
        """Test that default values are set when not in .env."""
        config = ConfigManager(env_file=temp_env_file)
        assert config.get("DATA_PATH_PROCESSED") == "data/processed"
        assert config.get("RANDOM_SEED") == 42
        assert config.get("FIGURES_PATH") == "data/results/plots"

    def test_get_path_relative(self, config_manager):
        """Test that relative paths are resolved correctly."""
        path = config_manager.get_path("DATA_PATH_RAW")
        assert isinstance(path, Path)
        assert path.is_absolute()
        assert "test" in str(path)

    def test_get_path_absolute(self, temp_env_file):
        """Test that absolute paths are preserved."""
        # Create env file with absolute path
        abs_env = temp_env_file.parent / "abs.env"
        abs_env.write_text(f"ABS_PATH={temp_env_file.parent}/absolute")
        config = ConfigManager(env_file=abs_env)
        path = config.get_path("ABS_PATH")
        assert path.is_absolute()
        assert str(path).endswith("absolute")

    def test_ensure_dirs(self, temp_env_file):
        """Test that ensure_dirs creates the required directories."""
        config = ConfigManager(env_file=temp_env_file)
        # Override paths to use temp directory
        config._config["DATA_PATH_RAW"] = str(temp_env_file.parent / "new_raw")
        config._config["DATA_PATH_PROCESSED"] = str(temp_env_file.parent / "new_processed")
        
        config.ensure_dirs()
        
        assert (temp_env_file.parent / "new_raw").exists()
        assert (temp_env_file.parent / "new_processed").exists()

    def test_validate_api_keys(self, temp_env_file):
        """Test API key validation logic."""
        config = ConfigManager(env_file=temp_env_file)
        validation = config.validate_api_keys()
        
        # API_KEY_OPENML and API_KEY_HF should be False (not set in test env)
        assert validation.get("API_KEY_OPENML") is False
        assert validation.get("API_KEY_HF") is False

    def test_to_dict(self, config_manager):
        """Test that to_dict returns a complete configuration dictionary."""
        config_dict = config_manager.to_dict()
        
        assert "project_root" in config_dict
        assert "data_raw" in config_dict
        assert "data_processed" in config_dict
        assert "api_keys_valid" in config_dict
        assert isinstance(config_dict["api_keys_valid"], dict)

    def test_save_config(self, temp_env_file, tmp_path):
        """Test that save_config writes a valid JSON file."""
        config = ConfigManager(env_file=temp_env_file)
        output_path = tmp_path / "config.json"
        
        saved_path = config.save_config(output_path)
        
        assert saved_path.exists()
        with open(saved_path, "r") as f:
            data = json.load(f)
        
        assert "project_root" in data
        assert "data_raw" in data

    def test_get_config_factory(self, temp_env_file):
        """Test the get_config factory function."""
        config = get_config(env_file=temp_env_file)
        assert isinstance(config, ConfigManager)
        assert config.get("TEST_VAR") == "test_value"

    def test_missing_required_path(self, temp_env_file):
        """Test that get_path raises error for missing key."""
        config = ConfigManager(env_file=temp_env_file)
        with pytest.raises(ValueError, match="Path configuration.*is not set"):
            config.get_path("NON_EXISTENT_KEY")

    def test_type_conversion(self, temp_env_file):
        """Test automatic type conversion for common types."""
        config = ConfigManager(env_file=temp_env_file)
        
        # Boolean conversion
        assert config.get("DEBUG_MODE") is True
        
        # Integer conversion (default)
        assert config.get("RANDOM_SEED") == 42
        
        # String conversion (when not convertible)
        assert config.get("TEST_VAR") == "test_value"
