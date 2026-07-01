"""Unit tests for configuration management."""
import os
import tempfile
import pytest
from pathlib import Path
from code.utils.config import ConfigManager, get_config


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        # Clear any existing env vars for clean test
        for key in ['OPENML_API_KEY', 'RAW_DATA_DIR']:
            os.environ.pop(key, None)
        
        config = ConfigManager()
        assert config.get('RAW_DATA_DIR') == 'data/raw'
        assert config.get('LOG_LEVEL') == 'INFO'
        assert config.get('ENABLE_REAL_DATA') is False

    def test_env_variable_override(self):
        """Test that environment variables override defaults."""
        os.environ['RAW_DATA_DIR'] = '/custom/path'
        os.environ['LOG_LEVEL'] = 'DEBUG'
        
        config = ConfigManager()
        assert config.get('RAW_DATA_DIR') == '/custom/path'
        assert config.get('LOG_LEVEL') == 'DEBUG'
        
        # Cleanup
        del os.environ['RAW_DATA_DIR']
        del os.environ['LOG_LEVEL']

    def test_env_file_loading(self):
        """Test loading configuration from .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('RAW_DATA_DIR=/env/file/path\n')
            f.write('LOG_LEVEL=WARNING\n')
            env_file = f.name
        
        try:
            config = ConfigManager(env_file=env_file)
            assert config.get('RAW_DATA_DIR') == '/env/file/path'
            assert config.get('LOG_LEVEL') == 'WARNING'
        finally:
            os.unlink(env_file)

    def test_get_path(self):
        """Test that get_path returns Path objects."""
        config = ConfigManager()
        path = config.get_path('RAW_DATA_DIR')
        assert isinstance(path, Path)
        assert str(path) == 'data/raw'

    def test_ensure_dirs(self):
        """Test that ensure_dirs creates directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set a custom path in temp directory
            test_dir = os.path.join(tmpdir, 'test_output')
            os.environ['RAW_DATA_DIR'] = test_dir
            
            config = ConfigManager()
            config.ensure_dirs()
            
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)
            
            del os.environ['RAW_DATA_DIR']

    def test_is_real_data_available_false(self):
        """Test is_real_data_available returns False when not configured."""
        # Clear API keys
        os.environ.pop('OPENML_API_KEY', None)
        os.environ.pop('HF_TOKEN', None)
        os.environ['ENABLE_REAL_DATA'] = 'false'
        
        config = ConfigManager()
        assert config.is_real_data_available() is False

    def test_is_real_data_available_true(self):
        """Test is_real_data_available returns True when configured."""
        os.environ['ENABLE_REAL_DATA'] = 'true'
        os.environ['OPENML_API_KEY'] = 'test_key_123'
        
        config = ConfigManager()
        assert config.is_real_data_available() is True
        
        # Cleanup
        del os.environ['ENABLE_REAL_DATA']
        del os.environ['OPENML_API_KEY']

    def test_to_json(self):
        """Test JSON export of configuration."""
        config = ConfigManager()
        json_str = config.to_json()
        
        import json
        parsed = json.loads(json_str)
        assert 'RAW_DATA_DIR' in parsed
        assert 'LOG_LEVEL' in parsed

def test_get_config_singleton():
    """Test that get_config returns the singleton instance."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2
