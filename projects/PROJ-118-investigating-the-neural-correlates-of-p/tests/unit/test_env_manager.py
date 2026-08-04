"""
Unit tests for environment variable management.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch

# Import the module under test
# Assuming tests are run from project root or PYTHONPATH is set
from code.env_manager import (
    get_openneuro_api_key,
    get_path,
    validate_environment,
    get_project_root,
)

class TestGetOpenNeuroApiKey:
    def test_key_exists(self):
        """Test retrieval when key is set."""
        with patch.dict(os.environ, {"OPENNEURO_API_KEY": "test_key_123"}):
            key = get_openneuro_api_key(required=True)
            assert key == "test_key_123"
    
    def test_key_missing_not_required(self):
        """Test retrieval when key is missing but not required."""
        with patch.dict(os.environ, {}, clear=True):
            key = get_openneuro_api_key(required=False)
            assert key is None
    
    def test_key_missing_required_raises(self):
        """Test that missing key raises error when required."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENNEURO_API_KEY environment variable is not set"):
                get_openneuro_api_key(required=True)

class TestGetPath:
    def test_env_var_set(self):
        """Test path retrieval from env var."""
        with patch.dict(os.environ, {"MY_PATH": "/custom/path"}):
            path = get_path("MY_PATH")
            assert path == Path("/custom/path")
    
    def test_env_var_missing_with_default(self):
        """Test path retrieval with default."""
        with patch.dict(os.environ, {}, clear=True):
            path = get_path("MISSING_PATH", "/default/path")
            assert path == Path("/default/path")
    
    def test_env_var_missing_no_default_raises(self):
        """Test that missing path raises error without default."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Environment variable 'MISSING_PATH' is not set"):
                get_path("MISSING_PATH")

class TestGetProjectRoot:
    def test_root_is_parent_of_code(self):
        """Verify project root logic."""
        root = get_project_root()
        # The code module is in code/, so root should be parent
        assert (root / "code").exists()

class TestValidateEnvironment:
    @patch.dict(os.environ, {"OPENNEURO_API_KEY": "valid_key"})
    def test_validate_success(self):
        """Test validation passes when key is set."""
        assert validate_environment() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_failure(self):
        """Test validation fails when key is missing."""
        assert validate_environment() is False
