"""
Unit tests for the download module.
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import download_bulk_configs
from code.validators import validate_citations
from code.config import VALIDATED_SOURCE_WHITELIST

@patch('code.data.download.validate_citations')
@patch('code.data.download.requests.get')
def test_successful_download(mock_get, mock_validate):
    """Test successful download with valid URL."""
    # Setup mocks
    mock_validate.return_value = True
    mock_response = MagicMock()
    mock_response.content = b"test content"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    # Call function
    result = download_bulk_configs("https://materialsproject.org/test.json")
    
    # Assertions
    assert result.exists()
    mock_validate.assert_called_once()
    mock_get.assert_called_once()
    
    # Cleanup
    if result.exists():
        result.unlink()

@patch('code.data.download.validate_citations')
def test_invalid_url(mock_validate):
    """Test that invalid URL raises ValueError."""
    mock_validate.return_value = False
    
    with pytest.raises(ValueError, match=r"\[DATA_UNAVAILABLE\]"):
        download_bulk_configs("https://unauthorized-site.com/test.json")

@patch('code.data.download.validate_citations')
@patch('code.data.download.requests.get')
def test_retry_logic(mock_get, mock_validate):
    """Test that retry logic works correctly."""
    mock_validate.return_value = True
    
    # Setup mock to fail twice then succeed
    mock_response = MagicMock()
    mock_response.content = b"test content"
    mock_response.raise_for_status = MagicMock()
    
    mock_get.side_effect = [
        Exception("Connection error"),
        Exception("Connection error"),
        mock_response
    ]
    
    # Call function
    result = download_bulk_configs("https://materialsproject.org/test.json", max_retries=3)
    
    # Assertions
    assert result.exists()
    assert mock_get.call_count == 3
    
    # Cleanup
    if result.exists():
        result.unlink()

@patch('code.data.download.validate_citations')
@patch('code.data.download.requests.get')
def test_all_retries_fail(mock_get, mock_validate):
    """Test that all retries failing raises ConnectionError."""
    mock_validate.return_value = True
    
    # Setup mock to always fail
    mock_get.side_effect = Exception("Connection error")
    
    # Call function
    with pytest.raises(ConnectionError, match=r"\[DATA_UNAVAILABLE\].*attempts=3"):
        download_bulk_configs("https://materialsproject.org/test.json", max_retries=3)
    
    assert mock_get.call_count == 3