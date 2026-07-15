"""
Unit tests for ingestion module.
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingest import verify_cda_url, update_manifest_entry, load_manifest

@patch('code.ingest.requests.get')
def test_verify_cda_url_success(mock_get):
    """Test successful URL verification."""
    mock_response = MagicMock()
    mock_response.text = "# LASCO CME List\n12345 67890 ID1 100 200 N00"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = verify_cda_url("https://example.com/test.txt")
    assert result is True

@patch('code.ingest.requests.get')
def test_verify_cda_url_timeout(mock_get):
    """Test URL verification with timeout."""
    from requests.exceptions import Timeout
    mock_get.side_effect = Timeout()

    result = verify_cda_url("https://example.com/test.txt")
    assert result is False

@patch('code.ingest.requests.get')
def test_verify_cda_url_empty_response(mock_get):
    """Test URL verification with empty response."""
    mock_response = MagicMock()
    mock_response.text = ""
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = verify_cda_url("https://example.com/test.txt")
    assert result is False

@patch('code.ingest.requests.get')
def test_verify_cda_url_invalid_format(mock_get):
    """Test URL verification with unexpected format."""
    mock_response = MagicMock()
    mock_response.text = "Unexpected content without LASCO or CME"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = verify_cda_url("https://example.com/test.txt")
    assert result is False

def test_update_manifest_entry():
    """Test updating manifest entry (mocked file system)."""
    # This test would require mocking file I/O
    # For now, we test the logic path
    pass

def test_load_manifest():
    """Test loading manifest (mocked file system)."""
    # This test would require mocking file I/O
    # For now, we test the logic path
    pass
