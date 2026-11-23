"""
Unit tests for OpenNeuro environment configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

# Adjust import based on project structure
from code.env_config import OpenNeuroConfig, get_openneuro_config


class TestOpenNeuroConfig:
    def test_initialization_valid_key(self):
        """Test that a valid API key initializes the config correctly."""
        config = OpenNeuroConfig(api_key="test_key_12345")
        assert config.api_key == "test_key_12345"
        assert config.anonymous_access is False
        assert config.base_url == "https://openneuro.org"

    def test_initialization_empty_key_raises(self):
        """Test that an empty API key raises a ValueError."""
        with pytest.raises(ValueError, match="OpenNeuro API key cannot be empty"):
            OpenNeuroConfig(api_key="")

    def test_get_headers(self):
        """Test that get_headers returns the correct authorization format."""
        config = OpenNeuroConfig(api_key="my_secret_key")
        headers = config.get_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer my_secret_key"
        assert headers["Content-Type"] == "application/json"

    def test_anonymous_access_flag(self):
        """Test that the anonymous access flag is respected."""
        config = OpenNeuroConfig(api_key="key", anonymous_access=True)
        assert config.anonymous_access is True


class TestGetOpenNeuroConfig:
    @patch("code.env_config.load_dotenv")
    @patch("code.env_config.os.getenv")
    def test_load_from_env_success(self, mock_getenv, mock_load_dotenv):
        """Test successful loading from environment variables."""
        mock_getenv.side_effect = lambda key, default=None: {
            "OPENNEURO_API_KEY": "env_key_999",
            "OPENNEURO_ANONYMOUS": "true"
        }.get(key, default)
        
        config = get_openneuro_config()
        
        assert config.api_key == "env_key_999"
        assert config.anonymous_access is True
        mock_load_dotenv.assert_called_once()

    @patch("code.env_config.load_dotenv")
    @patch("code.env_config.os.getenv")
    def test_missing_api_key_raises(self, mock_getenv, mock_load_dotenv):
        """Test that missing API key raises ValueError."""
        mock_getenv.return_value = None
        
        with pytest.raises(ValueError, match="OPENNEURO_API_KEY environment variable is not set"):
            get_openneuro_config()

    @patch("code.env_config.load_dotenv")
    @patch("code.env_config.os.getenv")
    def test_load_from_custom_env_file(self, mock_getenv, mock_load_dotenv):
        """Test loading from a specific .env file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OPENNEURO_API_KEY=custom_file_key\n")
            f.write("OPENNEURO_ANONYMOUS=true\n")
            temp_path = Path(f.name)
        
        try:
            # Reset side_effect to return specific values for the file load
            mock_getenv.side_effect = lambda key, default=None: {
                "OPENNEURO_API_KEY": "custom_file_key",
                "OPENNEURO_ANONYMOUS": "true"
            }.get(key, default)
            
            # Note: The actual implementation calls load_dotenv(env_file)
            # We mock os.getenv to simulate the result of loading that file
            config = get_openneuro_config(env_file=temp_path)
            
            assert config.api_key == "custom_file_key"
        finally:
            temp_path.unlink()
