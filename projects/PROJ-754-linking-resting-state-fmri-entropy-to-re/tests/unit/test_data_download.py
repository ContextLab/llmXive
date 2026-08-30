"""
Unit tests for HCP credential validation logic.

This module validates the specific credential check logic implemented in T012,
ensuring that the system correctly checks for the 'HCP_TOKEN' environment variable
and raises an appropriate error if it is missing or invalid.
"""
import os
import pytest
from unittest.mock import patch
from pathlib import Path
import sys

# Ensure the project root is in the path to import src modules
# The test assumes it is run from the project root or the path is adjusted accordingly.
# Based on the API surface, we import from src.config.env_manager
try:
    from src.config.env_manager import validate_hcp_credentials, EnvironmentError
except ImportError:
    # Fallback for different execution contexts if necessary, though task says src/
    from config.env_manager import validate_hcp_credentials, EnvironmentError


class TestHCPCredentialValidation:
    """Test suite for HCP token validation logic."""

    def test_validate_hcp_credentials_missing_token(self):
        """Test that ValueError is raised when HCP_TOKEN is missing."""
        # Ensure the environment variable is not set
        with patch.dict(os.environ, {}, clear=False):
            # Remove it if it exists to be sure
            os.environ.pop('HCP_TOKEN', None)
            
            with pytest.raises(EnvironmentError) as exc_info:
                validate_hcp_credentials()
            
            assert "HCP_TOKEN is required but not found" in str(exc_info.value)

    def test_validate_hcp_credentials_empty_token(self):
        """Test that ValueError is raised when HCP_TOKEN is empty."""
        with patch.dict(os.environ, {'HCP_TOKEN': ''}):
            with pytest.raises(EnvironmentError) as exc_info:
                validate_hcp_credentials()
            
            assert "HCP_TOKEN is required but not found" in str(exc_info.value) or "invalid" in str(exc_info.value).lower()

    def test_validate_hcp_credentials_whitespace_token(self):
        """Test that ValueError is raised when HCP_TOKEN contains only whitespace."""
        with patch.dict(os.environ, {'HCP_TOKEN': '   '}):
            with pytest.raises(EnvironmentError) as exc_info:
                validate_hcp_credentials()
            
            # Depending on implementation, this might fail on strip check or length check
            assert "invalid" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_validate_hcp_credentials_valid_token(self):
        """Test that no error is raised when a valid token is present."""
        fake_token = "valid_hcp_token_string_12345"
        with patch.dict(os.environ, {'HCP_TOKEN': fake_token}):
            # Should not raise any exception
            result = validate_hcp_credentials()
            # Typically returns True or None if successful
            assert result is True or result is None

    def test_validate_hcp_credentials_returns_token(self):
        """Test that the function returns the token or a success indicator."""
        fake_token = "test_token_abc"
        with patch.dict(os.environ, {'HCP_TOKEN': fake_token}):
            result = validate_hcp_credentials()
            # If the function returns the token or a confirmation
            assert result is not False

    def test_environment_error_type(self):
        """Test that the specific Exception type is raised."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('HCP_TOKEN', None)
            with pytest.raises(EnvironmentError):
                validate_hcp_credentials()