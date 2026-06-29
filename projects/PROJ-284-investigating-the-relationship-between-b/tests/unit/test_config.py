"""
Unit tests for the configuration management module.
"""

import os
import pytest
from unittest.mock import patch

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.config import (
    MEMORY_LIMIT_GB,
    MEMORY_LIMIT_BYTES,
    BATCH_SIZE,
    HCP_API_VERSION,
    SCHAEFER_ATLAS_URL,
    get_hcp_credentials,
    get_config,
    validate_config,
)


class TestConstants:
    """Test that configuration constants are set correctly."""

    def test_memory_limit_gb(self):
        """Verify memory limit is set to 7GB."""
        assert MEMORY_LIMIT_GB == 7.0

    def test_memory_limit_bytes(self):
        """Verify memory limit in bytes is calculated correctly."""
        expected = int(7.0 * 1024**3)
        assert MEMORY_LIMIT_BYTES == expected

    def test_batch_size(self):
        """Verify default batch size."""
        assert BATCH_SIZE == 10

    def test_hcp_api_version(self):
        """Verify HCP API version."""
        assert HCP_API_VERSION == "1.0"

    def test_schaefer_atlas_url(self):
        """Verify Schaefer atlas URL is not empty and is a valid URL."""
        assert SCHAEFER_ATLAS_URL.startswith("https://")
        assert "Schaefer" in SCHAEFER_ATLAS_URL


class TestHcpCredentials:
    """Test HCP credential retrieval."""

    def test_credentials_from_env(self):
        """Test that credentials are retrieved from environment variables."""
        with patch.dict(os.environ, {"HCP_USERNAME": "test_user", "HCP_PASSWORD": "test_pass"}):
            creds = get_hcp_credentials()
            assert creds["username"] == "test_user"
            assert creds["password"] == "test_pass"

    def test_missing_username_raises_error(self):
        """Test that missing username raises ValueError."""
        with patch.dict(os.environ, {"HCP_PASSWORD": "test_pass"}, clear=True):
            with pytest.raises(ValueError, match="HCP credentials not found"):
                get_hcp_credentials()

    def test_missing_password_raises_error(self):
        """Test that missing password raises ValueError."""
        with patch.dict(os.environ, {"HCP_USERNAME": "test_user"}, clear=True):
            with pytest.raises(ValueError, match="HCP credentials not found"):
                get_hcp_credentials()

    def test_both_missing_raises_error(self):
        """Test that missing both credentials raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HCP credentials not found"):
                get_hcp_credentials()


class TestGetConfig:
    """Test the get_config function."""

    def test_config_structure(self):
        """Test that get_config returns a dictionary with expected keys."""
        with patch.dict(os.environ, {"HCP_USERNAME": "u", "HCP_PASSWORD": "p"}):
            config = get_config()
            expected_keys = [
                "MEMORY_LIMIT_GB",
                "MEMORY_LIMIT_BYTES",
                "BATCH_SIZE",
                "HCP_API_VERSION",
                "HCP_BASE_URL",
                "SCHAEFER_ATLAS_URL",
                "HCP_CREDENTIALS",
            ]
            for key in expected_keys:
                assert key in config

    def test_config_values(self):
        """Test that config values match expected constants."""
        with patch.dict(os.environ, {"HCP_USERNAME": "u", "HCP_PASSWORD": "p"}):
            config = get_config()
            assert config["MEMORY_LIMIT_GB"] == 7.0
            assert config["BATCH_SIZE"] == 10
            assert config["HCP_API_VERSION"] == "1.0"


class TestValidateConfig:
    """Test the validate_config function."""

    def test_valid_config(self):
        """Test that validation passes with valid credentials."""
        with patch.dict(os.environ, {"HCP_USERNAME": "u", "HCP_PASSWORD": "p"}):
            assert validate_config() is True

    def test_invalid_credentials(self):
        """Test that validation fails without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            # This should print an error message and return False
            result = validate_config()
            assert result is False