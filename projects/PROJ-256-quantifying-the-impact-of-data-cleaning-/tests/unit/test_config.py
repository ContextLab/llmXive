"""
Unit tests for the configuration management module.

These tests verify that the Config class correctly loads environment variables,
provides both dictionary and attribute access, and handles edge cases gracefully.
"""

import os
import json
import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil

# Import the config module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config, get_config, reload_config

class TestConfigInitialization:
    """Tests for Config class initialization."""
    
    def test_default_initialization(self):
        """Test that Config initializes with default values."""
        cfg = Config()
        
        # Check that default values are set
        assert cfg.get('RANDOM_SEED') == 42
        assert cfg.get('BOOTSTRAP_ITERATIONS') == 1000
        assert 'DATASET_URLS' in cfg
        assert len(cfg.get('DATASET_URLS')) >= 2
        
        # Check that paths are set
        assert cfg.get('OUTPUT_PATH') == './output'
        assert cfg.get('DATA_RAW_PATH') == './data/raw'
        
    def test_environment_variable_overrides(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            'RANDOM_SEED': '123',
            'BOOTSTRAP_ITERATIONS': '2000',
            'OUTPUT_PATH': '/tmp/test_output'
        }):
            cfg = Config()
            
            assert cfg.get('RANDOM_SEED') == 123
            assert cfg.get('BOOTSTRAP_ITERATIONS') == 2000
            assert cfg.get('OUTPUT_PATH') == '/tmp/test_output'
    
    def test_invalid_random_seed_fallback(self):
        """Test that invalid RANDOM_SEED falls back to default."""
        with patch.dict(os.environ, {'RANDOM_SEED': 'not_a_number'}):
            cfg = Config()
            
            # Should fall back to default 42
            assert cfg.get('RANDOM_SEED') == 42
    
    def test_invalid_bootstrap_iterations_fallback(self):
        """Test that invalid BOOTSTRAP_ITERATIONS falls back to default."""
        with patch.dict(os.environ, {'BOOTSTRAP_ITERATIONS': 'invalid'}):
            cfg = Config()
            
            # Should fall back to default 1000
            assert cfg.get('BOOTSTRAP_ITERATIONS') == 1000
    
    def test_invalid_dataset_urls_fallback(self):
        """Test that invalid DATASET_URLS falls back to defaults."""
        with patch.dict(os.environ, {'DATASET_URLS': 'not_valid_json'}):
            cfg = Config()
            
            # Should have default datasets
            assert len(cfg.get('DATASET_URLS')) >= 2
            assert any(d['name'] == 'UCI HAR' for d in cfg.get('DATASET_URLS'))
    
    def test_creates_output_directories(self):
        """Test that Config creates necessary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_output')
            
            with patch.dict(os.environ, {'OUTPUT_PATH': output_path}):
                cfg = Config()
                
                # Directory should be created
                assert os.path.exists(output_path)
                
                # Check other directories too
                assert os.path.exists(os.path.join(tmpdir, 'data', 'raw'))
                assert os.path.exists(os.path.join(tmpdir, 'data', 'processed'))
                assert os.path.exists(os.path.join(tmpdir, 'data', 'results'))
                assert os.path.exists(os.path.join(tmpdir, 'output', 'figures'))
                assert os.path.exists(os.path.join(tmpdir, 'output', 'reports'))

class TestConfigAccess:
    """Tests for Config access methods."""
    
    def test_get_method(self):
        """Test dictionary-style get method."""
        cfg = Config()
        
        # Normal access
        seed = cfg.get('RANDOM_SEED')
        assert isinstance(seed, int)
        
        # With default
        missing = cfg.get('MISSING_KEY', 'default_value')
        assert missing == 'default_value'
    
    def test_set_method(self):
        """Test setting configuration values."""
        cfg = Config()
        cfg.set('TEST_KEY', 'test_value')
        
        assert cfg.get('TEST_KEY') == 'test_value'
    
    def test_item_access(self):
        """Test dictionary-style item access."""
        cfg = Config()
        
        seed = cfg['RANDOM_SEED']
        assert isinstance(seed, int)
    
    def test_contains(self):
        """Test key existence check."""
        cfg = Config()
        
        assert 'RANDOM_SEED' in cfg
        assert 'MISSING_KEY' not in cfg
    
    def test_keys_values_items(self):
        """Test iteration methods."""
        cfg = Config()
        
        keys = list(cfg.keys())
        assert 'RANDOM_SEED' in keys
        assert 'BOOTSTRAP_ITERATIONS' in keys
        
        values = list(cfg.values())
        assert 42 in values
        assert 1000 in values
        
        items = list(cfg.items())
        assert ('RANDOM_SEED', 42) in items
    
    def test_attribute_access(self):
        """Test attribute-style access."""
        cfg = Config()
        
        # Should work for known keys
        assert cfg.RANDOM_SEED == 42
        assert cfg.BOOTSTRAP_ITERATIONS == 1000
        
        # Should not raise for unknown attributes (returns no-op)
        unknown = cfg.UNKNOWN_ATTR
        assert callable(unknown)
        assert unknown() is None
    
    def test_logger_style_calls(self):
        """Test that Config tolerates logger-style method calls."""
        cfg = Config()
        
        # These should not raise AttributeError
        cfg.info("Test info")
        cfg.warning("Test warning")
        cfg.error("Test error")
        cfg.debug("Test debug")
        
        # Should return None
        assert cfg.info("test") is None
        assert cfg.warning("test") is None

class TestGlobalConfig:
    """Tests for global config functions."""
    
    def test_get_config_returns_singleton(self):
        """Test that get_config returns the same instance."""
        cfg1 = get_config()
        cfg2 = get_config()
        
        assert cfg1 is cfg2
    
    def test_reload_config_creates_new_instance(self):
        """Test that reload_config creates a new instance."""
        cfg1 = get_config()
        cfg2 = reload_config()
        
        assert cfg1 is not cfg2
    
    def test_config_constants(self):
        """Test that module-level constants are set."""
        from config import RANDOM_SEED, BOOTSTRAP_ITERATIONS
        
        assert isinstance(RANDOM_SEED, int)
        assert isinstance(BOOTSTRAP_ITERATIONS, int)
        assert RANDOM_SEED == 42
        assert BOOTSTRAP_ITERATIONS == 1000

class TestConfigIntegration:
    """Integration tests for Config with environment."""
    
    def test_json_dataset_urls(self):
        """Test parsing JSON dataset URLs from environment."""
        test_urls = json.dumps([
            {"name": "Test Dataset", "url": "https://example.com/data.csv"}
        ])
        
        with patch.dict(os.environ, {'DATASET_URLS': test_urls}):
            cfg = Config()
            
            urls = cfg.get('DATASET_URLS')
            assert len(urls) == 1
            assert urls[0]['name'] == 'Test Dataset'
            assert urls[0]['url'] == 'https://example.com/data.csv'
    
    def test_custom_paths(self):
        """Test custom path configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_paths = {
                'DATA_RAW_PATH': os.path.join(tmpdir, 'custom_raw'),
                'DATA_PROCESSED_PATH': os.path.join(tmpdir, 'custom_processed'),
                'FIGURES_PATH': os.path.join(tmpdir, 'custom_figures')
            }
            
            env_vars = {k: v for k, v in custom_paths.items()}
            
            with patch.dict(os.environ, env_vars):
                cfg = Config()
                
                for key, expected_path in custom_paths.items():
                    assert cfg.get(key) == expected_path
                    # Directory should exist
                    assert os.path.exists(expected_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
