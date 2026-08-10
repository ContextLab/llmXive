"""
Unit tests for the checksum utility module.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.checksum import (
    compute_file_sha256,
    compute_directory_checksums,
    verify_checksum,
    save_checksums,
    load_checksums,
    verify_directory_against_checksums
)
from utils.logging import setup_logging

# Setup logging for tests
setup_logging(level="DEBUG")

@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create test files
        (tmppath / "file1.txt").write_text("Hello, World!")
        (tmppath / "file2.txt").write_text("Test content for checksum verification.")
        (tmppath / "subdir").mkdir()
        (tmppath / "subdir" / "file3.txt").write_text("Nested file content.")
        
        yield tmppath

def test_compute_file_sha256(temp_dir):
    """Test SHA-256 computation for a single file."""
    file_path = temp_dir / "file1.txt"
    checksum = compute_file_sha256(file_path)
    
    # Verify against known value
    expected = hashlib.sha256(b"Hello, World!").hexdigest()
    assert checksum == expected
    assert len(checksum) == 64  # SHA-256 hex string length
    
def test_compute_file_sha256_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_file_sha256("/nonexistent/file.txt")
        
def test_compute_file_sha256_not_file(temp_dir):
    """Test that ValueError is raised for directory path."""
    with pytest.raises(ValueError):
        compute_file_sha256(temp_dir)
        
def test_compute_directory_checksums(temp_dir):
    """Test checksum computation for a directory."""
    checksums = compute_directory_checksums(temp_dir)
    
    assert len(checksums) == 3  # file1.txt, file2.txt, subdir/file3.txt
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums
    assert "subdir/file3.txt" in checksums
    
    # Verify all are valid hex strings
    for checksum in checksums.values():
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)
        
def test_compute_directory_checksums_not_found():
    """Test error handling for non-existent directory."""
    with pytest.raises(FileNotFoundError):
        compute_directory_checksums("/nonexistent/dir")
        
def test_compute_directory_checksums_extensions(temp_dir):
    """Test filtering by file extension."""
    # Create a .csv file
    (temp_dir / "data.csv").write_text("a,b,c")
    
    checksums = compute_directory_checksums(
        temp_dir,
        extensions=[".txt"]
    )
    
    assert len(checksums) == 3  # Only .txt files
    assert "data.csv" not in checksums
    
    checksums_all = compute_directory_checksums(
        temp_dir,
        extensions=None
    )
    assert len(checksums_all) == 4  # All files
    
def test_verify_checksum_success(temp_dir):
    """Test successful checksum verification."""
    file_path = temp_dir / "file1.txt"
    checksum = compute_file_sha256(file_path)
    
    assert verify_checksum(file_path, checksum) is True
    
def test_verify_checksum_failure(temp_dir):
    """Test failed checksum verification."""
    file_path = temp_dir / "file1.txt"
    checksum = compute_file_sha256(file_path)
    
    # Modify checksum slightly
    wrong_checksum = checksum[:-1] + ("1" if checksum[-1] != "1" else "2")
    
    assert verify_checksum(file_path, wrong_checksum) is False
    
def test_verify_checksum_not_found():
    """Test verification of non-existent file."""
    assert verify_checksum("/nonexistent/file.txt", "abc123") is False
    
def test_save_and_load_checksums(temp_dir):
    """Test saving and loading checksums from JSON."""
    checksums = compute_directory_checksums(temp_dir)
    
    output_path = temp_dir / "checksums.json"
    save_checksums(checksums, output_path)
    
    # Verify file exists
    assert output_path.exists()
    
    # Load and verify
    loaded = load_checksums(output_path)
    assert loaded == checksums
    
def test_save_checksums_creates_directories(temp_dir):
    """Test that save_checksums creates parent directories."""
    checksums = {"file.txt": "abc123"}
    output_path = temp_dir / "nested" / "deep" / "checksums.json"
    
    save_checksums(checksums, output_path)
    assert output_path.exists()
    
def test_load_checksums_not_found():
    """Test error handling for missing checksum file."""
    with pytest.raises(FileNotFoundError):
        load_checksums("/nonexistent/checksums.json")
        
def test_load_checksums_invalid_json(temp_dir):
    """Test error handling for invalid JSON."""
    invalid_path = temp_dir / "invalid.json"
    invalid_path.write_text("not valid json {")
    
    with pytest.raises(json.JSONDecodeError):
        load_checksums(invalid_path)
        
def test_load_checksums_missing_key(temp_dir):
    """Test error handling for missing 'checksums' key."""
    invalid_path = temp_dir / "invalid.json"
    invalid_path.write_text('{"version": "1.0"}')
    
    with pytest.raises(ValueError):
        load_checksums(invalid_path)
        
def test_verify_directory_against_checksums(temp_dir):
    """Test directory verification against stored checksums."""
    checksums = compute_directory_checksums(temp_dir)
    
    results = verify_directory_against_checksums(temp_dir, checksums)
    
    assert len(results) == len(checksums)
    assert all(results.values())  # All should be valid
    
def test_verify_directory_with_missing_file(temp_dir):
    """Test verification when a file is missing."""
    checksums = compute_directory_checksums(temp_dir)
    
    # Remove a file
    (temp_dir / "file1.txt").unlink()
    
    results = verify_directory_against_checksums(temp_dir, checksums)
    
    assert results["file1.txt"] is False
    assert results["file2.txt"] is True
    
def test_verify_directory_with_modified_file(temp_dir):
    """Test verification when a file is modified."""
    checksums = compute_directory_checksums(temp_dir)
    
    # Modify a file
    (temp_dir / "file1.txt").write_text("Modified content")
    
    results = verify_directory_against_checksums(temp_dir, checksums)
    
    assert results["file1.txt"] is False
    assert results["file2.txt"] is True