import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_cds_api import verify_cds_api_access, setup_logging

class TestVerifyCDSAPI:
    def test_verify_cds_api_access_success(self):
        """Test that verify_cds_api_access returns accessible status when API is reachable."""
        with patch('verify_cds_api.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            
            status, message = verify_cds_api_access()
            
            assert status == "accessible"
            assert "accessible" in message
            mock_session.get.assert_called_once_with("https://cds.climate.copernicus.eu/api/v2/resources")

    def test_verify_cds_api_access_auth_required(self):
        """Test that verify_cds_api_access returns accessible status when API returns 401/403."""
        with patch('verify_cds_api.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_session.get.return_value = mock_response
            
            status, message = verify_cds_api_access()
            
            assert status == "accessible"
            assert "Authentication required" in message

    def test_verify_cds_api_access_connection_error(self):
        """Test that verify_cds_api_access handles connection errors gracefully."""
        import requests
        with patch('verify_cds_api.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_session.get.side_effect = requests.exceptions.ConnectionError("Network error")
            
            status, message = verify_cds_api_access()
            
            assert status == "connection_failed"
            assert "Failed to connect" in message

    def test_verify_cds_api_access_unexpected_status(self):
        """Test that verify_cds_api_access handles unexpected status codes."""
        with patch('verify_cds_api.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_session.get.return_value = mock_response
            
            status, message = verify_cds_api_access()
            
            assert status == "unreachable"
            assert "unexpected status" in message
