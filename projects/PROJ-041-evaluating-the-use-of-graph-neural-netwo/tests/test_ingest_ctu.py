import os
import tempfile
import hashlib
from unittest.mock import patch, MagicMock
import pytest

from code.data.ingest_netflow import (
    download_file, 
    calculate_md5, 
    download_ctu_dataset, 
    CTU_EXPECTED_MD5,
    CTU_DATASET_URL
)

def test_calculate_md5():
    """Test MD5 calculation on a temporary file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = tmp.name
    
    try:
        md5_hash = calculate_md5(tmp_path)
        expected = hashlib.md5(b"test data").hexdigest()
        assert md5_hash == expected
    finally:
        os.unlink(tmp_path)

@patch('urllib.request.urlretrieve')
def test_download_file(mock_urlretrieve, tmp_path):
    """Test file download function."""
    mock_urlretrieve.return_value = None
    output_path = str(tmp_path / "test_file.txt")
    
    result = download_file("http://example.com/file.txt", output_path)
    
    assert result == output_path
    mock_urlretrieve.assert_called_once_with("http://example.com/file.txt", output_path)

@patch('code.data.ingest_netflow.download_file')
@patch('code.data.ingest_netflow.calculate_md5')
def test_download_ctu_dataset_success(mock_calc_md5, mock_download, tmp_path):
    """Test successful download and checksum validation."""
    mock_download.return_value = str(tmp_path / "ctu.tar.gz")
    mock_calc_md5.return_value = CTU_EXPECTED_MD5
    
    file_path, checksum = download_ctu_dataset(str(tmp_path))
    
    assert file_path == str(tmp_path / "ctu.tar.gz")
    assert checksum == CTU_EXPECTED_MD5
    mock_download.assert_called()
    mock_calc_md5.assert_called()

@patch('code.data.ingest_netflow.download_file')
@patch('code.data.ingest_netflow.calculate_md5')
def test_download_ctu_dataset_checksum_mismatch(mock_calc_md5, mock_download, tmp_path):
    """Test that checksum mismatch raises an error."""
    mock_download.return_value = str(tmp_path / "ctu.tar.gz")
    mock_calc_md5.return_value = "wrong_checksum"
    
    with pytest.raises(RuntimeError, match="Checksum mismatch"):
        download_ctu_dataset(str(tmp_path))

@patch('code.data.ingest_netflow.download_file')
def test_download_ctu_dataset_download_failure(mock_download, tmp_path):
    """Test that download failure raises an error."""
    mock_download.side_effect = RuntimeError("Download failed")
    
    with pytest.raises(RuntimeError, match="Download failed"):
        download_ctu_dataset(str(tmp_path))
