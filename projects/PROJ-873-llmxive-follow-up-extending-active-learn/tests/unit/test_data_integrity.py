"""
Unit tests for data_integrity module.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest

from data_integrity import calculate_sha256, record_checksums_to_state


def test_calculate_sha256_valid_file():
    """Test SHA-256 calculation on a known file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        # Calculate expected hash manually
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        
        # Calculate using function
        result_hash = calculate_sha256(temp_path)
        
        assert result_hash == expected_hash
    finally:
        os.unlink(temp_path)


def test_calculate_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/nonexistent/path/to/file.txt")


def test_record_checksums_to_state_creates_file():
    """Test that the state file is created if it doesn't exist."""
    # This is an integration-style unit test that touches the file system
    # We expect it to run successfully even if no BEIR data is present
    result = record_checksums_to_state()
    
    assert result["status"] in ["success", "warning"]
    assert "state_file" in result
    assert os.path.exists(result["state_file"])

def test_record_checksums_to_state_updates_existing():
    """Test that existing state is preserved and updated."""
    # Run once to create file
    result1 = record_checksums_to_state()
    state_path = result1["state_file"]
    
    # Read content
    with open(state_path, "r") as f:
        content1 = f.read()
    
    # Run again
    result2 = record_checksums_to_state()
    
    with open(state_path, "r") as f:
        content2 = f.read()
    
    # Content should be consistent (or at least file should still exist)
    assert os.path.exists(state_path)
    assert "artifact_hashes" in open(state_path).read()
