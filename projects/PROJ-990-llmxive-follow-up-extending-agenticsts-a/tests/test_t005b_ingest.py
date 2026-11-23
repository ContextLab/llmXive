import os
import json
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from t005b_ingest_trajectories import (
    compute_sha256, 
    fetch_manifest, 
    download_real_data, 
    verify_checksum,
    main,
    BASE_URL,
    MANIFEST_URL,
    DATA_URL,
    RAW_DIR,
    MANIFEST_PATH,
    DATA_PATH
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path

def test_compute_sha256(temp_dir):
    """Test SHA256 computation on a small file."""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    expected_hash = hashlib.sha256(test_content).hexdigest()
    actual_hash = compute_sha256(test_file)
    
    assert actual_hash == expected_hash

@patch('t005b_ingest_trajectories.urllib.request.urlopen')
@patch('t005b_ingest_trajectories.RAW_DIR')
def test_fetch_manifest(mock_dir, mock_urlopen, temp_dir):
    """Test manifest fetching logic."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "version": "1.0.0",
        "checksums": {"test.jsonl": "abc123"}
    }).encode('utf-8')
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    mock_dir.__truediv__.return_value = temp_dir
    
    manifest = fetch_manifest()
    
    assert manifest["version"] == "1.0.0"
    assert "abc123" in manifest["checksums"].values()
    
    # Verify manifest was saved
    assert (temp_dir / "manifest.json").exists()

@patch('t005b_ingest_trajectories.urllib.request.urlopen')
@patch('t005b_ingest_trajectories.RAW_DIR')
def test_download_real_data(mock_dir, mock_urlopen, temp_dir):
    """Test data download logic."""
    mock_response = MagicMock()
    mock_response.headers.get.return_value = "100"
    mock_response.read.side_effect = [b"test data", b""]
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    mock_dir.__truediv__.return_value = temp_dir
    
    download_real_data()
    
    assert (temp_dir / "agenticsts_trajectories.jsonl").exists()
    assert (temp_dir / "agenticsts_trajectories.jsonl").read_bytes() == b"test data"

def test_verify_checksum_missing_file(temp_dir):
    """Test checksum verification with missing file."""
    mock_manifest = {
        "checksums": {"agenticsts_trajectories.jsonl": "abc123"}
    }
    
    # Ensure file doesn't exist
    data_path = temp_dir / "agenticsts_trajectories.jsonl"
    if data_path.exists():
        data_path.unlink()
    
    # Temporarily override DATA_PATH
    import t005b_ingest_trajectories
    original_path = t005b_ingest_trajectories.DATA_PATH
    t005b_ingest_trajectories.DATA_PATH = data_path
    
    try:
        result = verify_checksum(mock_manifest)
        assert result is False
    finally:
        t005b_ingest_trajectories.DATA_PATH = original_path

def test_verify_checksum_mismatch(temp_dir):
    """Test checksum verification with mismatch."""
    test_file = temp_dir / "agenticsts_trajectories.jsonl"
    test_file.write_bytes(b"test content")
    
    mock_manifest = {
        "checksums": {"agenticsts_trajectories.jsonl": "wrong_hash"}
    }
    
    # Temporarily override DATA_PATH
    import t005b_ingest_trajectories
    original_path = t005b_ingest_trajectories.DATA_PATH
    t005b_ingest_trajectories.DATA_PATH = test_file
    
    try:
        result = verify_checksum(mock_manifest)
        assert result is False
    finally:
        t005b_ingest_trajectories.DATA_PATH = original_path

def test_verify_checksum_match(temp_dir):
    """Test checksum verification with match."""
    test_file = temp_dir / "agenticsts_trajectories.jsonl"
    test_content = b"test content"
    test_file.write_bytes(test_content)
    
    correct_hash = hashlib.sha256(test_content).hexdigest()
    mock_manifest = {
        "checksums": {"agenticsts_trajectories.jsonl": correct_hash}
    }
    
    # Temporarily override DATA_PATH
    import t005b_ingest_trajectories
    original_path = t005b_ingest_trajectories.DATA_PATH
    t005b_ingest_trajectories.DATA_PATH = test_file
    
    try:
        result = verify_checksum(mock_manifest)
        assert result is True
    finally:
        t005b_ingest_trajectories.DATA_PATH = original_path

@patch('t005b_ingest_trajectories.fetch_manifest')
@patch('t005b_ingest_trajectories.download_real_data')
@patch('t005b_ingest_trajectories.verify_checksum')
def test_main_success(mock_verify, mock_download, mock_fetch, temp_dir):
    """Test main function success path."""
    mock_manifest = {"checksums": {"test": "hash"}}
    mock_fetch.return_value = mock_manifest
    mock_verify.return_value = True
    
    # Temporarily override paths
    import t005b_ingest_trajectories
    original_dir = t005b_ingest_trajectories.RAW_DIR
    original_data = t005b_ingest_trajectories.DATA_PATH
    
    t005b_ingest_trajectories.RAW_DIR = temp_dir
    t005b_ingest_trajectories.DATA_PATH = temp_dir / "agenticsts_trajectories.jsonl"
    
    try:
        main()
        mock_fetch.assert_called_once()
        mock_download.assert_called_once()
        mock_verify.assert_called_once()
    finally:
        t005b_ingest_trajectories.RAW_DIR = original_dir
        t005b_ingest_trajectories.DATA_PATH = original_data

@patch('t005b_ingest_trajectories.fetch_manifest')
@patch('t005b_ingest_trajectories.download_real_data')
@patch('t005b_ingest_trajectories.verify_checksum')
def test_main_checksum_failure(mock_verify, mock_download, mock_fetch, temp_dir):
    """Test main function with checksum failure."""
    mock_manifest = {"checksums": {"test": "hash"}}
    mock_fetch.return_value = mock_manifest
    mock_verify.return_value = False
    
    # Temporarily override paths
    import t005b_ingest_trajectories
    original_dir = t005b_ingest_trajectories.RAW_DIR
    original_data = t005b_ingest_trajectories.DATA_PATH
    
    t005b_ingest_trajectories.RAW_DIR = temp_dir
    t005b_ingest_trajectories.DATA_PATH = temp_dir / "agenticsts_trajectories.jsonl"
    
    try:
        with pytest.raises(FileNotFoundError, match="checksum verification failed"):
            main()
    finally:
        t005b_ingest_trajectories.RAW_DIR = original_dir
        t005b_ingest_trajectories.DATA_PATH = original_data
