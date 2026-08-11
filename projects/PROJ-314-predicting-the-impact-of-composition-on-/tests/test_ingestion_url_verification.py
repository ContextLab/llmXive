"""
tests/test_ingestion_url_verification.py
Unit tests for T053: NIST URL Verification.
"""
import pytest
from unittest.mock import patch, MagicMock
import requests
from ingestion import verify_nist_url, fetch_nist_data

class TestNistUrlVerification:
    
    def test_verify_url_success(self):
        """Test successful URL verification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/csv'}
        mock_response.content = b"col1,col2\n1,2"
        
        with patch('ingestion.requests.get', return_value=mock_response) as mock_get:
            is_valid, message = verify_nist_url("https://example.com/data.csv")
            
            mock_get.assert_called_once_with("https://example.com/data.csv", timeout=30)
            assert is_valid is True
            assert "Verified" in message
            
    def test_verify_url_404(self):
        """Test verification fails on 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch('ingestion.requests.get', return_value=mock_response):
            is_valid, message = verify_nist_url("https://example.com/notfound.csv")
            
            assert is_valid is False
            assert "404" in message
            
    def test_verify_url_timeout(self):
        """Test verification fails on timeout."""
        with patch('ingestion.requests.get', side_effect=requests.exceptions.Timeout):
            is_valid, message = verify_nist_url("https://slow.com/data.csv")
            
            assert is_valid is False
            assert "timeout" in message.lower()
            
    def test_verify_url_empty_content(self):
        """Test verification fails on empty content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/plain'}
        mock_response.content = b""
        
        with patch('ingestion.requests.get', return_value=mock_response):
            is_valid, message = verify_nist_url("https://empty.com/data.csv")
            
            assert is_valid is False
            assert "empty" in message.lower()
            
    def test_fetch_nist_data_fails_on_verification(self):
        """Test that fetch_nist_data raises error if verification fails."""
        with patch('ingestion.verify_nist_url', return_value=(False, "Verification failed")):
            with pytest.raises(RuntimeError) as exc_info:
                fetch_nist_data("https://fail.com/data.csv")
                
            assert "URL verification failed" in str(exc_info.value)