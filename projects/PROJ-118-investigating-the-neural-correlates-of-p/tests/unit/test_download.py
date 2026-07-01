"""
Unit tests for code/download.py
"""
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import requests

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from download import (
    download_file,
    verify_checksum,
    calculate_sha256,
    INITIAL_BACKOFF,
    MAX_RETRIES
)

def test_download_retry_on_failure():
    """
    Test that download_file retries 3 times on failure and raises error on 4th.
    This satisfies the requirement for retry logic with exponential backoff.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_path = Path(tmpdir) / "test_file.txt"
        
        # Mock requests.get to raise an exception every time
        with patch('download.requests.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network error")
            
            # Call the function - it should retry 3 times then raise
            with pytest.raises(requests.RequestException):
                download_file("http://example.com/fake", dest_path, retries=3)
            
            # Assert it was called 3 times (3 retries)
            assert mock_get.call_count == 3

def test_download_success():
    """Test successful download."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_path = Path(tmpdir) / "test_file.txt"
        test_content = b"Hello, World!"
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [test_content]
        mock_response.headers = {'content-length': str(len(test_content))}
        mock_response.raise_for_status = MagicMock()
        
        with patch('download.requests.get', return_value=mock_response):
            result = download_file("http://example.com/fake", dest_path)
            
            assert result is True
            assert dest_path.exists()
            with open(dest_path, 'rb') as f:
                assert f.read() == test_content

def test_verify_checksum_valid():
    """Test checksum verification with a known hash."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        content = b"test data"
        file_path.write_bytes(content)
        
        # Calculate actual hash
        actual_hash = calculate_sha256(file_path)
        
        # Verify with correct hash
        assert verify_checksum(file_path, actual_hash) is True
        
        # Verify with wrong hash
        assert verify_checksum(file_path, "wronghash123") is False

def test_verify_checksum_empty_file():
    """Test verification of an empty file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "empty.txt"
        file_path.write_bytes(b"")
        
        # Without expected hash, it should fail on empty check
        assert verify_checksum(file_path, None) is False

def test_verify_checksum_no_hash_non_empty():
    """Test verification without expected hash on non-empty file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "non_empty.txt"
        file_path.write_bytes(b"data")
        
        # Should pass because file is not empty
        assert verify_checksum(file_path, None) is True