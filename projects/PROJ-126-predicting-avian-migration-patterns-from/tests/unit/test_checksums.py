import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Import from config
from config import (
    calculate_sha256,
    generate_checksums_for_raw_data,
    save_checksums,
    verify_checksums,
    ensure_directories,
    DATA_RAW,
    PROJECT_ROOT
)

def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test data")
        temp_path = Path(f.name)
    
    try:
        hash_val = calculate_sha256(temp_path)
        expected = hashlib.sha256(b"test data").hexdigest()
        assert hash_val == expected
    finally:
        os.unlink(temp_path)

def test_ensure_directories():
    """Test that ensure_directories creates the required folders."""
    dirs = ensure_directories()
    for d in dirs:
        assert d.exists()

def test_generate_checksums_for_raw_data():
    """Test checksum generation with a known file."""
    # Create a temp file in data/raw
    test_file = DATA_RAW / "test_checksum.txt"
    test_file.write_text("checksum test content")
    
    try:
        checksums = generate_checksums_for_raw_data()
        assert "test_checksum.txt" in checksums
        assert len(checksums) == 1
        # Verify the hash is correct
        expected_hash = hashlib.sha256(b"checksum test content").hexdigest()
        assert checksums["test_checksum.txt"] == expected_hash
    finally:
        if test_file.exists():
            test_file.unlink()

def test_save_and_verify_checksums():
    """Test saving and verifying checksums."""
    test_file = DATA_RAW / "verify_test.txt"
    test_file.write_text("verify content")
    
    try:
        # Generate and save
        checksums = generate_checksums_for_raw_data()
        save_checksums(checksums)
        
        # Verify
        assert verify_checksums(checksums) is True
        
        # Modify file and check failure
        test_file.write_text("modified content")
        assert verify_checksums(checksums) is False
    finally:
        if test_file.exists():
            test_file.unlink()
