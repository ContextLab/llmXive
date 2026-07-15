"""
Unit tests for configuration management (T008).

Tests verify that:
1. Configuration loads from .env file
2. Default values are used when environment variables are not set
3. Configuration values are correctly parsed (int, float, list, path)
4. Logging is properly configured
5. Sample .env file is created if it doesn't exist
"""
import os
import tempfile
import logging
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import Config, get_config, reset_config, DEFAULTS, PROJECT_ROOT


class TestConfigInitialization:
    """Tests for Config class initialization."""

    def test_create_sample_env_when_missing(self, tmp_path):
        """Test that a sample .env file is created when it doesn't exist."""
        # Create a temporary directory for testing
        test_env_path = tmp_path / ".env"
        
        # Create config with non-existent env path
        config = Config(test_env_path)
        
        # Verify the file was created
        assert test_env_path.exists()
        
        # Verify the file contains expected content
        content = test_env_path.read_text()
        assert "SEED=" in content
        assert "DATA_RAW_DIR=" in content
        assert "LOG_LEVEL=" in content

    def test_loads_from_existing_env(self, tmp_path):
        """Test that config loads from an existing .env file."""
        test_env_path = tmp_path / ".env"
        test_env_path.write_text("SEED=123\nLOG_LEVEL=DEBUG\n")
        
        config = Config(test_env_path)
        
        assert config.get("SEED") == 123
        assert config.get("LOG_LEVEL") == "DEBUG"

    def test_uses_defaults_when_env_missing(self):
        """Test that default values are used when environment variables are not set."""
        # Clear any existing env vars for tested keys
        for key in DEFAULTS.keys():
            os.environ.pop(key, None)
        
        # Create a temporary env file to avoid creation during test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("# Empty config\n")
            temp_env_path = Path(f.name)
        
        try:
            config = Config(temp_env_path)
            
            for key, default_value in DEFAULTS.items():
                assert config.get(key) == default_value
        finally:
            temp_env_path.unlink()


class TestConfigGetters:
    """Tests for configuration getter methods."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()
        # Create a temporary env file
        self.temp_env = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
        self.temp_env.write("SEED=42\nDATA_RAW_DIR=test/data\nLATTICE_SIZES=16,24,32\n")
        self.temp_env.close()

    def teardown_method(self):
        """Clean up after each test."""
        Path(self.temp_env.name).unlink()
        reset_config()

    def test_get_int(self):
        """Test integer value retrieval."""
        config = Config(Path(self.temp_env.name))
        assert config.get_int("SEED") == 42
        assert config.get_int("NONEXISTENT", 999) == 999

    def test_get_float(self):
        """Test float value retrieval."""
        config = Config(Path(self.temp_env.name))
        # Add a float value to test
        with open(self.temp_env.name, 'a') as f:
            f.write("TEMP_START=0.5\n")
        
        config = Config(Path(self.temp_env.name))
        assert config.get_float("TEMP_START") == 0.5
        assert config.get_float("NONEXISTENT", 1.5) == 1.5

    def test_get_list(self):
        """Test list value retrieval."""
        config = Config(Path(self.temp_env.name))
        assert config.get_list("LATTICE_SIZES") == ["16", "24", "32"]
        assert config.get_list("NONEXISTENT", ["default"]) == ["default"]

    def test_get_path(self):
        """Test path value retrieval."""
        config = Config(Path(self.temp_env.name))
        data_path = config.get_path("DATA_RAW_DIR")
        assert isinstance(data_path, Path)
        assert data_path.name == "test"
        assert data_path.parent.name == "data"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = Config(Path(self.temp_env.name))
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "SEED" in config_dict
        assert config_dict["SEED"] == 42


class TestLoggingSetup:
    """Tests for logging configuration."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()
        self.temp_env = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
        self.temp_env.write("LOG_LEVEL=WARNING\nLOG_FILE=test_logs/test.log\n")
        self.temp_env.close()

    def teardown_method(self):
        """Clean up after each test."""
        Path(self.temp_env.name).unlink()
        reset_config()
        # Clean up test log directory
        test_log_dir = Path(self.temp_env.name).parent / "test_logs"
        if test_log_dir.exists():
            import shutil
            shutil.rmtree(test_log_dir, ignore_errors=True)

    def test_logging_configured_correctly(self):
        """Test that logging is configured with correct level and handlers."""
        config = Config(Path(self.temp_env.name))
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING
        
        # Check that handlers are configured
        assert len(root_logger.handlers) > 0
        
        # Check for file handler
        file_handler_exists = any(
            isinstance(handler, logging.FileHandler) 
            for handler in root_logger.handlers
        )
        assert file_handler_exists


class TestGlobalConfig:
    """Tests for global config functions."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()
        self.temp_env = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
        self.temp_env.write("SEED=999\n")
        self.temp_env.close()

    def teardown_method(self):
        """Clean up after each test."""
        Path(self.temp_env.name).unlink()
        reset_config()

    def test_get_config_creates_instance(self):
        """Test that get_config creates a new instance when none exists."""
        config = get_config(Path(self.temp_env.name))
        assert config is not None
        assert config.get("SEED") == 999

    def test_get_config_returns_same_instance(self):
        """Test that get_config returns the same instance on subsequent calls."""
        config1 = get_config(Path(self.temp_env.name))
        config2 = get_config(Path(self.temp_env.name))
        assert config1 is config2

    def test_reset_config_clears_instance(self):
        """Test that reset_config clears the global instance."""
        get_config(Path(self.temp_env.name))
        reset_config()
        
        # Next call should create a new instance
        new_config = get_config(Path(self.temp_env.name))
        assert new_config is not None
        assert new_config.get("SEED") == 999