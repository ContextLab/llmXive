import os
import json
import tempfile
import hashlib
import pytest
from pathlib import Path
import yaml

from code.data_loader import (
    compute_sha256,
    read_artifact_hashes,
    write_artifact_hashes,
    verify_checksum_local,
    validate_synthetic_data_integrity,
    ChecksumValidationError,
    FatalError
)

@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary state directory structure."""
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    return state_dir

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory with synthetic files."""
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    
    # Create a fake synthetic trajectory file
    fake_file = data_dir / "synthetic_trajectory_001.h5"
    fake_file.write_bytes(b"fake hdf5 content")
    
    return data_dir

def test_compute_sha256():
    """Test SHA-256 computation on a simple file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = f.name
    
    try:
        hash1 = compute_sha256(temp_path)
        hash2 = compute_sha256(temp_path)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    finally:
        os.unlink(temp_path)

def test_write_and_read_artifact_hashes(temp_state_dir):
    """Test writing and reading artifact hashes."""
    test_hashes = {
        "file1.h5": "abc123",
        "file2.h5": "def456"
    }
    
    # Write hashes
    write_artifact_hashes(test_hashes)
    
    # Read hashes
    read_hashes = read_artifact_hashes()
    assert read_hashes == test_hashes

def test_verify_checksum_local_success(temp_data_dir):
    """Test successful checksum verification."""
    file_path = temp_data_dir / "synthetic_trajectory_001.h5"
    expected_hash = compute_sha256(str(file_path))
    
    assert verify_checksum_local(str(file_path), expected_hash) is True

def test_verify_checksum_local_failure(temp_data_dir):
    """Test failed checksum verification."""
    file_path = temp_data_dir / "synthetic_trajectory_001.h5"
    wrong_hash = "0" * 64  # Invalid hash
    
    with pytest.raises(ChecksumValidationError):
        verify_checksum_local(str(file_path), wrong_hash)

def test_validate_synthetic_data_integrity_missing_state(temp_data_dir, temp_state_dir):
    """Test validation fails when no state file exists."""
    # Temporarily change state path
    import code.data_loader as dl
    original_path = dl.STATE_FILE_PATH
    dl.STATE_FILE_PATH = str(temp_state_dir / "nonexistent.yaml")
    
    try:
        with pytest.raises(FatalError):
            validate_synthetic_data_integrity()
    finally:
        dl.STATE_FILE_PATH = original_path

def test_validate_synthetic_data_integrity_missing_files(temp_state_dir):
    """Test validation when no synthetic files exist."""
    # Create state file with hashes but no actual files
    state_file = temp_state_dir / "PROJ-080-phase-transitions-in-amorphous-solids-un.yaml"
    state_data = {
        "artifact_hashes": {
            "synthetic_data": {
                "nonexistent.h5": "abc123"
            }
        }
    }
    with open(state_file, "w") as f:
        yaml.dump(state_data, f)
    
    # Temporarily change data path
    import code.data_loader as dl
    original_path = dl.DATA_RAW_DIR
    dl.DATA_RAW_DIR = str(temp_state_dir.parent.parent / "data" / "raw")
    
    try:
        # Should not raise error if no files found, just log warning
        validate_synthetic_data_integrity()
    finally:
        dl.DATA_RAW_DIR = original_path

def test_validate_synthetic_data_integrity_success(temp_data_dir, temp_state_dir):
    """Test successful validation of synthetic data."""
    # Create state file with correct hashes
    file_path = temp_data_dir / "synthetic_trajectory_001.h5"
    expected_hash = compute_sha256(str(file_path))
    
    state_file = temp_state_dir / "PROJ-080-phase-transitions-in-amorphous-solids-un.yaml"
    state_data = {
        "artifact_hashes": {
            "synthetic_data": {
                "synthetic_trajectory_001.h5": expected_hash
            }
        }
    }
    with open(state_file, "w") as f:
        yaml.dump(state_data, f)
    
    # Temporarily change paths
    import code.data_loader as dl
    original_state = dl.STATE_FILE_PATH
    original_data = dl.DATA_RAW_DIR
    
    dl.STATE_FILE_PATH = str(state_file)
    dl.DATA_RAW_DIR = str(temp_data_dir)
    
    try:
        # Should succeed without raising
        validate_synthetic_data_integrity()
    finally:
        dl.STATE_FILE_PATH = original_state
        dl.DATA_RAW_DIR = original_data
