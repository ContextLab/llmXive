"""
Unit tests for download.py
"""
import pytest
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
from io import StringIO

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.download import (
    download_file_with_checksum,
    try_huggingface_download,
    compute_file_checksum
)
from code.utils.logger import reset_counters

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_file_checksum(temp_dir):
    """Test checksum computation on a known file"""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    checksum = compute_file_checksum(test_file)
    expected = hashlib.sha256(test_content).hexdigest()
    
    assert checksum.lower() == expected.lower()

@patch('code.data.download.urllib.request.urlretrieve')
def test_download_file_with_checksum_success(mock_urlretrieve, temp_dir):
    """Test successful download with checksum verification"""
    # Setup mock
    mock_urlretrieve.return_value = None
    
    test_file = temp_dir / "test.bin"
    test_content = b"Test content for checksum"
    test_file.write_bytes(test_content)
    
    # Mock the compute_file_checksum to return expected value
    expected_checksum = hashlib.sha256(test_content).hexdigest()
    
    with patch('code.data.download.compute_file_checksum', return_value=expected_checksum):
        success, message = download_file_with_checksum(
            "http://example.com/test.bin",
            test_file,
            expected_checksum
        )
        
        assert success is True
        assert "verified" in message.lower()

@patch('code.data.download.urllib.request.urlretrieve')
def test_download_file_with_checksum_failure(mock_urlretrieve, temp_dir):
    """Test download with checksum mismatch"""
    mock_urlretrieve.return_value = None
    
    test_file = temp_dir / "test.bin"
    test_content = b"Test content"
    test_file.write_bytes(test_content)
    
    wrong_checksum = "0" * 64  # Invalid checksum
    
    with patch('code.data.download.compute_file_checksum', return_value=wrong_checksum):
        success, message = download_file_with_checksum(
            "http://example.com/test.bin",
            test_file,
            "correct_checksum_123456789012345678901234567890123456789012345678901234"
        )
        
        assert success is False
        assert "mismatch" in message.lower()

@patch('code.data.download.load_dataset')
def test_huggingface_download_success(mock_load_dataset, temp_dir):
    """Test successful HuggingFace download"""
    # Mock dataset
    mock_dataset = MagicMock()
    mock_dataset.__len__ = lambda self: 100
    mock_dataset.to_parquet = MagicMock()
    
    mock_load_dataset.return_value = mock_dataset
    
    success, message = try_huggingface_download(
        "test/dataset",
        temp_dir,
        "train"
    )
    
    assert success is True
    assert "successfully downloaded" in message.lower()
    mock_dataset.to_parquet.assert_called_once()

def test_download_with_network_error(temp_dir):
    """Test download handling of network errors"""
    import urllib.error
    
    test_file = temp_dir / "test.bin"
    
    with patch('code.data.download.urllib.request.urlretrieve') as mock_urlretrieve:
        mock_urlretrieve.side_effect = urllib.error.URLError("Network error")
        
        success, message = download_file_with_checksum(
            "http://example.com/test.bin",
            test_file,
            None
        )
        
        assert success is False
        assert "failed" in message.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
