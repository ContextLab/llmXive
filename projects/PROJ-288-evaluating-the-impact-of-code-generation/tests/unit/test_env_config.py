"""
Unit tests for environment configuration management.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from data.env_config import (
    load_environment_variables,
    get_github_token,
    validate_github_token,
    setup_github_credentials,
    test_github_connection
)

class TestLoadEnvironmentVariables:
    """Tests for load_environment_variables function."""
    
    def test_load_env_file_exists(self, tmp_path):
        """Test loading from an existing .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("GITHUB_TOKEN=ghp_test123\n")
        
        with patch('data.env_config.load_dotenv') as mock_load:
            result = load_environment_variables(str(env_file))
            
            assert result is True
            mock_load.assert_called_once_with(env_file)
    
    def test_load_env_file_not_exists(self, tmp_path):
        """Test behavior when .env file doesn't exist."""
        env_file = tmp_path / ".env"
        
        with patch('data.env_config.logger') as mock_logger:
            result = load_environment_variables(str(env_file))
            
            assert result is False
            mock_logger.warning.assert_called_once()
    
    def test_load_env_file_exception(self, tmp_path):
        """Test handling of exceptions during loading."""
        env_file = tmp_path / ".env"
        env_file.write_text("GITHUB_TOKEN=ghp_test123\n")
        
        with patch('data.env_config.load_dotenv', side_effect=Exception("Test error")):
            result = load_environment_variables(str(env_file))
            
            assert result is False

class TestGetGithubToken:
    """Tests for get_github_token function."""
    
    def test_get_token_from_env(self):
        """Test retrieving token from environment variable."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test123"}):
            token = get_github_token(required=False)
            assert token == "ghp_test123"
    
    def test_get_token_missing_required(self):
        """Test error when token is missing and required=True."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GITHUB_TOKEN environment variable is required"):
                get_github_token(required=True)
    
    def test_get_token_missing_not_required(self):
        """Test returning None when token is missing and required=False."""
        with patch.dict(os.environ, {}, clear=True):
            token = get_github_token(required=False)
            assert token is None
    
    def test_token_validation_warning(self, caplog):
        """Test warning for invalid token format."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "invalid_token"}):
            token = get_github_token(required=False)
            assert token == "invalid_token"
            assert "may be invalid" in caplog.text

class TestValidateGithubToken:
    """Tests for validate_github_token function."""
    
    def test_valid_ghp_token(self):
        """Test validation of ghp_ prefix."""
        assert validate_github_token("ghp_test123") is True
    
    def test_valid_gho_token(self):
        """Test validation of gho_ prefix."""
        assert validate_github_token("gho_test123") is True
    
    def test_valid_pat_token(self):
        """Test validation of github_pat_ prefix."""
        assert validate_github_token("github_pat_test123") is True
    
    def test_invalid_token(self):
        """Test validation of invalid token."""
        assert validate_github_token("invalid_token") is False
    
    def test_empty_token(self):
        """Test validation of empty token."""
        assert validate_github_token("") is False
    
    def test_none_token(self):
        """Test validation of None token."""
        assert validate_github_token(None) is False

class TestSetupGithubCredentials:
    """Tests for setup_github_credentials function."""
    
    @patch('data.env_config.load_environment_variables')
    @patch('data.env_config.get_github_token')
    def test_setup_success(self, mock_get_token, mock_load_env):
        """Test successful setup of credentials."""
        mock_load_env.return_value = True
        mock_get_token.return_value = "ghp_test123"
        
        token = setup_github_credentials()
        
        assert token == "ghp_test123"
        mock_load_env.assert_called_once()
        mock_get_token.assert_called_once_with(required=True)
    
    @patch('data.env_config.load_environment_variables')
    @patch('data.env_config.get_github_token')
    def test_setup_invalid_token(self, mock_get_token, mock_load_env):
        """Test setup with invalid token format."""
        mock_load_env.return_value = True
        mock_get_token.return_value = "invalid_token"
        
        with pytest.raises(ValueError, match="Invalid GitHub token format"):
            setup_github_credentials()

class TestTestGithubConnection:
    """Tests for test_github_connection function."""
    
    @patch('data.env_config.get_github_token')
    @patch('data.env_config.requests.get')
    def test_connection_success(self, mock_get, mock_token):
        """Test successful GitHub connection."""
        mock_token.return_value = "ghp_test123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = test_github_connection()
        
        assert result is True
        mock_get.assert_called_once()
    
    @patch('data.env_config.get_github_token')
    @patch('data.env_config.requests.get')
    def test_connection_failure(self, mock_get, mock_token):
        """Test failed GitHub connection."""
        mock_token.return_value = "ghp_test123"
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = test_github_connection()
        
        assert result is False
    
    @patch('data.env_config.get_github_token')
    def test_connection_no_token(self, mock_token):
        """Test connection when no token is available."""
        mock_token.return_value = None
        
        result = test_github_connection()
        
        assert result is False
    
    @patch('data.env_config.get_github_token')
    def test_connection_import_error(self, mock_token):
        """Test connection when requests is not available."""
        mock_token.return_value = "ghp_test123"
        
        with patch('data.env_config.requests', None):
            result = test_github_connection()
            
            assert result is False