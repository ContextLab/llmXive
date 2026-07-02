"""
Unit tests for the Open Access Checker.
"""
import pytest
from unittest.mock import patch, MagicMock
from utils.oa_checker import is_open_access

class TestOAChecker:
    def test_oa_status_accessible(self):
        """Test that a 200 OK with HTML content returns True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
        mock_response.url = 'https://example.com/article/123'
        
        with patch('utils.oa_checker.requests.get', return_value=mock_response):
            assert is_open_access('https://example.com/article/123') is True

    def test_oa_status_paywalled_403(self):
        """Test that a 403 Forbidden returns False."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.url = 'https://publisher.com/login'
        
        with patch('utils.oa_checker.requests.get', return_value=mock_response):
            assert is_open_access('https://publisher.com/protected') is False

    def test_oa_status_redirect_to_login(self):
        """Test that a redirect to a login page returns False."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.url = 'https://publisher.com/login?return=/article'
        
        with patch('utils.oa_checker.requests.get', return_value=mock_response):
            assert is_open_access('https://publisher.com/article') is False

    def test_oa_status_timeout(self):
        """Test that a timeout returns False."""
        with patch('utils.oa_checker.requests.get', side_effect=Exception("Timeout")):
            assert is_open_access('https://slow-site.com') is False

    def test_oa_status_empty_url(self):
        """Test that an empty URL returns False."""
        assert is_open_access('') is False

    def test_oa_status_pdf_accessible(self):
        """Test that a 200 OK with PDF content returns True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/pdf'}
        mock_response.url = 'https://example.com/article.pdf'
        
        with patch('utils.oa_checker.requests.get', return_value=mock_response):
            assert is_open_access('https://example.com/article.pdf') is True