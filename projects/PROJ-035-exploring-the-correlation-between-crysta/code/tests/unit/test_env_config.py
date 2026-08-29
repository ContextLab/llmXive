"""
Unit tests for environment configuration management.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.config.env import (
    get_api_key, 
    load_materials_project_api_key, 
    validate_environment,
    _ENV_PATH
)


class TestGetApiKey:
    """Tests for get_api_key function."""

    def test_get_existing_key(self):
        """Test retrieving an existing environment variable."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = get_api_key("TEST_VAR", required=False)
            assert result == "test_value"

    def test_get_missing_key_not_required(self):
        """Test retrieving a missing environment variable when not required."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_api_key("NON_EXISTENT", required=False)
            assert result is None

    def test_get_missing_key_required_raises(self):
        """Test that retrieving a missing required key raises RuntimeError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                get_api_key("NON_EXISTENT", required=True)
            
            assert "NON_EXISTENT" in str(exc_info.value)

    def test_key_stripped(self):
        """Test that the returned key is stripped of whitespace."""
        with patch.dict(os.environ, {"TEST_VAR": "  value_with_spaces  "}):
            result = get_api_key("TEST_VAR", required=False)
            assert result == "value_with_spaces"


class TestLoadMaterialsProjectApiKey:
    """Tests for load_materials_project_api_key function."""

    def test_load_mp_key(self):
        """Test loading the MP API key."""
        fake_key = "mp-1234567890abcdef"
        with patch.dict(os.environ, {"MP_API_KEY": fake_key}):
            result = load_materials_project_api_key()
            assert result == fake_key

    def test_load_mp_key_missing(self):
        """Test that missing MP API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                load_materials_project_api_key()
            
            assert "MP_API_KEY" in str(exc_info.value)


class TestValidateEnvironment:
    """Tests for validate_environment function."""

    def test_validate_success(self):
        """Test validation passes when key exists."""
        with patch.dict(os.environ, {"MP_API_KEY": "fake_key"}):
            assert validate_environment() is True

    def test_validate_failure(self):
        """Test validation fails when key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError):
                validate_environment()