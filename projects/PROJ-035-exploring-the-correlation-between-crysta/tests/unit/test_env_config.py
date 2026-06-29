"""Unit tests for environment configuration management."""

import os
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config.env import (
    EnvironmentError,
    load_api_key,
    get_project_root,
    validate_environment,
    setup_environment,
)


class TestLoadApiKey:
    """Tests for the load_api_key function."""

    def test_load_api_key_success(self, monkeypatch):
        """Test successful loading of API key."""
        monkeypatch.setenv("MP_API_KEY", "test_api_key_123")
        api_key = load_api_key()
        assert api_key == "test_api_key_123"

    def test_load_api_key_whitespace_stripped(self, monkeypatch):
        """Test that whitespace is stripped from API key."""
        monkeypatch.setenv("MP_API_KEY", "  test_api_key  ")
        api_key = load_api_key()
        assert api_key == "test_api_key"

    def test_load_api_key_missing_raises_error(self, monkeypatch):
        """Test that missing API key raises EnvironmentError."""
        monkeypatch.delenv("MP_API_KEY", raising=False)
        with pytest.raises(EnvironmentError) as exc_info:
            load_api_key()
        assert "MP_API_KEY" in str(exc_info.value)

    def test_load_api_key_empty_raises_error(self, monkeypatch):
        """Test that empty API key raises EnvironmentError."""
        monkeypatch.setenv("MP_API_KEY", "")
        with pytest.raises(EnvironmentError) as exc_info:
            load_api_key()
        assert "MP_API_KEY" in str(exc_info.value)

    def test_load_api_key_custom_var_name(self, monkeypatch):
        """Test loading API key with custom variable name."""
        monkeypatch.setenv("CUSTOM_KEY", "custom_value")
        api_key = load_api_key("CUSTOM_KEY")
        assert api_key == "custom_value"


class TestGetProjectRoot:
    """Tests for the get_project_root function."""

    def test_get_project_root_returns_path(self):
        """Test that get_project_root returns a Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()


class TestValidateEnvironment:
    """Tests for the validate_environment function."""

    def test_validate_environment_success(self, monkeypatch):
        """Test successful validation with all env vars set."""
        monkeypatch.setenv("MP_API_KEY", "test_key")
        result = validate_environment()
        assert result["status"] == "valid"
        assert "MP_API_KEY" in result["variables"]

    def test_validate_environment_missing_raises_error(self, monkeypatch):
        """Test that missing env vars raise EnvironmentError."""
        monkeypatch.delenv("MP_API_KEY", raising=False)
        with pytest.raises(EnvironmentError) as exc_info:
            validate_environment()
        assert "MP_API_KEY" in str(exc_info.value)


class TestSetupEnvironment:
    """Tests for the setup_environment function."""

    def test_setup_environment_success(self, monkeypatch):
        """Test successful environment setup."""
        monkeypatch.setenv("MP_API_KEY", "test_key")
        # Should not raise
        setup_environment()

    def test_setup_environment_fails_without_key(self, monkeypatch):
        """Test that setup fails without API key."""
        monkeypatch.delenv("MP_API_KEY", raising=False)
        with pytest.raises(EnvironmentError):
            setup_environment()
