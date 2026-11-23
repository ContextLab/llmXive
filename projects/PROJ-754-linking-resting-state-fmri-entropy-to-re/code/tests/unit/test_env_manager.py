import os
import pytest
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
code_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(code_root))

from src.config.env_manager import (
    get_hcp_token, 
    validate_hcp_credentials, 
    get_optional_env, 
    EnvironmentError
)

class TestHCPEnvManager:
    """Tests for HCP token environment management."""

    def test_missing_hcp_token_raises_error(self, monkeypatch):
        """Verify that missing HCP_TOKEN raises ValueError with specific message."""
        # Ensure the variable is not set
        monkeypatch.delenv("HCP_TOKEN", raising=False)
        
        with pytest.raises(ValueError) as exc_info:
            get_hcp_token()
        
        assert "HCP_TOKEN is required but not found in environment variables." in str(exc_info.value)

    def test_empty_hcp_token_raises_error(self, monkeypatch):
        """Verify that empty HCP_TOKEN raises ValueError."""
        monkeypatch.setenv("HCP_TOKEN", "")
        
        with pytest.raises(ValueError) as exc_info:
            get_hcp_token()
        
        assert "HCP_TOKEN is required but not found in environment variables." in str(exc_info.value)

    def test_whitespace_hcp_token_raises_error(self, monkeypatch):
        """Verify that whitespace-only HCP_TOKEN raises ValueError."""
        monkeypatch.setenv("HCP_TOKEN", "   ")
        
        with pytest.raises(ValueError) as exc_info:
            get_hcp_token()
        
        assert "HCP_TOKEN is required but not found in environment variables." in str(exc_info.value)

    def test_valid_hcp_token_returns_value(self, monkeypatch):
        """Verify that a valid token is returned correctly."""
        test_token = "valid_hcp_token_12345"
        monkeypatch.setenv("HCP_TOKEN", test_token)
        
        result = get_hcp_token()
        assert result == test_token

    def test_valid_hcp_token_with_whitespace_strips(self, monkeypatch):
        """Verify that token with surrounding whitespace is stripped."""
        test_token = "  valid_token_with_spaces  "
        monkeypatch.setenv("HCP_TOKEN", test_token)
        
        result = get_hcp_token()
        assert result == "valid_token_with_spaces"

    def test_validate_hcp_credentials_success(self, monkeypatch):
        """Verify validate_hcp_credentials returns True for valid token."""
        monkeypatch.setenv("HCP_TOKEN", "a" * 16) # Long enough token
        assert validate_hcp_credentials() is True

    def test_validate_hcp_credentials_failure(self, monkeypatch):
        """Verify validate_hcp_credentials raises on missing token."""
        monkeypatch.delenv("HCP_TOKEN", raising=False)
        with pytest.raises(ValueError):
            validate_hcp_credentials()

    def test_get_optional_env_present(self, monkeypatch):
        """Test getting an optional env var that exists."""
        monkeypatch.setenv("OPTIONAL_VAR", "some_value")
        assert get_optional_env("OPTIONAL_VAR") == "some_value"

    def test_get_optional_env_missing_default(self, monkeypatch):
        """Test getting an optional env var that is missing, returning default."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        assert get_optional_env("MISSING_VAR", "default_val") == "default_val"

    def test_get_optional_env_missing_no_default(self, monkeypatch):
        """Test getting an optional env var that is missing, no default provided."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        assert get_optional_env("MISSING_VAR") is None
