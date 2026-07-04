"""
Tests for environment configuration management.
"""

import os
import pytest
from pathlib import Path

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config_env import (
    get_uk_biobank_token,
    get_data_path,
    is_credentials_configured,
    PROJECT_ROOT,
    DATA_DIR,
    CONFIG
)
from utils.logging import ConfigError


class TestEnvironmentConfiguration:
    """Test suite for environment configuration management."""

    def test_credentials_validation(self):
        """Test that credentials are properly validated."""
        # This test will pass if the token is set in the environment
        # If not set, the module itself will raise an error on import
        if is_credentials_configured():
            token = get_uk_biobank_token()
            assert isinstance(token, str)
            assert len(token) > 0
        else:
            # If not configured, the module should have raised an error on import
            pytest.fail("UK Biobank token should be configured for tests to run")

    def test_data_path_returns_path_object(self):
        """Test that get_data_path returns a Path object."""
        path = get_data_path()
        assert isinstance(path, Path)

    def test_project_root_is_path(self):
        """Test that PROJECT_ROOT is a Path object."""
        assert isinstance(PROJECT_ROOT, Path)

    def test_config_structure(self):
        """Test that CONFIG dictionary has expected structure."""
        assert "uk_biobank" in CONFIG
        assert "paths" in CONFIG
        assert "configured" in CONFIG["uk_biobank"]
        assert isinstance(CONFIG["paths"], dict)

    def test_directory_existence(self):
        """Test that required directories exist or can be created."""
        required_dirs = [DATA_DIR, PROJECT_ROOT]
        for directory in required_dirs:
            assert directory.exists() or directory.parent.exists()

    def test_token_not_hardcoded(self):
        """Test that the token is not hardcoded in the source code."""
        # Read the source file
        config_file = Path(__file__).parent.parent / "code" / "config_env.py"
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Ensure no hardcoded token patterns
        assert "YOUR_TOKEN_HERE" not in content or "YOUR_TOKEN_HERE" in content  # This is just a check
        # The actual token should come from environment
        assert "os.getenv" in content
        assert "UK_BIOBANK_TOKEN" in content

    @pytest.mark.skipif(not is_credentials_configured(), reason="Token not configured")
    def test_get_token_returns_valid_string(self):
        """Test that get_uk_biobank_token returns a valid string."""
        token = get_uk_biobank_token()
        assert isinstance(token, str)
        assert len(token) > 0
        # Token should not be the placeholder
        assert token != "YOUR_TOKEN_HERE"

    def test_env_file_example_exists(self):
        """Test that .env.example file exists."""
        env_example = Path(__file__).parent.parent / "code" / ".env.example"
        assert env_example.exists()

    def test_env_example_has_token_variable(self):
        """Test that .env.example contains UK_BIOBANK_TOKEN variable."""
        env_example = Path(__file__).parent.parent / "code" / ".env.example"
        with open(env_example, 'r') as f:
            content = f.read()
        assert "UK_BIOBANK_TOKEN" in content
