import os
import tempfile
import hashlib
import pytest
from pathlib import Path

from code.checksum_verify import (
    compute_sha256,
    ensure_raw_directory,
    load_checksums,
    save_checksums,
    verify_file,
    compute_and_store_checksum,
    store_all,
    DATA_RAW_DIR,
    STATE_FILE
)

def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    content = b"Hello, World!"
    expected_hash = hashlib.sha256(content).hexdigest()
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        actual_hash = compute_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_ensure_raw_directory():
    """Test that ensure_raw_directory creates the directory if missing."""
    # Remove if exists (for test isolation)
    if os.path.exists(DATA_RAW_DIR):
        # Don't remove if it's a real project directory in dev
        # Just ensure it exists
        pass
    
    ensure_raw_directory()
    assert os.path.isdir(DATA_RAW_DIR)

def test_load_save_checksums():
    """Test loading and saving checksums to state file."""
    test_checksums = {"test_file.jsonl": "abc123", "another.txt": "def456"}
    
    # Save
    save_checksums(test_checksums)
    
    # Load
    loaded = load_checksums()
    
    assert "test_file.jsonl" in loaded
    assert loaded["test_file.jsonl"] == "abc123"
    assert loaded["another.txt"] == "def456"

def test_verify_file():
    """Test file verification."""
    content = b"Verification test data"
    expected_hash = hashlib.sha256(content).hexdigest()
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # Should pass
        assert verify_file(temp_path, expected_hash) is True
        
        # Should fail
        assert verify_file(temp_path, "wrong_hash") is False
    finally:
        os.unlink(temp_path)

def test_compute_and_store_checksum():
    """Test computing and storing a checksum."""
    content = b"Test content for storage"
    
    with tempfile.NamedTemporaryFile(delete=False, dir=DATA_RAW_DIR) as f:
        f.write(content)
        temp_path = f.name
    
    file_name = os.path.basename(temp_path)
    expected_hash = hashlib.sha256(content).hexdigest()
    
    try:
        # Compute and store
        stored_hash = compute_and_store_checksum(temp_path)
        assert stored_hash == expected_hash
        
        # Verify it's in state
        checksums = load_checksums()
        assert file_name in checksums
        assert checksums[file_name] == expected_hash
    finally:
        os.unlink(temp_path)

def test_store_all():
    """Test storing checksums for all files in data/raw/."""
    # Create a test file
    test_content = b"Store all test"
    test_file = os.path.join(DATA_RAW_DIR, "store_all_test.jsonl")
    
    with open(test_file, "wb") as f:
        f.write(test_content)
    
    try:
        # Store all
        store_all()
        
        # Verify
        checksums = load_checksums()
        assert "store_all_test.jsonl" in checksums
        assert checksums["store_all_test.jsonl"] == hashlib.sha256(test_content).hexdigest()
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
