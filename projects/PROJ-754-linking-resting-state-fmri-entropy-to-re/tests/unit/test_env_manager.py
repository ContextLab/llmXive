"""
Unit tests for environment variable management.
"""
import os
import pytest
from unittest.mock import patch

# Adjust import path based on project structure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config.env_manager import (
    get_hcp_token,
    validate_hcp_credentials,
    get_optional_env,
    EnvironmentError,
    check_environment
)


class TestGetHcpToken:
    """Tests for get_hcp_token function."""

    def test_token_present(self):
        """Test that token is returned when present."""
        with patch.dict(os.environ, {"HCP_TOKEN": "test_token_123"}):
            result = get_hcp_token()
            assert result == "test_token_123"

    def test_token_missing(self):
        """Test that EnvironmentError is raised when token is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError) as exc_info:
                get_hcp_token()
            assert "HCP_TOKEN" in str(exc_info.value)
            assert "not set" in str(exc_info.value)

    def test_token_empty_string(self):
        """Test that EnvironmentError is raised when token is empty."""
        with patch.dict(os.environ, {"HCP_TOKEN": ""}):
            with pytest.raises(EnvironmentError) as exc_info:
                get_hcp_token()
            assert "HCP_TOKEN" in str(exc_info.value)
            assert "empty" in str(exc_info.value)

    def test_token_whitespace_only(self):
        """Test that EnvironmentError is raised when token is whitespace only."""
        with patch.dict(os.environ, {"HCP_TOKEN": "   "}):
            with pytest.raises(EnvironmentError) as exc_info:
                get_hcp_token()
            assert "HCP_TOKEN" in str(exc_info.value)


class TestValidateHcpCredentials:
    """Tests for validate_hcp_credentials function."""

    def test_valid_credentials(self):
        """Test that function returns True for valid credentials."""
        with patch.dict(os.environ, {"HCP_TOKEN": "valid_token"}):
            result = validate_hcp_credentials()
            assert result is True

    def test_invalid_credentials(self):
        """Test that function raises EnvironmentError for invalid credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError):
                validate_hcp_credentials()

    def test_whitespace_token(self):
        """Test that function raises error for whitespace-only token."""
        with patch.dict(os.environ, {"HCP_TOKEN": "   "}):
            with pytest.raises(EnvironmentError):
                validate_hcp_credentials()


class TestGetOptionalEnv:
    """Tests for get_optional_env function."""

    def test_variable_present(self):
        """Test returning value when variable is present."""
        with patch.dict(os.environ, {"MY_VAR": "value"}):
            result = get_optional_env("MY_VAR")
            assert result == "value"

    def test_variable_missing_no_default(self):
        """Test returning None when variable is missing and no default."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_optional_env("NONEXISTENT")
            assert result is None

    def test_variable_missing_with_default(self):
        """Test returning default when variable is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_optional_env("NONEXISTENT", default="default_value")
            assert result == "default_value"

    def test_variable_present_ignores_default(self):
        """Test that default is ignored when variable is present."""
        with patch.dict(os.environ, {"MY_VAR": "actual_value"}):
            result = get_optional_env("MY_VAR", default="default_value")
            assert result == "actual_value"


class TestCheckEnvironment:
    """Tests for check_environment function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        result = check_environment()
        assert isinstance(result, dict)

    def test_contains_hcp_token_status(self):
        """Test that result contains HCP_TOKEN status."""
        result = check_environment()
        assert "HCP_TOKEN" in result
        assert result["HCP_TOKEN"] in ["set", "missing"]

    def test_contains_pythonpath_status(self):
        """Test that result contains PYTHONPATH status."""
        result = check_environment()
        assert "PYTHONPATH" in result
        assert result["PYTHONPATH"] in ["set", "not set"]

    def test_hcp_token_status_set(self):
        """Test HCP_TOKEN status when token is set."""
        with patch.dict(os.environ, {"HCP_TOKEN": "token"}):
            result = check_environment()
            assert result["HCP_TOKEN"] == "set"

    def test_hcp_token_status_missing(self):
        """Test HCP_TOKEN status when token is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = check_environment()
            assert result["HCP_TOKEN"] == "missing"
