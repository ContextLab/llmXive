"""
Unit tests for T071: Explicit CDAWeb URL Verification.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from ingest import DataFetchError, verify_cdaweb_source, load_manifest, MANIFEST_PATH

@patch('ingest.requests.head')
@patch('ingest.requests.get')
def test_verify_cdaweb_success_head(mock_get, mock_head):
    """Test successful verification via HEAD request."""
    mock_head_response = MagicMock()
    mock_head_response.status_code = 200
    mock_head.return_value = mock_head_response

    # Mock manifest functions to avoid file I/O in unit test
    with patch('ingest.update_manifest_entry') as mock_update:
        result = verify_cdaweb_source("https://example.com", "test_source")
        
        assert result is True
        mock_head.assert_called_once()
        mock_update.assert_called_once()
        args = mock_update.call_args[0]
        assert args[0] == "test_source"
        assert args[1]["cme_url_verified"] is True

@patch('ingest.requests.head')
@patch('ingest.requests.get')
def test_verify_cdaweb_fallback_get(mock_get, mock_head):
    """Test verification fallback to GET when HEAD fails."""
    # HEAD fails
    mock_head_response = MagicMock()
    mock_head_response.status_code = 405
    mock_head.return_value = mock_head_response

    # GET succeeds
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get.return_value = mock_get_response

    with patch('ingest.update_manifest_entry') as mock_update:
        result = verify_cdaweb_source("https://example.com", "test_source")
        
        assert result is True
        assert mock_head.called
        assert mock_get.called
        mock_update.assert_called_once()

@patch('ingest.requests.head')
def test_verify_cdaweb_failure(mock_head):
    """Test that DataFetchError is raised on persistent failure."""
    mock_head_response = MagicMock()
    mock_head_response.status_code = 404
    mock_head.return_value = mock_head_response

    with patch('ingest.requests.get') as mock_get:
        mock_get_response = MagicMock()
        mock_get_response.status_code = 404
        mock_get.return_value = mock_get_response

        with pytest.raises(DataFetchError) as excinfo:
            verify_cdaweb_source("https://example.com", "test_source")
        
        assert "404" in str(excinfo.value)
        assert "test_source" in str(excinfo.value)