import os
import hashlib
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.ingest_netflow import calculate_md5, download_file, download_ctu_dataset, ensure_data_dirs, load_state, STATE_FILE

def test_calculate_md5(tmp_path):
    """Test MD5 calculation function."""
    test_file = tmp_path / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    expected_hash = hashlib.md5(test_content).hexdigest()
    actual_hash = calculate_md5(str(test_file))
    
    assert actual_hash == expected_hash

def test_ensure_data_dirs(tmp_path, monkeypatch):
    """Test that ensure_data_dirs creates required directories."""
    monkeypatch.chdir(tmp_path)
    ensure_data_dirs()
    
    assert os.path.exists("data/raw")
    assert os.path.exists("data/processed")
    assert os.path.exists("data/results")
    assert os.path.exists("state/projects")

def test_download_file_success(tmp_path):
    """Test successful file download and checksum validation."""
    # Create a mock response
    mock_data = b"Mock file content for testing"
    mock_hash = hashlib.md5(mock_data).hexdigest()
    
    dest_path = tmp_path / "test_download.txt"
    
    with patch('urllib.request.urlretrieve') as mock_urlretrieve:
        mock_urlretrieve.return_value = None # Simulate successful download
        # We need to mock the file creation as well since urlretrieve doesn't actually run
        # In a real test, we might use a local server or a known file
        # For this unit test, we'll simulate the download by creating the file
        dest_path.write_bytes(mock_data)
        
        # Mock calculate_md5 to return the known hash
        with patch('data.ingest_netflow.calculate_md5', return_value=mock_hash):
            result = download_file("http://example.com/test.txt", str(dest_path), mock_hash)
            
            assert result is True
            assert dest_path.exists()

def test_download_file_checksum_mismatch(tmp_path):
    """Test that download_file raises error on checksum mismatch."""
    mock_data = b"Mock file content"
    mock_hash = hashlib.md5(mock_data).hexdigest()
    wrong_hash = "00000000000000000000000000000000"
    
    dest_path = tmp_path / "test_download.txt"
    dest_path.write_bytes(mock_data)
    
    with patch('data.ingest_netflow.calculate_md5', return_value=mock_hash):
        with pytest.raises(ValueError, match="Checksum mismatch"):
            download_file("http://example.com/test.txt", str(dest_path), wrong_hash)

def test_load_state_missing_file(tmp_path, monkeypatch):
    """Test load_state when state file does not exist."""
    monkeypatch.chdir(tmp_path)
    state = load_state()
    
    assert state == {"artifact_hashes": {}, "dataset_info": {}}

def test_update_state(tmp_path, monkeypatch):
    """Test update_state function."""
    monkeypatch.chdir(tmp_path)
    
    # Ensure state file doesn't exist initially
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    
    download_ctu_dataset_url = "http://example.com/ctu.tar.gz"
    checksum = "abc123"
    
    from data.ingest_netflow import update_state
    update_state("test_dataset", download_ctu_dataset_url, "1.0", checksum)
    
    state = load_state()
    assert "test_dataset" in state["dataset_info"]
    assert state["dataset_info"]["test_dataset"]["url"] == download_ctu_dataset_url
    assert state["dataset_info"]["test_dataset"]["checksum"] == checksum
