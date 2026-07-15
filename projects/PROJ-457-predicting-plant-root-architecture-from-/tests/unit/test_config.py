"""
Unit tests for the configuration module.
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import (
    load_config,
    get_config,
    get_seed,
    get_data_path,
    get_output_path,
    get_figures_path,
    get_reports_path,
    get_models_path,
    setup_logging,
    get_logger,
    DEFAULT_CONFIG,
    CONFIG_PATH,
    PROJECT_ROOT
)


class TestConfigLoading:
    """Tests for configuration loading functionality."""
    
    def test_load_config_returns_dict(self):
        """Test that load_config returns a dictionary."""
        config = load_config()
        assert isinstance(config, dict)
    
    def test_load_config_contains_required_keys(self):
        """Test that config contains all required keys."""
        config = load_config()
        required_keys = [
            "DATA_PATH", "SEED", "LOG_LEVEL", 
            "FIGURES_PATH", "REPORTS_PATH", "MODELS_PATH"
        ]
        for key in required_keys:
            assert key in config, f"Missing required key: {key}"
    
    def test_get_config_retrieves_value(self):
        """Test that get_config retrieves the correct value."""
        config = load_config()
        assert get_config("SEED") == config["SEED"]
    
    def test_get_config_returns_default(self):
        """Test that get_config returns default for missing key."""
        assert get_config("NON_EXISTENT_KEY", "default_value") == "default_value"
    
    def test_get_seed_returns_int(self):
        """Test that get_seed returns an integer."""
        seed = get_seed()
        assert isinstance(seed, int)
    
    def test_get_seed_returns_config_value(self):
        """Test that get_seed returns the value from config."""
        config = load_config()
        assert get_seed() == config["SEED"]
    
    def test_path_functions_return_path_objects(self):
        """Test that path getter functions return Path objects."""
        assert isinstance(get_data_path(), Path)
        assert isinstance(get_output_path(), Path)
        assert isinstance(get_figures_path(), Path)
        assert isinstance(get_reports_path(), Path)
        assert isinstance(get_models_path(), Path)
    
    def test_paths_are_absolute(self):
        """Test that path functions return absolute paths."""
        assert get_data_path().is_absolute()
        assert get_output_path().is_absolute()
        assert get_figures_path().is_absolute()
        assert get_reports_path().is_absolute()
        assert get_models_path().is_absolute()


class TestLogging:
    """Tests for logging functionality."""
    
    def test_setup_logging_returns_logger(self):
        """Test that setup_logging returns a logger instance."""
        logger = setup_logging()
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
    
    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns the same logger instance."""
        logger1 = setup_logging()
        logger2 = get_logger()
        assert logger1 is logger2
    
    def test_logger_has_handlers(self):
        """Test that logger has file and console handlers."""
        logger = setup_logging()
        assert len(logger.handlers) >= 2  # File and console handlers
    
    def test_log_level_is_respected(self):
        """Test that the configured log level is respected."""
        logger = setup_logging()
        # The logger level should match the config
        assert logger.level == setup_logging().level


class TestConfigWithCustomFile:
    """Tests using a custom config file."""
    
    def test_custom_config_overrides_defaults(self, tmp_path):
        """Test that custom config file overrides default values."""
        # Create a temporary config file
        custom_config = {
            "SEED": 123,
            "LOG_LEVEL": "DEBUG",
            "DATA_PATH": str(tmp_path / "custom_data")
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(custom_config, f)
        
        # Temporarily override CONFIG_PATH
        import config
        original_config_path = config.CONFIG_PATH
        config.CONFIG_PATH = config_file
        
        try:
            # Reset cached config
            config._config = None
            
            loaded_config = load_config()
            assert loaded_config["SEED"] == 123
            assert loaded_config["LOG_LEVEL"] == "DEBUG"
            assert loaded_config["DATA_PATH"] == str(tmp_path / "custom_data")
        finally:
            # Restore original config path
            config.CONFIG_PATH = original_config_path
            config._config = None
