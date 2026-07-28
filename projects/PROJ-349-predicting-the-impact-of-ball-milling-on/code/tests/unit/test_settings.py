"""
Unit tests for the settings configuration module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

from src.config.settings import (
    Settings,
    get_settings,
    reset_settings,
    get_config_value,
    get_resource_limits,
    get_api_endpoints,
    get_ocr_settings,
    get_data_paths,
    create_default_config,
    ConfigError
)


class TestSettings:
    """Test cases for the Settings class."""
    
    def test_singleton_pattern(self):
        """Test that Settings follows the singleton pattern."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_load_config_success(self):
        """Test successful configuration loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            test_config = {
                'api_endpoints': {'test': 'http://test.com'},
                'resource_limits': {'gpr_max_runtime': 3600}
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                settings = Settings()
                settings._config = {}
                settings._load_config()
                
                assert settings.get('api_endpoints.test') == 'http://test.com'
                assert settings.get('resource_limits.gpr_max_runtime') == 3600
    
    def test_load_config_missing_file(self):
        """Test behavior when config file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'nonexistent.yaml'
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                settings = Settings()
                settings._config = {}
                
                # Should create default config
                settings._load_config()
                assert config_path.exists()
    
    def test_load_config_invalid_yaml(self):
        """Test handling of invalid YAML syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'invalid.yaml'
            
            with open(config_path, 'w') as f:
                f.write('invalid: yaml: content: [')
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                settings = Settings()
                settings._config = {}
                
                with pytest.raises(ConfigError):
                    settings._load_config()
    
    def test_get_nested_value(self):
        """Test getting nested configuration values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            test_config = {
                'parent': {
                    'child': {
                        'value': 'test'
                    }
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                settings = Settings()
                settings._config = {}
                settings._load_config()
                
                assert settings.get('parent.child.value') == 'test'
                assert settings.get('parent.child.missing', 'default') == 'default'
    
    def test_get_nonexistent_key(self):
        """Test getting a non-existent key."""
        settings = get_settings()
        assert settings.get('nonexistent.key', 'default') == 'default'
    
    def test_reload_config(self):
        """Test reloading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            test_config = {'key': 'value1'}
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                settings = Settings()
                settings._config = {}
                settings._load_config()
                
                assert settings.get('key') == 'value1'
                
                # Update config file
                test_config['key'] = 'value2'
                with open(config_path, 'w') as f:
                    yaml.dump(test_config, f)
                
                settings.reload()
                assert settings.get('key') == 'value2'

class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    def test_get_config_value(self):
        """Test get_config_value function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            test_config = {'test_key': 'test_value'}
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                reset_settings()
                value = get_config_value('test_key', 'default')
                assert value == 'test_value'
    
    def test_get_resource_limits(self):
        """Test get_resource_limits function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            test_config = {
                'resource_limits': {
                    'gpr_max_runtime': 1800,
                    'gpr_max_memory': 5.0
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                reset_settings()
                limits = get_resource_limits()
                assert limits['gpr_max_runtime'] == 1800
                assert limits['gpr_max_memory'] == 5.0
    
    def test_get_api_endpoints(self):
        """Test get_api_endpoints function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            test_config = {
                'api_endpoints': {
                    'materials_project': 'http://mp.com'
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                reset_settings()
                endpoints = get_api_endpoints()
                assert endpoints['materials_project'] == 'http://mp.com'
    
    def test_get_ocr_settings(self):
        """Test get_ocr_settings function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            test_config = {
                'ocr_settings': {
                    'ocr_enabled': True,
                    'ocr_language': 'eng'
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                reset_settings()
                ocr_settings = get_ocr_settings()
                assert ocr_settings['ocr_enabled'] is True
                assert ocr_settings['ocr_language'] == 'eng'
    
    def test_get_data_paths(self):
        """Test get_data_paths function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            test_config = {
                'data_paths': {
                    'raw': 'data/raw',
                    'processed': 'data/processed'
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                reset_settings()
                paths = get_data_paths()
                assert paths['raw'] == 'data/raw'
                assert paths['processed'] == 'data/processed'

class TestCreateDefaultConfig:
    """Test cases for create_default_config function."""
    
    def test_create_default_config_creates_file(self):
        """Test that create_default_config creates a valid config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            
            result_path = create_default_config(config_path)
            
            assert result_path == config_path
            assert config_path.exists()
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            assert 'api_endpoints' in config
            assert 'resource_limits' in config
            assert 'ocr_settings' in config
            assert 'data_paths' in config
            assert config['resource_limits']['gpr_max_runtime'] == 1800
            assert config['resource_limits']['gpr_max_memory'] == 5.0
    
    def test_create_default_config_default_path(self):
        """Test create_default_config with default path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the project root
            mock_path = Path(tmpdir) / 'config.yaml'
            
            with patch('src.config.settings.Path.__truediv__', return_value=mock_path):
                with patch('src.config.settings.__file__', str(Path(tmpdir) / 'src' / 'config' / 'settings.py')):
                    result_path = create_default_config()
                    
                    assert result_path.exists()

class TestInvalidYamlHandling:
    """Test cases for invalid YAML handling."""
    
    def test_invalid_yaml_raises_error(self):
        """Test that invalid YAML raises ConfigError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            
            with open(config_path, 'w') as f:
                f.write('invalid: yaml: [')
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                settings = Settings()
                settings._config = {}
                
                with pytest.raises(ConfigError):
                    settings._load_config()
    
    def test_empty_yaml_file(self):
        """Test handling of empty YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            
            with open(config_path, 'w') as f:
                f.write('')
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                settings = Settings()
                settings._config = {}
                
                # Should not raise, just return empty config
                settings._load_config()
                assert settings._config == {}
    
    def test_yaml_with_comments_only(self):
        """Test handling of YAML file with only comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            
            with open(config_path, 'w') as f:
                f.write('# This is a comment\n# Another comment')
            
            with patch('src.config.settings.Path.__truediv__', return_value=config_path):
                settings = Settings()
                settings._config = {}
                
                settings._load_config()
                assert settings._config == {}