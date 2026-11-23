"""
Unit tests for checksum verification functionality.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Import the module under test
from checksum_verification import (
    compute_sha256,
    scan_directory,
    load_existing_checksums,
    save_checksums,
    verify_data_integrity,
    update_checksums
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    # Create a subdirectory
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    
    # Create sample files
    file1 = temp_dir / "file1.txt"
    file1.write_text("Hello, World!")
    
    file2 = temp_dir / "file2.txt"
    file2.write_text("Test data")
    
    file3 = subdir / "file3.txt"
    file3.write_text("Nested file")
    
    return [file1, file2, file3]

def test_compute_sha256(sample_files):
    """Test SHA-256 computation for known content."""
    file_path = sample_files[0]
    expected_content = "Hello, World!"
    expected_hash = hashlib.sha256(expected_content.encode()).hexdigest()
    
    computed_hash = compute_sha256(file_path)
    assert computed_hash == expected_hash

def test_compute_sha256_nonexistent_file():
    """Test error handling for non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/file.txt"))

def test_scan_directory(temp_dir, sample_files):
    """Test directory scanning."""
    files = scan_directory(temp_dir)
    assert len(files) == 3
    assert all(f.exists() for f in files)

def test_scan_directory_with_extension(temp_dir, sample_files):
    """Test directory scanning with extension filter."""
    # Create a file with different extension
    (temp_dir / "file.xml").write_text("<xml></xml>")
    
    files = scan_directory(temp_dir, extensions=[".txt"])
    assert len(files) == 3
    assert all(f.suffix == ".txt" for f in files)

def test_scan_directory_nonexistent():
    """Test scanning non-existent directory."""
    files = scan_directory(Path("/nonexistent/directory"))
    assert files == []

def test_save_and_load_checksums(temp_dir):
    """Test saving and loading checksums."""
    checksum_file = temp_dir / "checksums.json"
    test_checksums = {
        "file1.txt": "abc123",
        "file2.txt": "def456"
    }
    
    save_checksums(test_checksums, checksum_file)
    loaded = load_existing_checksums(checksum_file)
    
    assert loaded == test_checksums

def test_load_nonexistent_checksums(temp_dir):
    """Test loading from non-existent checksum file."""
    checksum_file = temp_dir / "nonexistent.json"
    loaded = load_existing_checksums(checksum_file)
    assert loaded == {}

def test_verify_data_integrity_no_checksums(temp_dir, sample_files):
    """Test verification when no checksums exist."""
    # Create a temporary checksum file with no entries
    checksum_file = temp_dir / "checksums.json"
    save_checksums({}, checksum_file)
    
    # Mock the functions to use our temp dir
    import checksum_verification as cv
    original_checksum_file = cv.CHECKSUM_FILE
    cv.CHECKSUM_FILE = checksum_file
    
    try:
        is_valid, missing, corrupted = verify_data_integrity([temp_dir])
        assert is_valid
        assert len(missing) == 0
        assert len(corrupted) == 0
    finally:
        cv.CHECKSUM_FILE = original_checksum_file

def test_verify_data_integrity_corrupted_file(temp_dir, sample_files):
    """Test verification when a file is corrupted."""
    # Create initial checksums
    import checksum_verification as cv
    original_checksum_file = cv.CHECKSUM_FILE
    checksum_file = temp_dir / "checksums.json"
    cv.CHECKSUM_FILE = checksum_file
    
    try:
        # First, update checksums
        update_checksums([temp_dir])
        
        # Modify a file
        sample_files[0].write_text("Modified content")
        
        # Verify - should detect corruption
        is_valid, missing, corrupted = verify_data_integrity([temp_dir])
        assert not is_valid
        assert len(corrupted) == 1
        assert len(missing) == 0
    finally:
        cv.CHECKSUM_FILE = original_checksum_file

def test_verify_data_integrity_missing_file(temp_dir, sample_files):
    """Test verification when a file is missing."""
    import checksum_verification as cv
    original_checksum_file = cv.CHECKSUM_FILE
    checksum_file = temp_dir / "checksums.json"
    cv.CHECKSUM_FILE = checksum_file
    
    try:
        # First, update checksums
        update_checksums([temp_dir])
        
        # Delete a file
        sample_files[0].unlink()
        
        # Verify - should detect missing file
        is_valid, missing, corrupted = verify_data_integrity([temp_dir])
        assert not is_valid
        assert len(missing) == 1
        assert len(corrupted) == 0
    finally:
        cv.CHECKSUM_FILE = original_checksum_file
