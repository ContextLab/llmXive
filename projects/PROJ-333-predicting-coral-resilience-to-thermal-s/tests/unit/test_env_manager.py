"""
Unit tests for NCBI environment variable management.

These tests verify that:
1. Environment variables are loaded correctly
2. .env file loading works (if python-dotenv is available)
3. Configuration validation works
4. FTP access is properly configured by default
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.env_manager import (
    NCBIConfig,
    load_env_file,
    get_ncbi_config,
    get_entrez_headers,
    is_ftp_access_available,
    get_ftp_base_url,
    ensure_ncbi_access
)


class TestNCBIConfig:
    """Tests for NCBIConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = NCBIConfig()
        assert config.api_key is None
        assert config.email is None
        assert config.tool_name == "llmXive-coral-resilience"
        assert config.max_retries == 3
        assert config.timeout_seconds == 60
        assert config.use_direct_ftp is True
        assert "ftp-trace.ncbi.nlm.nih.gov" in config.ftp_base_url
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = NCBIConfig(
            api_key="test-key",
            email="test@example.com",
            tool_name="custom-tool",
            max_retries=5,
            use_direct_ftp=False
        )
        assert config.api_key == "test-key"
        assert config.email == "test@example.com"
        assert config.tool_name == "custom-tool"
        assert config.max_retries == 5
        assert config.use_direct_ftp is False
    
    def test_validate_with_ftp(self):
        """Test validation when using direct FTP."""
        config = NCBIConfig(use_direct_ftp=True)
        assert config.validate() is True
    
    def test_validate_without_api_key(self):
        """Test validation without API key (should still be valid)."""
        config = NCBIConfig(use_direct_ftp=False, api_key=None)
        assert config.validate() is True
    
    def test_validate_with_all_fields(self):
        """Test validation with all fields populated."""
        config = NCBIConfig(
            use_direct_ftp=False,
            api_key="test-key",
            email="test@example.com"
        )
        assert config.validate() is True


class TestLoadEnvFile:
    """Tests for load_env_file function."""
    
    def test_no_dotenv_installed(self):
        """Test behavior when python-dotenv is not installed."""
        with patch("code.data.env_manager.HAS_DOTENV", False):
            result = load_env_file()
            assert result is False
    
    def test_env_file_not_found(self, tmp_path):
        """Test behavior when .env file doesn't exist."""
        with patch("code.data.env_manager.HAS_DOTENV", True):
            result = load_env_file(tmp_path / "nonexistent.env")
            assert result is False
    
    def test_env_file_found(self, tmp_path):
        """Test successful .env file loading."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\n")
        
        with patch("code.data.env_manager.HAS_DOTENV", True):
            with patch("code.data.env_manager.load_dotenv") as mock_load:
                result = load_env_file(env_file)
                assert result is True
                mock_load.assert_called_once_with(env_file)


class TestGetNcbiConfig:
    """Tests for get_ncbi_config function."""
    
    def test_default_config_from_env(self):
        """Test default config when no env vars are set."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_ncbi_config()
            assert config.api_key is None
            assert config.email is None
            assert config.use_direct_ftp is True
    
    def test_config_with_api_key(self):
        """Test config with API key set."""
        with patch.dict(os.environ, {"NCBI_API_KEY": "test-key"}):
            config = get_ncbi_config()
            assert config.api_key == "test-key"
    
    def test_config_with_email(self):
        """Test config with email set."""
        with patch.dict(os.environ, {"NCBI_EMAIL": "test@example.com"}):
            config = get_ncbi_config()
            assert config.email == "test@example.com"
    
    def test_config_with_all_vars(self):
        """Test config with all environment variables set."""
        env_vars = {
            "NCBI_API_KEY": "test-key",
            "NCBI_EMAIL": "test@example.com",
            "NCBI_TOOL_NAME": "custom-tool",
            "USE_DIRECT_FTP": "false"
        }
        with patch.dict(os.environ, env_vars):
            config = get_ncbi_config()
            assert config.api_key == "test-key"
            assert config.email == "test@example.com"
            assert config.tool_name == "custom-tool"
            assert config.use_direct_ftp is False


class TestGetEntrezHeaders:
    """Tests for get_entrez_headers function."""
    
    def test_headers_without_credentials(self):
        """Test headers when no credentials are provided."""
        config = NCBIConfig()
        headers = get_entrez_headers(config)
        assert "User-Agent" in headers
        assert "X-NCBI-Email" not in headers
        assert "X-NCBI-APIKey" not in headers
    
    def test_headers_with_email(self):
        """Test headers with email provided."""
        config = NCBIConfig(email="test@example.com")
        headers = get_entrez_headers(config)
        assert headers["X-NCBI-Email"] == "test@example.com"
    
    def test_headers_with_api_key(self):
        """Test headers with API key provided."""
        config = NCBIConfig(api_key="test-key")
        headers = get_entrez_headers(config)
        assert headers["X-NCBI-APIKey"] == "test-key"
    
    def test_headers_with_both(self):
        """Test headers with both email and API key."""
        config = NCBIConfig(
            email="test@example.com",
            api_key="test-key"
        )
        headers = get_entrez_headers(config)
        assert headers["X-NCBI-Email"] == "test@example.com"
        assert headers["X-NCBI-APIKey"] == "test-key"


class TestFtpAccess:
    """Tests for FTP access functions."""
    
    def test_is_ftp_access_available_default(self):
        """Test that FTP access is available by default."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_ftp_access_available() is True
    
    def test_is_ftp_access_disabled(self):
        """Test FTP access when disabled."""
        with patch.dict(os.environ, {"USE_DIRECT_FTP": "false"}):
            assert is_ftp_access_available() is False
    
    def test_get_ftp_base_url_default(self):
        """Test default FTP base URL."""
        url = get_ftp_base_url()
        assert "ftp-trace.ncbi.nlm.nih.gov" in url
        assert "sra/sra-instant/reads/ByStudy/sra/" in url
    
    def test_get_ftp_base_url_custom(self):
        """Test custom FTP base URL."""
        custom_url = "ftp://custom.example.com/sra/"
        with patch.dict(os.environ, {"NCBI_FTP_BASE_URL": custom_url}):
            url = get_ftp_base_url()
            assert url == custom_url
    
    def test_ensure_ncbi_access_default(self):
        """Test that NCBI access is ensured by default."""
        with patch.dict(os.environ, {}, clear=True):
            assert ensure_ncbi_access() is True
    
    def test_ensure_ncbi_access_with_api_key(self):
        """Test NCBI access with API key."""
        with patch.dict(os.environ, {"NCBI_API_KEY": "test-key"}):
            assert ensure_ncbi_access() is True
