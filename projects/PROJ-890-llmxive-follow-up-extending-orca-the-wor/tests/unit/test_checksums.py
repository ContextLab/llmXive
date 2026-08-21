"""
Unit tests for checksum verification utilities.
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.checksums import (
    compute_file_checksum,
    generate_checksum_manifest,
    verify_checksums,
    get_all_files_in_directory,
    save_checksums,
    load_checksums
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test files
        (tmp_path / "file1.txt").write_text("Hello, World!")
        (tmp_path / "file2.txt").write_text("Test content 123")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("Nested file")
        
        yield tmp_path

def test_compute_file_checksum(temp_dir):
    """Test SHA256 checksum computation."""
    file_path = temp_dir / "file1.txt"
    checksum = compute_file_checksum(file_path)
    
    # Verify it's a valid hex string of correct length
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)
    
    # Verify against known value
    expected = hashlib.sha256(b"Hello, World!").hexdigest()
    assert checksum == expected

def test_compute_file_checksum_nonexistent():
    """Test checksum computation on nonexistent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("/nonexistent/file.txt"))

def test_get_all_files_in_directory(temp_dir):
    """Test file discovery in directory."""
    files = get_all_files_in_directory(temp_dir)
    
    assert len(files) == 3
    file_names = sorted([f.name for f in files])
    assert file_names == ["file1.txt", "file2.txt", "file3.txt"]

def test_get_all_files_in_directory_empty():
    """Test file discovery on empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = get_all_files_in_directory(Path(tmpdir))
        assert len(files) == 0

def test_generate_checksum_manifest(temp_dir):
    """Test manifest generation."""
    files = get_all_files_in_directory(temp_dir)
    manifest = generate_checksum_manifest(files, temp_dir)
    
    assert len(manifest) == 3
    assert "file1.txt" in manifest
    assert "subdir/file3.txt" in manifest
    
    # Verify checksums are valid
    for checksum in manifest.values():
        assert len(checksum) == 64

def test_verify_checksums_match(temp_dir):
    """Test verification when all checksums match."""
    files = get_all_files_in_directory(temp_dir)
    current_manifest = generate_checksum_manifest(files, temp_dir)
    
    # Use same manifest as stored
    all_valid, mismatches = verify_checksums(current_manifest, current_manifest)
    
    assert all_valid is True
    assert len(mismatches) == 0

def test_verify_checksums_mismatch(temp_dir):
    """Test verification when checksums don't match."""
    files = get_all_files_in_directory(temp_dir)
    current_manifest = generate_checksum_manifest(files, temp_dir)
    
    # Modify one checksum in stored manifest
    stored_manifest = current_manifest.copy()
    stored_manifest["file1.txt"] = "invalid_checksum_123456789012345678901234567890123456789012345678901234"
    
    all_valid, mismatches = verify_checksums(current_manifest, stored_manifest)
    
    assert all_valid is False
    assert len(mismatches) == 1
    assert "MISMATCH: file1.txt" in mismatches

def test_verify_checksums_missing_file(temp_dir):
    """Test verification when a file is missing."""
    files = get_all_files_in_directory(temp_dir)
    current_manifest = generate_checksum_manifest(files, temp_dir)
    
    # Remove one file from current manifest to simulate deletion
    stored_manifest = current_manifest.copy()
    del current_manifest["file1.txt"]
    
    all_valid, mismatches = verify_checksums(current_manifest, stored_manifest)
    
    assert all_valid is False
    assert len(mismatches) == 1
    assert "MISSING: file1.txt" in mismatches

def test_save_and_load_checksums(temp_dir):
    """Test saving and loading checksums to/from JSON."""
    files = get_all_files_in_directory(temp_dir)
    manifest = generate_checksum_manifest(files, temp_dir)
    
    # Save to temp file
    checksum_file = temp_dir / "test_checksums.json"
    save_checksums(manifest, checksum_file)
    
    # Load back
    loaded = load_checksums(checksum_file)
    
    assert loaded == manifest
    
    # Verify file structure
    with open(checksum_file, 'r') as f:
        data = json.load(f)
    assert "checksums" in data
    assert "version" in data
    assert data["version"] == "1.0"

def test_load_nonexistent_checksums():
    """Test loading from nonexistent file returns empty dict."""
    result = load_checksums(Path("/nonexistent/checksums.json"))
    assert result == {}