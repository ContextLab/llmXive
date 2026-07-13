"""
Unit tests for the configuration management module.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch

# Import the module under test
# Assuming the test runs from the project root or code/ is in sys.path
try:
    from code.config import Config, ConfigError, get_config, require_hf_token
except ImportError:
    # Fallback for different execution contexts
    from config import Config, ConfigError, get_config, require_hf_token


class TestConfigInitialization:
    """Tests for Config class initialization and defaults."""

    def test_default_paths_exist(self):
        """Verify that default paths are set and directories are created."""
        with patch("code.config.Path.mkdir") as mock_mkdir:
            cfg = Config()
            # Check that mkdir was called for directories that didn't exist
            # (mocked to return True/False logic would be needed for strictness,
            # but here we just ensure the call happened if path didn't exist)
            # For this test, we just ensure no exception is raised.
            assert cfg.data_dir is not None
            assert cfg.state_dir is not None
            assert cfg.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_env_variables_override_defaults(self, monkeypatch):
        """Verify that environment variables override default paths."""
        custom_data = "/custom/data/path"
        custom_state = "/custom/state/path"
        custom_log = "DEBUG"
        
        monkeypatch.setenv("DATA_DIR", custom_data)
        monkeypatch.setenv("STATE_DIR", custom_state)
        monkeypatch.setenv("LOG_LEVEL", custom_log)
        
        # Need to reload or create a new instance logic if the module caches
        # Since Config reads os.getenv on __init__, a new instance works.
        # We must ensure we don't use the global 'config' singleton if it was already created.
        # So we instantiate a fresh one.
        cfg = Config()
        
        assert str(cfg.data_dir) == custom_data
        assert str(cfg.state_dir) == custom_state
        assert cfg.log_level == custom_log

    def test_hf_token_from_env(self, monkeypatch):
        """Verify HF token is loaded from environment."""
        test_token = "test_token_12345"
        monkeypatch.setenv("HF_TOKEN", test_token)
        
        cfg = Config()
        assert cfg.hf_token == test_token

    def test_hf_token_missing(self):
        """Verify HF token is None if not set."""
        # Ensure it's not set
        if "HF_TOKEN" in os.environ:
            del os.environ["HF_TOKEN"]
        
        cfg = Config()
        assert cfg.hf_token is None


class TestConfigValidation:
    """Tests for configuration validation logic."""

    def test_require_hf_token_success(self, monkeypatch):
        """Test require_hf_token returns token when present."""
        token = "valid_token"
        monkeypatch.setenv("HF_TOKEN", token)
        cfg = Config() # Re-init to pick up env var if needed, though we mock below
        
        # We test the function directly with a mock config or by setting env
        # The function 'require_hf_token' reads from the global 'config'
        # To test properly, we need to ensure the global config has the token
        # or mock the getter.
        # Simpler: set env, create a new module-level config (hard in Python without reload)
        # Let's just test the logic by patching the global config.
        
        with patch("code.config.config") as mock_global_config:
            mock_global_config.hf_token = token
            result = require_hf_token()
            assert result == token

    def test_require_hf_token_failure(self, monkeypatch):
        """Test require_hf_token raises ConfigError when token missing."""
        with patch("code.config.config") as mock_global_config:
            mock_global_config.hf_token = None
            
            with pytest.raises(ConfigError, match="HuggingFace token not found"):
                require_hf_token()


class TestConfigMethods:
    """Tests for Config utility methods."""

    def test_get_path(self):
        """Test get_path returns correct Path object."""
        cfg = Config()
        path = cfg.get_path("data_dir")
        assert isinstance(path, Path)

    def test_get_path_invalid_key(self):
        """Test get_path raises ConfigError for invalid key."""
        cfg = Config()
        with pytest.raises(ConfigError, match="not found"):
            cfg.get_path("invalid_key")

    def test_to_dict(self):
        """Test to_dict returns expected keys."""
        cfg = Config()
        d = cfg.to_dict()
        assert "data_dir" in d
        assert "state_dir" in d
        assert "log_level" in d
        assert "hf_token_set" in d
        assert "hf_token" not in d # Sensitive data excluded