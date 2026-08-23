import os
import json
import hashlib
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Import the module under test using the API surface
from download import (
    download_subject_data,
    compute_sha256_file,
    verify_checksum,
    check_hcp_availability
)
from config import ensure_dirs

# Fixtures
@pytest.fixture
def mock_raw_dir(tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    # Create a mock checksum file
    checksums = {
        "sub-123_dwi.trk": "abc123",
        "sub-123_rsfmri.nii.gz": "def456"
    }
    checksum_file = raw_dir / ".checksums.json"
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f)
    return raw_dir

@pytest.fixture
def mock_config(tmp_path):
    # Ensure config paths point to our temp directory
    with patch('config.DATA_RAW_DIR', str(tmp_path / "data" / "raw")):
        yield

def test_download_subject_data_returns_dict(mock_raw_dir, mock_config):
    """Contract: Verify download_subject_data returns a dict with expected keys."""
    subject_id = "sub-123"
    
    # Mock the actual download to avoid network calls
    with patch('download.download_file') as mock_dl:
        mock_dl.return_value = str(mock_raw_dir / f"{subject_id}_dwi.trk")
        
        # Create dummy files to simulate download
        (mock_raw_dir / f"{subject_id}_dwi.trk").touch()
        (mock_raw_dir / f"{subject_id}_rsfmri.nii.gz").touch()
        
        result = download_subject_data(subject_id)
        
        assert isinstance(result, dict)
        assert 'dwi_path' in result
        assert 'rsfmri_path' in result
        assert os.path.exists(result['dwi_path'])
        assert os.path.exists(result['rsfmri_path'])

def test_download_subject_data_raises_file_not_found(mock_raw_dir, mock_config):
    """Contract: Verify FileNotFoundError is raised if files are missing."""
    subject_id = "sub-999"
    
    with patch('download.download_file') as mock_dl:
        mock_dl.side_effect = FileNotFoundError("Simulated missing file")
        
        with pytest.raises(FileNotFoundError):
            download_subject_data(subject_id)

def test_compute_sha256_file(mock_raw_dir):
    """Verify SHA256 computation on a real file."""
    test_file = mock_raw_dir / "test.txt"
    test_content = b"test content for hashing"
    test_file.write_bytes(test_content)
    
    computed_hash = compute_sha256_file(str(test_file))
    
    # Expected hash for "test content for hashing"
    expected_hash = hashlib.sha256(test_content).hexdigest()
    
    assert computed_hash == expected_hash

def test_verify_checksum_success(mock_raw_dir):
    """Verify checksum validation passes for matching files."""
    test_file = mock_raw_dir / "test.txt"
    test_content = b"valid content"
    test_file.write_bytes(test_content)
    
    correct_hash = hashlib.sha256(test_content).hexdigest()
    
    assert verify_checksum(str(test_file), correct_hash) is True

def test_verify_checksum_failure(mock_raw_dir):
    """Verify checksum validation fails for mismatched files."""
    test_file = mock_raw_dir / "test.txt"
    test_file.write_bytes(b"content")
    
    wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    
    assert verify_checksum(str(test_file), wrong_hash) is False

def test_check_hcp_availability_success():
    """Verify HCP availability check returns True for valid bucket."""
    # Mock the boto3 client to avoid actual AWS calls
    with patch('download.boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_client.head_object.return_value = {'ContentLength': 100}
        mock_boto.return_value = mock_client
        
        # This should return True without raising
        result = check_hcp_availability("sub-123", "dwi")
        assert result is True

def test_check_hcp_availability_failure():
    """Verify HCP availability check returns False for missing data."""
    with patch('download.boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_client.head_object.side_effect = Exception("Not found")
        mock_boto.return_value = mock_client
        
        result = check_hcp_availability("sub-999", "dwi")
        assert result is False
