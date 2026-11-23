import os
import yaml
import pytest
from pathlib import Path
from code.env_config import (
    compute_file_hash, 
    store_hash_in_state, 
    read_hash_from_state, 
    verify_source_integrity,
    STATE_FILE,
    DATASET_HF_ID
)
import tempfile
import hashlib

@pytest.fixture
def temp_state_dir(tmp_path):
    # Override the global STATE_FILE for testing
    global STATE_FILE
    original_state_file = STATE_FILE
    test_state_file = tmp_path / "test_state.yaml"
    STATE_FILE = test_state_file
    yield test_state_file
    STATE_FILE = original_state_file

@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / "test_data.bin"
    content = b"Hello, World! This is a test file."
    file_path.write_bytes(content)
    return file_path

def test_compute_file_hash(temp_file):
    expected_hash = hashlib.sha256(b"Hello, World! This is a test file.").hexdigest()
    computed_hash = compute_file_hash(temp_file)
    assert computed_hash == expected_hash

def test_store_and_read_hash(temp_state_dir):
    test_hash = "abc123def456"
    store_hash_in_state(DATASET_HF_ID, test_hash)
    
    assert STATE_FILE.exists()
    with open(STATE_FILE, "r") as f:
        state_data = yaml.safe_load(f)
    
    assert "artifact_hashes" in state_data
    assert DATASET_HF_ID in state_data["artifact_hashes"]
    assert state_data["artifact_hashes"][DATASET_HF_ID]["hash"] == test_hash

    read_hash = read_hash_from_state(DATASET_HF_ID)
    assert read_hash == test_hash

def test_verify_source_integrity_success(temp_file):
    computed_hash = compute_file_hash(temp_file)
    assert verify_source_integrity(temp_file, computed_hash) is True

def test_verify_source_integrity_failure(temp_file):
    with pytest.raises(ValueError, match="Hash mismatch"):
        verify_source_integrity(temp_file, "wrong_hash")

def test_verify_source_integrity_no_expected_hash(temp_file, temp_state_dir):
    # When no expected hash is provided, it should store the computed one
    result = verify_source_integrity(temp_file)
    assert result is True
    
    # Verify it was stored
    stored_hash = read_hash_from_state(DATASET_HF_ID)
    computed_hash = compute_file_hash(temp_file)
    assert stored_hash == computed_hash

def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        verify_source_integrity(Path("non_existent_file.txt"))
