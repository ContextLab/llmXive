"""
Tests for the configuration module.

These tests verify that the configuration loader correctly:
1. Loads defaults
2. Overrides with config file values
3. Overrides with environment variables
4. Resolves paths correctly
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    Configuration,
    get_config,
    get_project_root,
    get_data_path,
    get_output_path,
    _PROJECT_ROOT
)


class TestConfigurationDefaults:
    """Test that default configuration values are set correctly."""

    def test_default_knn_neighbors(self):
        """Default KNN neighbors should be 5."""
        config = Configuration()
        assert config.get('knn_neighbors') == 5

    def test_default_random_seed(self):
        """Default random seed should be 42."""
        config = Configuration()
        assert config.get('random_seed') == 42

    def test_default_environment(self):
        """Default environment should be development."""
        config = Configuration()
        assert config.get('environment') == 'development'

    def test_default_fingerprint_bits(self):
        """Default fingerprint bits should be 2048."""
        config = Configuration()
        assert config.get('fingerprint_bits') == 2048


class TestConfigurationSingleton:
    """Test that Configuration is a singleton."""

    def test_singleton_instance(self):
        """Multiple calls to Configuration() should return same instance."""
        config1 = Configuration()
        config2 = Configuration()
        assert config1 is config2

    def test_singleton_get_config(self):
        """get_config() should return the singleton instance."""
        config1 = Configuration()
        config2 = get_config()
        assert config1 is config2


class TestConfigurationOverride:
    """Test configuration override mechanisms."""

    def test_env_variable_override(self, monkeypatch):
        """Environment variables should override defaults."""
        monkeypatch.setenv('LLMXIVE_KNN_NEIGHBORS', '10')
        
        # Create a fresh configuration instance by resetting the flag
        config = Configuration()
        config._initialized = False
        config.__init__()
        
        assert config.get('knn_neighbors') == 10

    def test_bool_env_variable_override(self, monkeypatch):
        """Boolean environment variables should be parsed correctly."""
        monkeypatch.setenv('LLMXIVE_DEBUG', 'true')
        
        config = Configuration()
        config._initialized = False
        config.__init__()
        
        assert config.get('debug') is True

    def test_env_variable_false(self, monkeypatch):
        """False boolean environment variables should be parsed correctly."""
        monkeypatch.setenv('LLMXIVE_DEBUG', 'false')
        
        config = Configuration()
        config._initialized = False
        config.__init__()
        
        assert config.get('debug') is False


class TestPathResolution:
    """Test path resolution functionality."""

    def test_get_project_root(self):
        """Project root should be a valid Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_data_path_raw(self):
        """Data path should resolve to correct directory."""
        path = get_data_path('raw')
        assert path.is_absolute()
        assert 'data' in str(path)
        assert 'raw' in str(path)

    def test_get_data_path_with_filename(self):
        """Data path with filename should include the filename."""
        path = get_data_path('processed', 'test.csv')
        assert path.name == 'test.csv'
        assert path.parent.name == 'processed'

    def test_get_output_path(self):
        """Output path should resolve to outputs directory."""
        path = get_output_path('metrics.json')
        assert path.name == 'metrics.json'
        assert 'outputs' in str(path)


class TestConfigurationMethods:
    """Test configuration utility methods."""

    def test_get_all_returns_dict(self):
        """get_all() should return a dictionary."""
        config = Configuration()
        all_config = config.get_all()
        assert isinstance(all_config, dict)
        assert len(all_config) > 0

    def test_get_with_default(self):
        """get() should return default for missing keys."""
        config = Configuration()
        value = config.get('nonexistent_key', 'default_value')
        assert value == 'default_value'

    def test_get_without_default(self):
        """get() should return None for missing keys without default."""
        config = Configuration()
        value = config.get('nonexistent_key')
        assert value is None

    def test_get_path_returns_path(self):
        """get_path() should return a Path object."""
        config = Configuration()
        path = config.get_path('data_raw_dir')
        assert isinstance(path, Path)


class TestConfigurationPersistence:
    """Test configuration save/load functionality."""

    def test_save_and_load_config(self, tmp_path):
        """Configuration should be savable and loadable from JSON."""
        config = Configuration()
        
        # Create a temporary config file
        temp_config_path = tmp_path / "test_settings.json"
        
        # Save configuration
        config.save_config(temp_config_path)
        
        # Verify file was created
        assert temp_config_path.exists()
        
        # Verify it's valid JSON
        with open(temp_config_path, 'r') as f:
            loaded = json.load(f)
        
        assert isinstance(loaded, dict)
        assert 'knn_neighbors' in loaded
        assert loaded['knn_neighbors'] == 5

    def test_save_creates_directories(self, tmp_path):
        """save_config() should create parent directories if needed."""
        config = Configuration()
        
        # Create a path with non-existent parent directories
        temp_config_path = tmp_path / "deep" / "nested" / "config" / "settings.json"
        
        # This should not raise an error
        config.save_config(temp_config_path)
        
        assert temp_config_path.exists()