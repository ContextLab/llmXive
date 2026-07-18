"""
Unit tests for the configuration management system.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

# Import the module to test
from src.config.settings import Settings, get_config, reset_config, ConfigError


class TestSettingsLoading:
    """Tests for basic configuration loading functionality."""
    
    def test_load_defaults_when_file_missing(self):
        """Should load default values when config file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "missing.yaml"
            settings = Settings(str(config_path))
            
            assert settings.get('resources.gpr_max_runtime') == 1800
            assert settings.get('resources.gpr_max_memory') == 5.0
            assert settings.get('ocr.fallback_enabled') is False
    
    def test_load_from_yaml_file(self):
        """Should load configuration from a valid YAML file."""
        yaml_content = """
        resources:
          gpr_max_runtime: 3600
          gpr_max_memory: 10.0
        ocr:
          fallback_enabled: true
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(yaml_content)
            
            settings = Settings(str(config_path))
            
            assert settings.get('resources.gpr_max_runtime') == 3600
            assert settings.get('resources.gpr_max_memory') == 10.0
            assert settings.get('ocr.fallback_enabled') is True
    
    def test_invalid_yaml_raises_error(self):
        """Should raise ConfigError for invalid YAML syntax."""
        yaml_content = """
        resources:
          gpr_max_runtime: invalid: yaml: content
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(yaml_content)
            
            with pytest.raises(ConfigError):
                Settings(str(config_path))


class TestEnvironmentOverrides:
    """Tests for environment variable overrides."""
    
    def test_env_override_integer(self):
        """Environment variables should override integer config values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("resources:\n  gpr_max_runtime: 100")
            
            with patch.dict(os.environ, {"BALLMILL_RESOURCES_GPR_MAX_RUNTIME": "5000"}):
                settings = Settings(str(config_path))
                assert settings.get('resources.gpr_max_runtime') == 5000
    
    def test_env_override_float(self):
        """Environment variables should override float config values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("resources:\n  gpr_max_memory: 2.0")
            
            with patch.dict(os.environ, {"BALLMILL_RESOURCES_GPR_MAX_MEMORY": "15.5"}):
                settings = Settings(str(config_path))
                assert settings.get('resources.gpr_max_memory') == 15.5
    
    def test_env_override_boolean(self):
        """Environment variables should override boolean config values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("ocr:\n  fallback_enabled: false")
            
            with patch.dict(os.environ, {"BALLMILL_OCR_FALLBACK_ENABLED": "true"}):
                settings = Settings(str(config_path))
                assert settings.get('ocr.fallback_enabled') is True
    
    def test_env_override_string(self):
        """Environment variables should override string config values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("api:\n  materials_project:\n    base_url: 'http://old.url'")
            
            with patch.dict(os.environ, {"BALLMILL_API_MATERIALS_PROJECT_BASE_URL": "http://new.url"}):
                settings = Settings(str(config_path))
                assert settings.get('api.materials_project.base_url') == "http://new.url"


class TestConfigAccess:
    """Tests for configuration access methods."""
    
    def test_get_with_default(self):
        """get() should return default for missing keys."""
        settings = Settings()
        assert settings.get('nonexistent.key', 'default_value') == 'default_value'
    
    def test_getitem_raises_on_missing(self):
        """__getitem__ should raise KeyError for missing keys."""
        settings = Settings()
        with pytest.raises(KeyError):
            _ = settings['nonexistent.key']
    
    def test_contains(self):
        """__contains__ should check for key existence."""
        settings = Settings()
        assert 'resources.gpr_max_runtime' in settings
        assert 'nonexistent.key' not in settings
    
    def test_to_dict(self):
        """to_dict() should return a copy of the config."""
        settings = Settings()
        config_dict = settings.to_dict()
        assert isinstance(config_dict, dict)
        assert 'resources' in config_dict


class TestSingleton:
    """Tests for the singleton configuration pattern."""
    
    def test_get_config_returns_singleton(self):
        """get_config() should return the same instance."""
        reset_config()
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2
    
    def test_reset_config(self):
        """reset_config() should allow re-initialization."""
        reset_config()
        cfg1 = get_config()
        reset_config()
        cfg2 = get_config()
        assert cfg1 is not cfg2
    
    def test_singleton_uses_default_path(self):
        """Singleton should use default config path."""
        reset_config()
        # This should not raise even if config.yaml doesn't exist in cwd
        cfg = get_config()
        assert cfg is not None
    
    def test_singleton_uses_custom_path(self):
        """Singleton should accept custom config path."""
        reset_config()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "custom.yaml"
            config_path.write_text("test: value")
            cfg = get_config(str(config_path))
            assert cfg.get('test') == 'value'
            reset_config()
    
    def tearDown(self):
        """Cleanup after tests."""
        reset_config()
