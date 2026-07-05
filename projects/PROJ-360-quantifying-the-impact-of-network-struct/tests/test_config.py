"""
Tests for environment configuration management.

These tests verify that:
1. Configuration singleton works correctly
2. API keys are loaded from environment
3. Random seeds are managed properly
4. Path configuration is correct
"""

import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from config import Config, get_config, reset_config, initialize_environment


class TestConfig:
    """Test suite for Config class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset configuration before each test
        reset_config()
        
        # Set test environment variables
        os.environ['MATERIALS_PROJECT_API_KEY'] = 'test_api_key_12345'
        os.environ['RANDOM_SEED'] = '42'

    def teardown_method(self):
        """Clean up after tests."""
        # Remove test environment variables
        os.environ.pop('MATERIALS_PROJECT_API_KEY', None)
        os.environ.pop('RANDOM_SEED', None)
        reset_config()

    def test_config_singleton(self):
        """Test that Config returns the same instance."""
        config1 = Config.get_instance()
        config2 = Config.get_instance()
        assert config1 is config2

    def test_get_config_function(self):
        """Test the get_config convenience function."""
        config = get_config()
        assert isinstance(config, Config)

    def test_api_key_loading(self):
        """Test that API keys are loaded from environment."""
        config = get_config()
        mp_key = config.get_api_key('materials_project')
        assert mp_key == 'test_api_key_12345'

    def test_missing_api_key(self):
        """Test behavior when API key is missing."""
        os.environ.pop('MATERIALS_PROJECT_API_KEY', None)
        reset_config()
        
        config = get_config()
        mp_key = config.get_api_key('materials_project')
        assert mp_key is None

    def test_random_seed_default(self):
        """Test default random seed value."""
        os.environ.pop('RANDOM_SEED', None)
        reset_config()
        
        config = get_config()
        assert config.get_random_seed() == 42

    def test_random_seed_custom(self):
        """Test custom random seed from environment."""
        os.environ['RANDOM_SEED'] = '12345'
        reset_config()
        
        config = get_config()
        assert config.get_random_seed() == 12345

    def test_set_random_seed(self):
        """Test setting random seed programmatically."""
        config = get_config()
        config.set_random_seed(999)
        assert config.get_random_seed() == 999

    def test_path_configuration(self):
        """Test that paths are configured correctly."""
        config = get_config()
        
        base_path = config.get_path('base')
        assert base_path is not None
        assert base_path.exists()

    def test_ensure_directories(self):
        """Test that ensure_directories creates required paths."""
        config = get_config()
        config.ensure_directories()
        
        # Verify key directories exist
        assert config.get_path('data_raw').exists()
        assert config.get_path('models').exists()
        assert config.get_path('results').exists()

    def test_to_dict_excludes_sensitive_data(self):
        """Test that to_dict() doesn't expose API keys."""
        config = get_config()
        config_dict = config.to_dict()
        
        # Check that API keys are not in the dictionary values
        dict_str = str(config_dict)
        assert 'test_api_key_12345' not in dict_str
        
        # But API key names should be present
        assert 'api_keys_configured' in config_dict

    def test_reset_config(self):
        """Test that reset_config() clears the singleton."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        # Should be different instances after reset
        assert config1 is not config2


class TestInitializeEnvironment:
    """Test suite for initialize_environment function."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_config()

    def teardown_method(self):
        """Clean up after tests."""
        reset_config()

    def test_initialize_with_seed(self):
        """Test initialization with custom seed."""
        config = initialize_environment(seed=555)
        assert config.get_random_seed() == 555

    def test_initialize_creates_directories(self):
        """Test that initialization creates directories."""
        config = initialize_environment()
        
        assert config.get_path('data_raw').exists()
        assert config.get_path('models').exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])