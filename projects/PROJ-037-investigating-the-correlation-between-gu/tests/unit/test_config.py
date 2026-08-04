import pytest
from code.config import Config, get_config, reset_config
from code.utils.config import Config as UtilsConfig, get_config as utils_get_config

class TestConfig:
    def test_config_singleton(self):
        """Test that Config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_config_reset(self):
        """Test that reset_config creates a new instance."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2

    def test_config_default_values(self):
        """Test that Config has expected default values."""
        config = get_config()
        # Check for expected attributes based on typical config structure
        assert hasattr(config, 'project_root')
        assert hasattr(config, 'data_dir')
        assert hasattr(config, 'output_dir')

    def test_config_data_dirs(self):
        """Test that config contains correct directory paths."""
        config = get_config()
        assert 'data/raw' in str(config.data_dir) or 'data/raw' in config.data_dir
        assert 'data/processed' in str(config.data_dir) or 'data/processed' in config.data_dir
        assert 'data/outputs' in str(config.output_dir) or 'data/outputs' in config.output_dir

class TestUtilsConfig:
    def test_utils_config_singleton(self):
        """Test that UtilsConfig returns the same instance."""
        config1 = utils_get_config()
        config2 = utils_get_config()
        assert config1 is config2

    def test_utils_config_attributes(self):
        """Test that UtilsConfig has expected attributes."""
        config = utils_get_config()
        assert hasattr(config, 'project_root')
        assert hasattr(config, 'data_dir')
        assert hasattr(config, 'output_dir')