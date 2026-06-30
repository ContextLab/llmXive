"""
Unit tests for the configuration management module.
"""
import os
import pytest
from pathlib import Path
import tempfile
import sys

# Ensure we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.config import (
    get_api_key,
    get_config,
    load_env_vars,
    validate_materials_project_config,
    validate_huggingface_config,
    get_project_paths,
    DEFAULTS
)


class TestConfigLoading:
    """Test environment variable loading functionality."""

    def test_load_env_vars_idempotent(self):
        """Test that load_env_vars can be called multiple times safely."""
        # First call
        load_env_vars()
        # Second call should not raise
        load_env_vars()
        assert True

    def test_load_env_vars_creates_cache(self):
        """Test that environment loading sets the cache flag."""
        from src.utils import config
        load_env_vars()
        assert "ENV_LOADED" in config._config_cache


class TestApiKeyRetrieval:
    """Test API key retrieval functionality."""

    def test_get_api_key_unknown_service(self):
        """Test that unknown service raises ValueError."""
        with pytest.raises(ValueError, match="Unknown service"):
            get_api_key("unknown_service")

    def test_get_api_key_missing_required(self):
        """Test that missing required key raises ValueError."""
        # Ensure the env var is not set
        os.environ.pop("MATERIALS_PROJECT_API_KEY", None)
        
        with pytest.raises(ValueError, match="API key.*is required"):
            get_api_key("materials_project", required=True)

    def test_get_api_key_missing_optional(self):
        """Test that missing optional key returns None."""
        os.environ.pop("MATERIALS_PROJECT_API_KEY", None)
        
        result = get_api_key("materials_project", required=False)
        assert result is None

    def test_get_api_key_with_env_var(self, monkeypatch):
        """Test retrieving key when environment variable is set."""
        test_key = "test_api_key_123"
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", test_key)
        
        result = get_api_key("materials_project", required=True)
        assert result == test_key

    def test_get_api_key_huggingface(self, monkeypatch):
        """Test retrieving HuggingFace token."""
        test_token = "hf_test_token"
        monkeypatch.setenv("HUGGINGFACE_TOKEN", test_token)
        
        result = get_api_key("huggingface", required=True)
        assert result == test_token


class TestConfigRetrieval:
    """Test general configuration retrieval."""

    def test_get_config_from_env(self, monkeypatch):
        """Test getting config from environment variable."""
        monkeypatch.setenv("MAX_WORKERS", "8")
        
        result = get_config("MAX_WORKERS")
        assert result == 8  # Should be converted to int

    def test_get_config_default(self):
        """Test getting config with default value."""
        os.environ.pop("TIMEOUT_SECONDS", None)
        
        result = get_config("TIMEOUT_SECONDS", default=600)
        assert result == 600

    def test_get_config_default_from_defaults(self):
        """Test getting config that falls back to DEFAULTS."""
        os.environ.pop("MAX_WORKERS", None)
        
        result = get_config("MAX_WORKERS")
        assert result == 4  # From DEFAULTS

    def test_get_config_boolean_conversion(self, monkeypatch):
        """Test boolean conversion in config."""
        monkeypatch.setenv("DEBUG_MODE", "true")
        
        result = get_config("DEBUG_MODE")
        assert result is True

        monkeypatch.setenv("DEBUG_MODE", "false")
        result = get_config("DEBUG_MODE")
        assert result is False


class TestValidation:
    """Test configuration validation functions."""

    def test_validate_mp_missing(self, monkeypatch):
        """Test validation fails when MP key is missing."""
        monkeypatch.delenv("MATERIALS_PROJECT_API_KEY", raising=False)
        
        result = validate_materials_project_config()
        assert result is False

    def test_validate_mp_present(self, monkeypatch):
        """Test validation succeeds when MP key is present."""
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "fake_key")
        
        result = validate_materials_project_config()
        assert result is True

    def test_validate_hf_missing(self, monkeypatch):
        """Test validation fails when HF token is missing."""
        monkeypatch.delenv("HUGGINGFACE_TOKEN", raising=False)
        
        result = validate_huggingface_config()
        assert result is False

    def test_validate_hf_present(self, monkeypatch):
        """Test validation succeeds when HF token is present."""
        monkeypatch.setenv("HUGGINGFACE_TOKEN", "fake_token")
        
        result = validate_huggingface_config()
        assert result is True


class TestProjectPaths:
    """Test project path generation."""

    def test_get_project_paths_structure(self):
        """Test that get_project_paths returns expected keys."""
        paths = get_project_paths()
        
        expected_keys = ["root", "src", "data", "data_raw", "data_processed", "tests", "figures"]
        for key in expected_keys:
            assert key in paths, f"Missing key: {key}"
            assert isinstance(paths[key], Path), f"Value for {key} is not a Path"

    def test_get_project_paths_relative(self):
        """Test that paths are relative to code directory."""
        paths = get_project_paths()
        
        # Root should be 'code' or value from config
        assert str(paths["root"]) in ["code", os.getenv("CODE_DIR", "code")]
        assert str(paths["src"]).endswith("src")
        assert str(paths["data"]).endswith("data")