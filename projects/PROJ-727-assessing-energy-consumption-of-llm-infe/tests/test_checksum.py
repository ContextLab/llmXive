import os
import tempfile
import yaml
from pathlib import Path
import pytest

from code.checksum_verify import (
    compute_sha256,
    ensure_raw_directory,
    load_checksums,
    save_checksums,
    verify_file,
    compute_and_store_checksum,
)
from code.config import DATA_RAW_DIR, STATE_FILE

@pytest.fixture
def temp_state_file(tmp_path):
    """Create a temporary state file for testing."""
    state_file = tmp_path / "state.yaml"
    state_file.write_text("artifact_hashes: {}\n")
    return str(state_file)

@pytest.fixture
def temp_raw_dir(tmp_path):
    """Create a temporary raw directory for testing."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return str(raw_dir)

def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test data")
        temp_path = f.name
    
    try:
        # Known SHA-256 for "test data"
        expected_hash = "39a7299387e8b8f441f97d0b9d632c99412744482e54916723d716690c19050d"
        actual_hash = compute_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_ensure_raw_directory():
    """Test that ensure_raw_directory creates the directory."""
    # This test assumes DATA_RAW_DIR is a valid path
    ensure_raw_directory()
    assert os.path.exists(DATA_RAW_DIR)

def test_load_save_checksums(temp_state_file):
    """Test loading and saving checksums."""
    # Temporarily override STATE_FILE for testing
    import code.checksum_verify
    original_state_file = code.checksum_verify.STATE_FILE
    code.checksum_verify.STATE_FILE = temp_state_file
    
    try:
        checksums = {"test.txt": "abc123"}
        save_checksums(checksums)
        
        loaded = load_checksums()
        assert loaded == checksums
    finally:
        code.checksum_verify.STATE_FILE = original_state_file

def test_verify_file():
    """Test file verification."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test data")
        temp_path = f.name
    
    try:
        # Correct hash
        correct_hash = compute_sha256(temp_path)
        assert verify_file(temp_path, correct_hash)
        
        # Incorrect hash
        assert not verify_file(temp_path, "wrong_hash")
        
        # Non-existent file
        assert not verify_file("non_existent_file.txt", "any_hash")
    finally:
        os.unlink(temp_path)

def test_compute_and_store_checksum(temp_state_file, temp_raw_dir):
    """Test computing and storing a checksum."""
    # Create a test file
    test_file = os.path.join(temp_raw_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("test content")
    
    # Temporarily override constants for testing
    import code.checksum_verify
    original_state_file = code.checksum_verify.STATE_FILE
    original_data_raw_dir = code.checksum_verify.DATA_RAW_DIR
    
    code.checksum_verify.STATE_FILE = temp_state_file
    code.checksum_verify.DATA_RAW_DIR = temp_raw_dir
    
    try:
        checksum = compute_and_store_checksum(test_file, "test.txt")
        
        # Verify the checksum was stored
        checksums = load_checksums()
        assert "test.txt" in checksums
        assert checksums["test.txt"] == checksum
        
        # Verify the checksum matches
        assert compute_sha256(test_file) == checksum
    finally:
        code.checksum_verify.STATE_FILE = original_state_file
        code.checksum_verify.DATA_RAW_DIR = original_data_raw_dir
