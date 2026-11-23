"""
Unit tests for environment variable management utilities.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from utils.env import (
    get_project_env_path,
    get_env_var,
    get_overpass_api_key,
    get_aws_credentials,
    validate_required_env_vars,
    create_example_env_file
)
from config import get_path

class TestGetProjectEnvPath:
    def test_returns_correct_path(self):
        """Test that the function returns the .env path in the project root."""
        result = get_project_env_path()
        assert isinstance(result, Path)
        assert result.name == ".env"
        # It should be in the root relative to the project
        assert result.parent == get_path("")

class TestGetEnvVar:
    def test_returns_existing_var(self):
        """Test retrieving an existing environment variable."""
        test_key = "TEST_VAR_EXISTING"
        test_val = "test_value"
        with patch.dict(os.environ, {test_key: test_val}):
            result = get_env_var(test_key)
            assert result == test_val

    def test_returns_default_for_missing(self):
        """Test retrieving a missing variable returns the default."""
        test_key = "TEST_VAR_MISSING"
        default_val = "default_value"
        # Ensure it's not in env
        if test_key in os.environ:
            del os.environ[test_key]
        
        result = get_env_var(test_key, default=default_val)
        assert result == default_val

    def test_raises_on_missing_required(self):
        """Test that required=True raises ValueError if missing."""
        test_key = "TEST_VAR_REQUIRED"
        if test_key in os.environ:
            del os.environ[test_key]
        
        with pytest.raises(ValueError, match=f"Required environment variable '{test_key}' is not set"):
            get_env_var(test_key, required=True)

class TestGetOverpassApiKey:
    def test_returns_key(self):
        """Test retrieving the Overpass API key."""
        test_key = "OVERPASS_API_KEY"
        test_val = "secret_key_123"
        with patch.dict(os.environ, {test_key: test_val}):
            result = get_overpass_api_key()
            assert result == test_val

    def test_returns_none_if_missing(self):
        """Test that None is returned if the key is missing."""
        test_key = "OVERPASS_API_KEY"
        if test_key in os.environ:
            del os.environ[test_key]
        
        result = get_overpass_api_key()
        assert result is None

class TestGetAwsCredentials:
    def test_returns_dict_with_keys(self):
        """Test retrieving AWS credentials returns a dict with expected keys."""
        env_vars = {
            "AWS_ACCESS_KEY_ID": "access123",
            "AWS_SECRET_ACCESS_KEY": "secret456",
            "AWS_REGION": "eu-west-1"
        }
        with patch.dict(os.environ, env_vars):
            result = get_aws_credentials()
            assert isinstance(result, dict)
            assert result["aws_access_key_id"] == "access123"
            assert result["aws_secret_access_key"] == "secret456"
            assert result["aws_region"] == "eu-west-1"

    def test_default_region(self):
        """Test that AWS region defaults to us-east-1 if not set."""
        env_vars = {
            "AWS_ACCESS_KEY_ID": "access123",
            "AWS_SECRET_ACCESS_KEY": "secret456"
        }
        with patch.dict(os.environ, env_vars):
            # Ensure AWS_REGION is not set
            if "AWS_REGION" in os.environ:
                del os.environ["AWS_REGION"]
            
            result = get_aws_credentials()
            assert result["aws_region"] == "us-east-1"

class TestValidateRequiredEnvVars:
    def test_all_present(self):
        """Test validation passes when all keys are present."""
        keys = ["KEY_A", "KEY_B"]
        with patch.dict(os.environ, {"KEY_A": "val", "KEY_B": "val"}):
            assert validate_required_env_vars(keys) is True

    def test_missing_raises(self):
        """Test validation raises ValueError when a key is missing."""
        keys = ["KEY_A", "KEY_MISSING"]
        with patch.dict(os.environ, {"KEY_A": "val"}):
            with pytest.raises(ValueError, match="Missing required environment variables"):
                validate_required_env_vars(keys)

class TestCreateExampleEnvFile:
    def test_creates_file(self, tmp_path):
        """Test that the function creates a .env.example file."""
        # Mock get_path to return tmp_path
        with patch('utils.env.get_path', return_value=tmp_path):
            result_path = create_example_env_file()
            assert result_path.exists()
            assert result_path.name == ".env.example"
            
            # Check content
            content = result_path.read_text()
            assert "OVERPASS_API_KEY" in content
            assert "AWS_ACCESS_KEY_ID" in content
    
    def test_does_not_overwrite_existing(self, tmp_path):
        """Test that the function does not overwrite an existing .env.example."""
        existing_path = tmp_path / ".env.example"
        existing_path.write_text("EXISTING_CONTENT")
        
        with patch('utils.env.get_path', return_value=tmp_path):
            result_path = create_example_env_file()
            assert result_path.read_text() == "EXISTING_CONTENT"