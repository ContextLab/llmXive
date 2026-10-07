"""
Unit tests for checksum utilities.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path

# Import the module
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.checksums import (
    compute_checksum,
    load_checksums,
    save_checksums,
    verify_checksum,
    FileChecksumError,
    get_checksum_store_path
)

def test_compute_checksum_valid_file():
    """Test computing checksum of a valid file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        # Compute checksum
        hash_val = compute_checksum(temp_path)
        assert len(hash_val) == 64  # SHA-256 hex length
        assert isinstance(hash_val, str)
    finally:
        os.unlink(temp_path)

def test_compute_checksum_nonexistent_file():
    """Test that computing checksum of non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_checksum("/nonexistent/path/file.txt")

def test_save_and_load_checksums():
    """Test saving and loading checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / ".checksums.json"
        
        # Mock the store path function if needed, or just test logic directly
        # Since get_checksum_store_path is fixed to project root, we test save/load logic
        data = {"file1.txt": "abc123", "file2.txt": "def456"}
        
        # Save to temp path
        save_checksums(data, store_path)
        
        # Load from temp path (we need to override the function or just read the file)
        # To properly test, we'll read the file directly
        with open(store_path, "r") as f:
            loaded = json.load(f)
        
        assert loaded == data

def test_verify_checksum_success():
    """Test successful checksum verification."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        hash_val = compute_checksum(temp_path)
        # Should not raise
        assert verify_checksum(temp_path, hash_val) is True
    finally:
        os.unlink(temp_path)

def test_verify_checksum_failure():
    """Test failed checksum verification."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        with pytest.raises(FileChecksumError):
            verify_checksum(temp_path, "wrong_hash_value")
    finally:
        os.unlink(temp_path)

def test_empty_file_checksum():
    """Test checksum of empty file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        # Create empty file
        temp_path = f.name

    try:
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        hash_val = compute_checksum(temp_path)
        assert hash_val == expected
    finally:
        os.unlink(temp_path)
