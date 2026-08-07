"""
Unit tests for download.py module.
"""
import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import requests

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import download_file, _create_retry_session, load_zenodo_metadata
from validation_utils import compute_file_checksum

def test_create_retry_session():
    """Test that retry session is created correctly."""
    session = _create_retry_session()
    assert session is not None
    # Verify adapters are mounted
    assert "http://" in session.adapters
    assert "https://" in session.adapters

@patch('download.requests.Session')
def test_download_file_success(mock_session_class):
    """Test successful file download."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {'content-length': '100'}
    
    # Mock iter_content to yield data
    mock_response.iter_content = MagicMock(return_value=[b'x' * 50, b'x' * 50])
    
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session_class.return_value = mock_session

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "test.xyz"
        expected_checksum = hashlib.sha256(b'x' * 100).hexdigest()
        
        result = download_file("http://example.com/test.xyz", dest, expected_checksum)
        
        assert result is True
        assert dest.exists()
        assert compute_file_checksum(dest) == expected_checksum

@patch('download.requests.Session')
def test_download_file_checksum_mismatch(mock_session_class):
    """Test that checksum mismatch raises RuntimeError."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {'content-length': '10'}
    mock_response.iter_content = MagicMock(return_value=[b'1234567890'])
    
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session_class.return_value = mock_session

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "test.xyz"
        # Wrong checksum
        wrong_checksum = "0" * 64 
        
        with pytest.raises(RuntimeError, match="Checksum mismatch"):
            download_file("http://example.com/test.xyz", dest, wrong_checksum)
        
        # File should be cleaned up on failure
        assert not dest.exists()

@patch('download.requests.Session')
def test_download_file_network_error(mock_session_class):
    """Test that network errors are handled and file cleaned up."""
    mock_session = MagicMock()
    mock_session.get = MagicMock(side_effect=requests.exceptions.RequestException("Network error"))
    mock_session_class.return_value = mock_session

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "test.xyz"
        
        with pytest.raises(RuntimeError, match="Failed to download"):
            download_file("http://example.com/test.xyz", dest)
        
        assert not dest.exists()

@patch('download._create_retry_session')
def test_load_zenodo_metadata_success(mock_session_func):
    """Test successful metadata loading."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "files": [
            {"filename": "a-Si-1000.xyz", "url": "http://zenodo.org/1", "checksum": "abc"}
        ]
    }
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session_func.return_value = mock_session
    
    with patch('download.get_zenodo_url', return_value="http://zenodo.org/"):
        metadata = load_zenodo_metadata()
        
    assert "files" in metadata
    assert len(metadata["files"]) == 1
    assert metadata["files"][0]["filename"] == "a-Si-1000.xyz"

@patch('download._create_retry_session')
def test_load_zenodo_metadata_failure(mock_session_func):
    """Test metadata loading failure."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status = MagicMock(side_effect=requests.exceptions.HTTPError("404"))
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session_func.return_value = mock_session
    
    with patch('download.get_zenodo_url', return_value="http://zenodo.org/"):
        with pytest.raises(RuntimeError, match="Could not retrieve dataset metadata"):
            load_zenodo_metadata()
