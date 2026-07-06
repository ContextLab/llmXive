"""
Integration tests for the download module (T014).
Tests the full download flow including checksum verification.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import requests

from code.download import run_download, _download_file, _fetch_zenodo_files, DownloadError
from code.config.env_config import EnvironmentConfig

# Mock data for testing
MOCK_ZENODO_RESPONSE = {
    "id": 123456,
    "files": [
        {
            "key": "test_trajectory_1.xyz",
            "links": {"self": "https://zenodo.org/api/records/123456/files/test_trajectory_1.xyz"},
            "checksum": "md5:d41d8cd98f00b204e9800998ecf8427e"
        },
        {
            "key": "test_trajectory_2.xyz",
            "links": {"self": "https://zenodo.org/api/records/123456/files/test_trajectory_2.xyz"},
            "checksum": "md5:098f6bcd4621d373cade4e832627b4f6"
        }
    ]
}

def mock_get(url, *args, **kwargs):
    """Mock requests.get to simulate Zenodo API and file download."""
    mock_response = MagicMock()
    
    if "api/records" in url:
        # Simulate metadata fetch
        mock_response.json.return_value = MOCK_ZENODO_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
    elif "files/test_trajectory" in url:
        # Simulate file download
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = [b"x" * 100]
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
    else:
        mock_response.raise_for_status = MagicMock(side_effect=requests.exceptions.HTTPError("404"))
    
    return mock_response

@pytest.fixture
def temp_env_config(tmp_path):
    """Set up a temporary environment config for the test."""
    # Create a mock config object
    config = EnvironmentConfig()
    config.data_dir = tmp_path / "data"
    config.raw_dir = config.data_dir / "raw"
    config.processed_dir = config.data_dir / "processed"
    config.state_dir = tmp_path / "state"
    config.zenodo_record_id = "123456"
    return config

@patch('code.download.get_config')
@patch('code.download.requests.get', side_effect=mock_get)
@patch('code.download.get_data_dir')
def test_run_download_success(mock_get_data_dir, mock_requests, mock_get_config, temp_env_config, tmp_path):
    """Test successful download and checksum verification."""
    # Setup paths
    raw_dir = temp_env_config.raw_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    mock_get_data_dir.return_value = temp_env_config.data_dir
    mock_get_config.return_value = {
        'zenodo_record_id': '123456'
    }
    
    # Run download
    result = run_download()
    
    # Assertions
    assert result['status'] != 'failed', f"Download failed: {result}"
    assert len(result['downloaded']) == 2
    assert 'test_trajectory_1.xyz' in result['downloaded']
    assert 'test_trajectory_2.xyz' in result['downloaded']
    assert len(result['failed']) == 0
    
    # Check files exist
    assert (raw_dir / "test_trajectory_1.xyz").exists()
    assert (raw_dir / "test_trajectory_2.xyz").exists()
    
    # Check manifest
    manifest_path = raw_dir / "manifest.json"
    assert manifest_path.exists()
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert "test_trajectory_1.xyz" in manifest["files"]

@patch('code.download.get_config')
@patch('code.download.requests.get', side_effect=mock_get)
@patch('code.download.get_data_dir')
def test_run_download_checksum_mismatch(mock_get_data_dir, mock_requests, mock_get_config, temp_env_config, tmp_path):
    """Test handling of checksum mismatch."""
    raw_dir = temp_env_config.raw_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    mock_get_data_dir.return_value = temp_env_config.data_dir
    mock_get_config.return_value = {
        'zenodo_record_id': '123456'
    }
    
    # Patch verify_file_integrity to return False
    with patch('code.download.verify_file_integrity', return_value=False):
        result = run_download()
    
    # Should fail to download due to checksum mismatch
    assert len(result['failed']) == 2
    assert len(result['downloaded']) == 0
    
    # Files should not exist (cleaned up)
    assert not (raw_dir / "test_trajectory_1.xyz").exists()
    assert not (raw_dir / "test_trajectory_2.xyz").exists()

@patch('code.download.get_config')
@patch('code.download.requests.get')
@patch('code.download.get_data_dir')
def test_run_download_missing_id(mock_get_data_dir, mock_requests, mock_get_config, temp_env_config, tmp_path):
    """Test error handling when Zenodo ID is missing."""
    mock_get_data_dir.return_value = temp_env_config.data_dir
    mock_get_config.return_value = {}  # No zenodo_record_id
    
    with pytest.raises(DownloadError, match="ZENODO_RECORD_ID not found"):
        run_download()
