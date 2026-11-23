"""
Unit tests for the download module.
"""
import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import requests

# Mock the environment variable before importing download
os.environ["ZENODO_RECORD_ID"] = "123456"
os.environ["DATA_DIR"] = "/tmp/test_data"

from download import download_file, load_zenodo_metadata, compute_file_checksum

def test_download_file_success():
    """Test successful download and checksum verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "test.txt"
        content = b"Hello, World!"
        expected_checksum = hashlib.md5(content).hexdigest()
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [content]
        mock_response.headers = {'content-length': str(len(content))}
        mock_response.raise_for_status = MagicMock()
        
        with patch('download.requests.get', return_value=mock_response):
            download_file("http://example.com/test.txt", dest, expected_checksum)
            
        assert dest.exists()
        assert dest.read_bytes() == content

def test_download_file_checksum_mismatch():
    """Test that download raises error on checksum mismatch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "test.txt"
        content = b"Hello, World!"
        wrong_checksum = "00000000000000000000000000000000" # Invalid MD5
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [content]
        mock_response.headers = {'content-length': str(len(content))}
        mock_response.raise_for_status = MagicMock()
        
        with patch('download.requests.get', return_value=mock_response):
            with pytest.raises(RuntimeError, match="Checksum verification failed"):
                download_file("http://example.com/test.txt", dest, wrong_checksum)

def test_download_file_network_error():
    """Test that download raises error on network failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "test.txt"
        
        with patch('download.requests.get', side_effect=requests.exceptions.ConnectionError()):
            with pytest.raises(RuntimeError, match="Download failed"):
                download_file("http://example.com/test.txt", dest)

def test_load_zenodo_metadata_success():
    """Test loading metadata from Zenodo."""
    mock_metadata = {
        "files": [
            {
                "key": "config_1.xyz",
                "checksum": "md5:abc123",
                "links": {"self": "http://zenodo.org/file1"}
            }
        ]
    }
    
    mock_response = MagicMock()
    mock_response.json.return_value = mock_metadata
    mock_response.raise_for_status = MagicMock()
    
    with patch('download.requests.get', return_value=mock_response):
        result = load_zenodo_metadata("123456")
        
    assert result == mock_metadata

def test_load_zenodo_metadata_failure():
    """Test that loading metadata raises error on failure."""
    with patch('download.requests.get', side_effect=requests.exceptions.HTTPError()):
        with pytest.raises(RuntimeError, match="Failed to fetch metadata"):
            load_zenodo_metadata("123456")
