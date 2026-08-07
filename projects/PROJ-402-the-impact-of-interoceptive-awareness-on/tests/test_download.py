import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from code import download_file_with_checksum, calculate_sha256, get_wesad_download_url

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_calculate_sha256(temp_dir):
    """Test SHA-256 checksum calculation."""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    expected_hash = hashlib.sha256(test_content).hexdigest()
    actual_hash = calculate_sha256(test_file)
    
    assert actual_hash == expected_hash
    assert len(actual_hash) == 64  # SHA-256 produces 64 hex characters

@patch('code.01_download_data.requests.get')
def test_get_wesad_download_url(mock_get, temp_dir):
    """Test fetching download URL from Zenodo API."""
    # Mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'files': [
            {'key': 'wesad.zip', 'links': {'self': 'https://zenodo.org/api/records/123/files/wesad.zip'}}
        ]
    }
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    url = get_wesad_download_url()
    assert url == 'https://zenodo.org/api/records/123/files/wesad.zip'
    mock_get.assert_called_once()

@patch('code.01_download_data.requests.get')
def test_download_file_with_checksum_success(mock_get, temp_dir):
    """Test successful file download."""
    # Mock response
    mock_response = MagicMock()
    mock_response.headers = {'content-length': '100'}
    mock_response.iter_content.return_value = [b'x' * 50, b'y' * 50]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    output_file = temp_dir / "test.zip"
    checksum = download_file_with_checksum("https://example.com/file.zip", output_file, timeout=30)
    
    assert output_file.exists()
    assert checksum is not None
    assert len(checksum) == 64

@patch('code.01_download_data.requests.get')
def test_download_file_with_checksum_timeout(mock_get, temp_dir):
    """Test download timeout handling."""
    import requests
    
    # Mock timeout
    mock_get.side_effect = requests.exceptions.Timeout("Download timed out")
    
    output_file = temp_dir / "test.zip"
    temp_file = Path(str(output_file) + ".tmp")
    
    # Create a temporary file to simulate partial download
    temp_file.touch()
    
    with pytest.raises(TimeoutError):
        download_file_with_checksum("https://example.com/file.zip", output_file, timeout=1)
    
    # Verify temp file was deleted
    assert not temp_file.exists()
    assert not output_file.exists()

@patch('code.01_download_data.requests.get')
def test_download_file_with_checksum_network_error(mock_get, temp_dir):
    """Test network error handling."""
    import requests
    
    # Mock network error
    mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
    
    output_file = temp_dir / "test.zip"
    temp_file = Path(str(output_file) + ".tmp")
    
    # Create a temporary file to simulate partial download
    temp_file.touch()
    
    with pytest.raises(requests.exceptions.ConnectionError):
        download_file_with_checksum("https://example.com/file.zip", output_file, timeout=1)
    
    # Verify temp file was deleted
    assert not temp_file.exists()
    assert not output_file.exists()