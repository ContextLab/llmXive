"""
Unit tests for the auth_manager module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException

from src.utils.auth_manager import validate_lsms_token, get_lsms_token, validate_lsms_credentials, FatalError
from src.utils.io_helpers import FatalError as IoFatalError

class TestAuthManager:
    
    def test_get_lsms_token_missing(self):
        """Test that FatalError is raised when token is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(IoFatalError, match="WB_LSMS_TOKEN environment variable is not set."):
                get_lsms_token()

    def test_get_lsms_token_present(self):
        """Test that token is returned correctly when present."""
        test_token = "test_token_123"
        with patch.dict(os.environ, {"WB_LSMS_TOKEN": test_token}):
            token = get_lsms_token()
            assert token == test_token

    @patch('src.utils.auth_manager.requests.get')
    def test_validate_lsms_token_success(self, mock_get):
        """Test successful token validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = validate_lsms_token("valid_token")
        assert result is True
        mock_get.assert_called_once()

    @patch('src.utils.auth_manager.requests.get')
    def test_validate_lsms_token_invalid_401(self, mock_get):
        """Test validation fails on 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        with pytest.raises(IoFatalError, match="Invalid LSMS-ISA token"):
            validate_lsms_token("invalid_token")

    @patch('src.utils.auth_manager.requests.get')
    def test_validate_lsms_token_invalid_403(self, mock_get):
        """Test validation fails on 403."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_get.return_value = mock_response

        with pytest.raises(IoFatalError, match="Invalid LSMS-ISA token"):
            validate_lsms_token("invalid_token")

    @patch('src.utils.auth_manager.requests.get')
    def test_validate_lsms_token_network_error(self, mock_get):
        """Test validation fails on network error."""
        mock_get.side_effect = RequestException("Network error")

        with pytest.raises(IoFatalError, match="Could not connect to World Bank API"):
            validate_lsms_token("token")

    def test_validate_lsms_token_empty(self):
        """Test validation fails on empty token."""
        with pytest.raises(IoFatalError, match="LSMS-ISA token is missing"):
            validate_lsms_token("")

    @patch('src.utils.auth_manager.get_lsms_token')
    @patch('src.utils.auth_manager.validate_lsms_token')
    def test_validate_lsms_credentials_success(self, mock_validate, mock_get_token):
        """Test successful credentials validation."""
        mock_get_token.return_value = "valid_token"
        mock_validate.return_value = True

        # Should not raise
        validate_lsms_credentials()

    @patch('src.utils.auth_manager.get_lsms_token')
    @patch('src.utils.auth_manager.validate_lsms_token')
    def test_validate_lsms_credentials_failure(self, mock_validate, mock_get_token):
        """Test credentials validation fails if token validation fails."""
        mock_get_token.return_value = "valid_token"
        mock_validate.side_effect = IoFatalError("Validation failed")

        with pytest.raises(IoFatalError, match="Validation failed"):
            validate_lsms_credentials()
