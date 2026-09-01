"""
Tests for the checksum utilities.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
from src.data.checksums import (
    compute_file_checksum,
    compute_directory_checksums,
    save_checksums,
    load_checksums,
    verify_checksums,
    generate_checksums_for_directories,
    verify_all_checksums,
    CHECKSUM_FILE
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # Create directory structure
        raw_dir = base / "raw"
        processed_dir = base / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        # Create test files
        (raw_dir / "file1.txt").write_text("Hello World")
        (raw_dir / "file2.csv").write_text("a,b,c\n1,2,3")
        (processed_dir / "output.json").write_text('{"key": "value"}')
        
        # Create a .gitkeep file (should be excluded)
        (raw_dir / ".gitkeep").write_text("")
        
        yield base

def test_compute_file_checksum(temp_data_dir):
    """Test computing checksum of a single file."""
    file_path = temp_data_dir / "raw" / "file1.txt"
    checksum = compute_file_checksum(file_path)
    
    assert len(checksum) == 64  # SHA-256 hex length
    assert isinstance(checksum, str)
    
    # Verify consistency
    checksum2 = compute_file_checksum(file_path)
    assert checksum == checksum2

def test_save_and_load_checksums(temp_data_dir):
    """Test saving and loading checksums to/from JSON."""
    checksums = {"file1.txt": "abc123", "file2.txt": "def456"}
    output_path = temp_data_dir / "test_checksums.json"
    
    save_checksums(checksums, output_path)
    
    assert output_path.exists()
    
    loaded = load_checksums(output_path)
    assert loaded == checksums

def test_save_checksums_excludes_itself(temp_data_dir):
    """Test that save_checksums doesn't include itself in the checksum file."""
    raw_dir = temp_data_dir / "raw"
    checksum_file = raw_dir / CHECKSUM_FILE
    
    checksums = compute_directory_checksums(raw_dir)
    save_checksums(checksums, checksum_file)
    
    # Reload and verify the checksum file is not in the list
    loaded = load_checksums(checksum_file)
    assert CHECKSUM_FILE not in loaded

def test_verify_checksums_valid(temp_data_dir):
    """Test verifying valid checksums."""
    raw_dir = temp_data_dir / "raw"
    checksums = compute_directory_checksums(raw_dir)
    
    results = verify_checksums(raw_dir, checksums)
    
    assert all(results.values())
    assert len(results) > 0

def test_verify_checksums_modified_file(temp_data_dir):
    """Test verifying checksums with a modified file."""
    raw_dir = temp_data_dir / "raw"
    file_path = raw_dir / "file1.txt"
    
    # Get original checksums
    original_checksums = compute_directory_checksums(raw_dir)
    
    # Modify the file
    file_path.write_text("Modified content")
    
    # Verify - should fail for the modified file
    results = verify_checksums(raw_dir, original_checksums)
    
    assert results["file1.txt"] is False
    assert results["file2.csv"] is True

def test_verify_checksums_missing_file(temp_data_dir):
    """Test verifying checksums with a missing file."""
    raw_dir = temp_data_dir / "raw"
    checksums = compute_directory_checksums(raw_dir)
    
    # Remove a file
    (raw_dir / "file1.txt").unlink()
    
    results = verify_checksums(raw_dir, checksums)
    
    assert results["file1.txt"] is False

def test_verify_checksums_no_stored(temp_data_dir):
    """Test verifying with empty stored checksums."""
    raw_dir = temp_data_dir / "raw"
    
    results = verify_checksums(raw_dir, {})
    
    assert len(results) == 0

def test_get_checksum_file_path(temp_data_dir):
    """Test that checksum file is created in the correct location."""
    raw_dir = temp_data_dir / "raw"
    checksums = compute_directory_checksums(raw_dir)
    checksum_file = raw_dir / CHECKSUM_FILE
    
    save_checksums(checksums, checksum_file)
    
    assert checksum_file.exists()
    
    # Verify the file is a valid JSON with the expected structure
    with open(checksum_file, 'r') as f:
        data = json.load(f)
    
    assert "checksums" in data
    assert "created_at" in data
    assert "algorithm" in data

def test_compute_directory_checksums_excludes_patterns(temp_data_dir):
    """Test that directory checksums exclude specified patterns."""
    raw_dir = temp_data_dir / "raw"
    checksums = compute_directory_checksums(raw_dir)
    
    # .gitkeep should be excluded
    assert ".gitkeep" not in checksums
    
    # Regular files should be included
    assert "file1.txt" in checksums
    assert "file2.csv" in checksums
