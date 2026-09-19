"""
Unit tests for the configuration management module.
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.src.utils.config import (
    load_env_file,
    get_api_key,
    get_materials_project_api_key,
    get_huggingface_token,
    validate_materials_project_connection,
    get_project_root,
    get_config_summary,
    ConfigError
)


class TestLoadEnvFile:
    """Tests for the load_env_file function."""

    def test_load_env_file_with_valid_file(self, tmp_path):
        """Test loading a valid .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
        # Comment line
        MATERIALS_PROJECT_API_KEY=test_key_123
        HUGGINGFACE_TOKEN=hf_token_456
        EMPTY_VALUE=
        """)

        result = load_env_file(env_file)

        assert result["MATERIALS_PROJECT_API_KEY"] == "test_key_123"
        assert result["HUGGINGFACE_TOKEN"] == "hf_token_456"
        assert result["EMPTY_VALUE"] == ""
        assert "Comment line" not in result

    def test_load_env_file_not_exists(self, tmp_path):
        """Test loading a non-existent .env file returns empty dict."""
        non_existent = tmp_path / "non_existent.env"
        
        result = load_env_file(non_existent)
        
        assert result == {}

    def test_load_env_file_with_spaces(self, tmp_path):
        """Test loading .env file with spaces around keys/values."""
        env_file = tmp_path / ".env"
        env_file.write_text("  KEY  =  value_with_spaces  \n")

        result = load_env_file(env_file)

        assert result["KEY"] == "value_with_spaces"

    def test_load_env_file_with_quotes(self, tmp_path):
        """Test loading .env file with quoted values."""
        env_file = tmp_path / ".env"
        env_file.write_text('KEY1="quoted_value"\nKEY2=\'single_quoted\'\n')

        result = load_env_file(env_file)

        assert result["KEY1"] == "quoted_value"
        assert result["KEY2"] == "single_quoted"


class TestGetApiKey:
    """Tests for the get_api_key function."""

    def test_get_api_key_from_os_environ(self):
        """Test retrieving API key from os.environ."""
        test_key = "test_api_key_12345"
        
        with patch.dict(os.environ, {"MATERIALS_PROJECT_API_KEY": test_key}):
            result = get_api_key("materials_project", required=False)
            
            assert result == test_key

    def test_get_api_key_from_env_file(self, tmp_path):
        """Test retrieving API key from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("MATERIALS_PROJECT_API_KEY=env_file_key\n")
        
        with patch("code.src.utils.config.load_env_file", return_value={"MATERIALS_PROJECT_API_KEY": "env_file_key"}):
            # Clear environ to force fallback to .env
            with patch.dict(os.environ, {}, clear=False):
                if "MATERIALS_PROJECT_API_KEY" in os.environ:
                    del os.environ["MATERIALS_PROJECT_API_KEY"]
                
                result = get_api_key("materials_project", required=False)
                
                assert result == "env_file_key"

    def test_get_api_key_required_missing_raises(self):
        """Test that required=True raises ConfigError when key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("code.src.utils.config.load_env_file", return_value={}):
                with pytest.raises(ConfigError, match="Required API key"):
                    get_api_key("materials_project", required=True)

    def test_get_api_key_not_required_missing_returns_none(self):
        """Test that required=False returns None when key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("code.src.utils.config.load_env_file", return_value={}):
                result = get_api_key("materials_project", required=False)
                
                assert result is None

    def test_get_api_key_case_insensitive_service_name(self):
        """Test that service name is normalized correctly."""
        test_key = "test_key"
        
        with patch.dict(os.environ, {"MATERIALS_PROJECT_API_KEY": test_key}):
            # Test with different cases
            assert get_api_key("materials_project", required=False) == test_key
            assert get_api_key("MATERIALS_PROJECT", required=False) == test_key
            assert get_api_key("Materials-Project", required=False) == test_key


class TestGetMaterialsProjectApiKey:
    """Tests for get_materials_project_api_key."""

    def test_get_materials_project_api_key_returns_key(self):
        """Test retrieval of Materials Project API key."""
        test_key = "mp_test_key"
        
        with patch.dict(os.environ, {"MATERIALS_PROJECT_API_KEY": test_key}):
            result = get_materials_project_api_key()
            
            assert result == test_key

    def test_get_materials_project_api_key_returns_none(self):
        """Test that None is returned when key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_materials_project_api_key()
            
            assert result is None


class TestGetHuggingfaceToken:
    """Tests for get_huggingface_token."""

    def test_get_huggingface_token_returns_token(self):
        """Test retrieval of HuggingFace token."""
        test_token = "hf_test_token"
        
        with patch.dict(os.environ, {"HUGGINGFACE_API_KEY": test_token}):
            result = get_huggingface_token()
            
            assert result == test_token

    def test_get_huggingface_token_returns_none(self):
        """Test that None is returned when token is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_huggingface_token()
            
            assert result is None


class TestValidateMaterialsProjectConnection:
    """Tests for validate_materials_project_connection."""

    def test_validate_with_valid_key(self):
        """Test validation with a valid API key."""
        test_key = "valid_key_123"
        
        with patch.dict(os.environ, {"MATERIALS_PROJECT_API_KEY": test_key}):
            result = validate_materials_project_connection()
            
            assert result is True

    def test_validate_with_empty_key(self):
        """Test validation with an empty API key."""
        with patch.dict(os.environ, {"MATERIALS_PROJECT_API_KEY": ""}):
            result = validate_materials_project_connection()
            
            assert result is False

    def test_validate_with_none_key(self):
        """Test validation when no key is present."""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_materials_project_connection()
            
            assert result is False

    def test_validate_with_explicit_key(self):
        """Test validation with an explicitly passed key."""
        test_key = "explicit_key"
        
        result = validate_materials_project_connection(api_key=test_key)
        
        assert result is True


class TestGetProjectRoot:
    """Tests for get_project_root."""

    def test_get_project_root_returns_path(self):
        """Test that get_project_root returns a Path object."""
        root = get_project_root()
        
        assert isinstance(root, Path)
        # Should be a valid directory (assuming standard project structure)
        assert root.exists()


class TestGetConfigSummary:
    """Tests for get_config_summary."""

    def test_get_config_summary_returns_dict(self):
        """Test that get_config_summary returns a dictionary."""
        summary = get_config_summary()
        
        assert isinstance(summary, dict)
        assert "materials_project" in summary
        assert "huggingface" in summary
        assert "project_root" in summary

    def test_get_config_summary_structure(self):
        """Test the structure of the config summary."""
        summary = get_config_summary()
        
        mp_config = summary["materials_project"]
        assert "configured" in mp_config
        assert "key_length" in mp_config
        assert isinstance(mp_config["configured"], bool)
        assert isinstance(mp_config["key_length"], int)

        hf_config = summary["huggingface"]
        assert "configured" in hf_config
        assert "key_length" in hf_config