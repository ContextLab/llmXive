"""
Unit tests for the configuration module (src/utils/config.py).
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from code.src.utils.config import (
    ConfigError,
    load_env_file,
    get_api_key,
    get_materials_project_api_key,
    get_huggingface_token,
    validate_materials_project_connection,
    get_project_root,
    get_config_summary
)


class TestLoadEnvFile:
    """Tests for load_env_file function."""

    def test_load_env_file_success(self, tmp_path):
        """Test successful loading of a valid .env file."""
        env_content = """
        # Comment line
        KEY1=value1
        KEY2="value with spaces"
        KEY3='single quoted value'
        EMPTY=
        """
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)

        result = load_env_file(str(env_file))

        assert result["KEY1"] == "value1"
        assert result["KEY2"] == "value with spaces"
        assert result["KEY3"] == "single quoted value"
        assert result["EMPTY"] == ""
        assert "KEY4" not in result  # Non-existent key

    def test_load_env_file_not_found(self, tmp_path):
        """Test behavior when .env file does not exist."""
        non_existent_path = tmp_path / "non_existent.env"
        
        result = load_env_file(str(non_existent_path))
        
        assert result == {}

    def test_load_env_file_empty(self, tmp_path):
        """Test loading an empty .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("")
        
        result = load_env_file(str(env_file))
        
        assert result == {}

    def test_load_env_file_comments_only(self, tmp_path):
        """Test loading a file with only comments."""
        env_content = """
        # This is a comment
        # Another comment
        """
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)
        
        result = load_env_file(str(env_file))
        
        assert result == {}


class TestGetApiKey:
    """Tests for get_api_key function."""

    def test_get_api_key_from_system_env(self, monkeypatch):
        """Test retrieving key from system environment."""
        monkeypatch.setenv("TEST_API_KEY", "system_value")
        
        result = get_api_key("TEST_API_KEY")
        
        assert result == "system_value"

    def test_get_api_key_from_env_file(self, tmp_path):
        """Test retrieving key from .env file when not in system env."""
        env_content = "TEST_KEY=file_value"
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)
        
        # Ensure not in system env
        if "TEST_KEY" in os.environ:
            del os.environ["TEST_KEY"]
            
        result = get_api_key("TEST_KEY", load_env_file(str(env_file)))
        
        assert result == "file_value"

    def test_get_api_key_missing(self, tmp_path):
        """Test error when key is missing from both sources."""
        env_file = tmp_path / ".env"
        env_file.write_text("OTHER_KEY=value")
        
        with pytest.raises(ConfigError, match="API key 'MISSING_KEY' not found"):
            get_api_key("MISSING_KEY", load_env_file(str(env_file)))


class TestGetMaterialsProjectApiKey:
    """Tests for get_materials_project_api_key function."""

    def test_get_materials_project_api_key_success(self, monkeypatch):
        """Test successful retrieval of Materials Project API key."""
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "mp_test_key_123")
        
        result = get_materials_project_api_key()
        
        assert result == "mp_test_key_123"

    def test_get_materials_project_api_key_missing(self, monkeypatch, tmp_path):
        """Test error when Materials Project API key is missing."""
        # Remove from system env
        if "MATERIALS_PROJECT_API_KEY" in os.environ:
            del os.environ["MATERIALS_PROJECT_API_KEY"]
        
        # Create empty .env
        env_file = tmp_path / ".env"
        env_file.write_text("")
        
        with pytest.raises(ConfigError):
            get_materials_project_api_key()


class TestGetHuggingfaceToken:
    """Tests for get_huggingface_token function."""

    def test_get_huggingface_token_success(self, monkeypatch):
        """Test successful retrieval of HuggingFace token."""
        monkeypatch.setenv("HUGGINGFACE_TOKEN", "hf_test_token_456")
        
        result = get_huggingface_token()
        
        assert result == "hf_test_token_456"

    def test_get_huggingface_token_missing(self, monkeypatch, tmp_path):
        """Test error when HuggingFace token is missing."""
        # Remove from system env
        if "HUGGINGFACE_TOKEN" in os.environ:
            del os.environ["HUGGINGFACE_TOKEN"]
        
        # Create empty .env
        env_file = tmp_path / ".env"
        env_file.write_text("")
        
        with pytest.raises(ConfigError):
            get_huggingface_token()


class TestValidateMaterialsProjectConnection:
    """Tests for validate_materials_project_connection function."""

    @patch('code.src.utils.config.requests.get')
    def test_validate_connection_success(self, mock_get, monkeypatch):
        """Test successful connection validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "valid_key")
        
        result = validate_materials_project_connection()
        
        assert result is True
        mock_get.assert_called_once()

    @patch('code.src.utils.config.requests.get')
    def test_validate_connection_invalid_key(self, mock_get, monkeypatch):
        """Test connection validation with invalid key (401)."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "invalid_key")
        
        result = validate_materials_project_connection()
        
        assert result is False

    @patch('code.src.utils.config.requests.get')
    def test_validate_connection_network_error(self, mock_get, monkeypatch):
        """Test connection validation with network error."""
        mock_get.side_effect = Exception("Network error")
        
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "some_key")
        
        result = validate_materials_project_connection()
        
        assert result is False

    def test_validate_connection_no_key(self, monkeypatch, tmp_path):
        """Test connection validation when no key is configured."""
        # Remove from system env
        if "MATERIALS_PROJECT_API_KEY" in os.environ:
            del os.environ["MATERIALS_PROJECT_API_KEY"]
        
        # Create empty .env
        env_file = tmp_path / ".env"
        env_file.write_text("")
        
        result = validate_materials_project_connection()
        
        assert result is False


class TestGetProjectRoot:
    """Tests for get_project_root function."""

    def test_get_project_root_finds_marker(self, tmp_path):
        """Test that project root is found when marker exists."""
        # Create a marker file in tmp_path
        (tmp_path / ".git").mkdir()
        
        # Change to a subdirectory
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        
        with patch('code.src.utils.config.Path.cwd', return_value=subdir):
            result = get_project_root()
            
            assert result == tmp_path

    def test_get_project_root_no_marker(self, tmp_path):
        """Test fallback to current directory when no marker found."""
        # Ensure no markers exist
        markers = ['.git', 'pyproject.toml', 'setup.py', 'README.md']
        for marker in markers:
            if (tmp_path / marker).exists():
                (tmp_path / marker).unlink()
        
        with patch('code.src.utils.config.Path.cwd', return_value=tmp_path):
            result = get_project_root()
            
            assert result == tmp_path


class TestGetConfigSummary:
    """Tests for get_config_summary function."""

    def test_get_config_summary_with_all_keys(self, monkeypatch):
        """Test summary when all keys are configured."""
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "key1")
        monkeypatch.setenv("HUGGINGFACE_TOKEN", "key2")
        
        summary = get_config_summary()
        
        assert summary["total_configured"] == 2
        assert "MATERIALS_PROJECT_API_KEY" in summary["configured_keys"]
        assert "HUGGINGFACE_TOKEN" in summary["configured_keys"]
        assert len(summary["missing_keys"]) == 0

    def test_get_config_summary_with_missing_keys(self, monkeypatch):
        """Test summary when some keys are missing."""
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "key1")
        
        summary = get_config_summary()
        
        assert summary["total_configured"] == 1
        assert "MATERIALS_PROJECT_API_KEY" in summary["configured_keys"]
        assert "HUGGINGFACE_TOKEN" in summary["missing_keys"]