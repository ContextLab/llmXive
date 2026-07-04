"""
Unit tests for environment variable management (src/config/env.py).
"""
import os
import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile

from src.config.env import (
    EnvironmentError,
    EnvConfig,
    get_config,
    get_openneuro_api_key,
    get_data_dir
)


class TestEnvConfigValidation:
    """Tests for the EnvConfig class validation logic."""

    def test_valid_config_initialization(self, tmp_path):
        """Test that a valid config initializes successfully."""
        config = EnvConfig("valid-key-123", str(tmp_path))
        assert config.openneuro_api_key == "valid-key-123"
        assert config.data_dir == tmp_path

    def test_empty_api_key_raises_error(self, tmp_path):
        """Test that an empty API key raises EnvironmentError."""
        with pytest.raises(EnvironmentError, match="non-empty"):
            EnvConfig("", str(tmp_path))

    def test_whitespace_api_key_raises_error(self, tmp_path):
        """Test that a whitespace-only API key raises EnvironmentError."""
        with pytest.raises(EnvironmentError, match="non-empty"):
            EnvConfig("   ", str(tmp_path))

    def test_empty_data_dir_raises_error(self):
        """Test that an empty DATA_DIR raises EnvironmentError."""
        with pytest.raises(EnvironmentError, match="non-empty"):
            EnvConfig("valid-key", "")

    def test_whitespace_data_dir_raises_error(self):
        """Test that a whitespace-only DATA_DIR raises EnvironmentError."""
        with pytest.raises(EnvironmentError, match="non-empty"):
            EnvConfig("valid-key", "   ")

    def test_data_dir_creation_on_init(self):
        """Test that DATA_DIR is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_base:
            new_dir = os.path.join(tmp_base, "new_subdir")
            assert not os.path.exists(new_dir)
            
            config = EnvConfig("valid-key", new_dir)
            assert os.path.exists(new_dir)
            assert config.data_dir == Path(new_dir)

class TestGlobalAccessors:
    """Tests for the global accessor functions."""

    def teardown_method(self):
        """Reset the global config state after each test."""
        import src.config.env as env_module
        env_module._config = None

    @patch.dict(os.environ, {"OPENNEURO_API_KEY": "test-key-123", "DATA_DIR": "/tmp/test-data"})
    def test_get_config_success(self):
        """Test successful retrieval of config when env vars are set."""
        config = get_config()
        assert config.openneuro_api_key == "test-key-123"
        assert config.data_dir == Path("/tmp/test-data")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_config_missing_api_key(self):
        """Test that missing API key raises error."""
        with pytest.raises(EnvironmentError, match="OPENNEURO_API_KEY"):
            get_config()

    @patch.dict(os.environ, {"OPENNEURO_API_KEY": "test-key"}, clear=True)
    def test_get_config_missing_data_dir(self):
        """Test that missing DATA_DIR raises error."""
        with pytest.raises(EnvironmentError, match="DATA_DIR"):
            get_config()

    @patch.dict(os.environ, {"OPENNEURO_API_KEY": "key-xyz", "DATA_DIR": "/data/root"})
    def test_get_openneuro_api_key(self):
        """Test the specific accessor for API key."""
        key = get_openneuro_api_key()
        assert key == "key-xyz"

    @patch.dict(os.environ, {"OPENNEURO_API_KEY": "key-xyz", "DATA_DIR": "/data/root"})
    def test_get_data_dir(self):
        """Test the specific accessor for data dir."""
        data_dir = get_data_dir()
        assert data_dir == Path("/data/root")

    @patch.dict(os.environ, {"OPENNEURO_API_KEY": "  spaced-key  ", "DATA_DIR": "  /path/to/data  "})
    def test_config_strips_whitespace(self):
        """Test that config strips whitespace from values."""
        config = get_config()
        assert config.openneuro_api_key == "spaced-key"
        assert config.data_dir == Path("/path/to/data")