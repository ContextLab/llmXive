"""
Contract tests for checksum file schema.

Validates that checksum files adhere to the expected schema structure.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
from src.data.checksums import compute_directory_checksums, save_checksums, CHECKSUM_FILE

def ensure_checksum_exists(temp_dir: Path) -> Path:
    """Create a test directory with a checksum file."""
    test_dir = temp_dir / "test_data"
    test_dir.mkdir()
    (test_dir / "test.txt").write_text("test content")
    
    checksums = compute_directory_checksums(test_dir)
    checksum_file = test_dir / CHECKSUM_FILE
    save_checksums(checksums, checksum_file)
    
    return checksum_file

def test_checksum_file_exists(tmp_path):
    """Test that a checksum file can be created."""
    checksum_file = ensure_checksum_exists(tmp_path)
    assert checksum_file.exists()

def test_checksum_schema_structure(tmp_path):
    """Test that checksum file has the required schema structure."""
    checksum_file = ensure_checksum_exists(tmp_path)
    
    with open(checksum_file, 'r') as f:
        data = json.load(f)
    
    # Check required top-level keys
    assert "checksums" in data
    assert "created_at" in data
    assert "algorithm" in data
    
    # Check algorithm is sha256
    assert data["algorithm"] == "sha256"
    
    # Check checksums is a dict
    assert isinstance(data["checksums"], dict)

def test_checksum_version_format(tmp_path):
    """Test that the created_at timestamp is in ISO format."""
    checksum_file = ensure_checksum_exists(tmp_path)
    
    with open(checksum_file, 'r') as f:
        data = json.load(f)
    
    from datetime import datetime
    # Should not raise
    datetime.fromisoformat(data["created_at"])

def test_checksum_entry_structure(tmp_path):
    """Test that each checksum entry is a valid hex string."""
    checksum_file = ensure_checksum_exists(tmp_path)
    
    with open(checksum_file, 'r') as f:
        data = json.load(f)
    
    for file_path, checksum in data["checksums"].items():
        # Check it's a string
        assert isinstance(checksum, str)
        # Check it's valid hex (SHA-256 is 64 chars)
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

def test_checksum_file_is_valid_json(tmp_path):
    """Test that the checksum file is valid JSON."""
    checksum_file = ensure_checksum_exists(tmp_path)
    
    # Should not raise
    with open(checksum_file, 'r') as f:
        json.load(f)

def test_checksum_file_excludes_itself(tmp_path):
    """Test that the checksum file is not included in its own checksums."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    (test_dir / "test.txt").write_text("test content")
    
    checksums = compute_directory_checksums(test_dir)
    checksum_file = test_dir / CHECKSUM_FILE
    save_checksums(checksums, checksum_file)
    
    # Reload and verify
    with open(checksum_file, 'r') as f:
        data = json.load(f)
    
    assert CHECKSUM_FILE not in data["checksums"]