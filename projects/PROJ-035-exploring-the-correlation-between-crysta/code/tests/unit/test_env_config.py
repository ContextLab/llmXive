import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.config.env import load_api_key, validate_environment, setup_logger

class TestGetApiKey:
    def test_load_api_key_existing(self):
        """Test loading an existing API key."""
        with patch.dict(os.environ, {"TEST_KEY": "secret_value"}):
            result = load_api_key("TEST_KEY")
            assert result == "secret_value"

    def test_load_api_key_missing(self):
        """Test loading a missing API key raises KeyError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyError, match="Environment variable 'MISSING_KEY' is not set."):
                load_api_key("MISSING_KEY")

class TestLoadMaterialsProjectApiKey:
    def test_mp_api_key_present(self):
        """Test that MP_API_KEY is loaded correctly when present."""
        with patch.dict(os.environ, {"MP_API_KEY": "mp_12345"}):
            result = load_api_key("MP_API_KEY")
            assert result == "mp_12345"

    def test_mp_api_key_missing_raises(self):
        """Test that MP_API_KEY missing raises KeyError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyError):
                load_api_key("MP_API_KEY")

class TestValidateEnvironment:
    @patch('src.config.env.sys.exit')
    @patch('src.config.env.setup_logger')
    def test_validate_environment_success(self, mock_logger, mock_exit):
        """Test validation passes when MP_API_KEY is set."""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        with patch.dict(os.environ, {"MP_API_KEY": "valid_key"}):
            result = validate_environment()
            
            assert result is True
            mock_exit.assert_not_called()
            mock_logger_instance.info.assert_called_with("Environment validation successful. All required API keys present.")

    @patch('src.config.env.sys.exit')
    @patch('src.config.env.setup_logger')
    def test_validate_environment_mp_api_key_missing(self, mock_logger, mock_exit):
        """Test validation fails with exit code 1 when MP_API_KEY is missing."""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        with patch.dict(os.environ, {}, clear=True):
            validate_environment()
            
            mock_exit.assert_called_once_with(1)
            mock_logger_instance.error.assert_called_with("MP_API_KEY not set")

    @patch('src.config.env.sys.exit')
    @patch('src.config.env.setup_logger')
    def test_validate_environment_other_key_missing(self, mock_logger, mock_exit):
        """Test validation fails for other missing keys."""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        with patch.dict(os.environ, {"MP_API_KEY": "valid_key"}):
            # Test with a different required key
            validate_environment(required_keys=["OTHER_KEY"])
            
            mock_exit.assert_called_once_with(1)
            mock_logger_instance.error.assert_called_with("Missing required environment variables: ['OTHER_KEY']")

class TestSetupLogger:
    def test_setup_logger_creates_handler(self):
        """Test that setup_logger creates a handler if none exist."""
        logger = setup_logger("test_logger_unique")
        assert len(logger.handlers) > 0
    
    def test_setup_logger_returns_existing(self):
        """Test that setup_logger returns existing logger configuration."""
        logger1 = setup_logger("test_logger_shared")
        logger2 = setup_logger("test_logger_shared")
        assert logger1 is logger2
        assert len(logger1.handlers) == 1 # Should not add another handler