"""
Unit tests for checksum validation functionality (Task T014).

Tests verify that:
1. Checksums are computed correctly
2. Manifests are saved and loaded properly
3. Integrity validation detects missing, new, and corrupted files
"""
import json
import tempfile
import os
from pathlib import Path
import pytest
from code.dataset.validate_checksums import (
    compute_file_checksum,
    generate_checksums_for_directory,
    save_checksums,
    load_checksums,
    validate_data_integrity,
    update_manifest
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with test files."""
    # Create test files with known content
    (tmp_path / "file1.txt").write_text("Hello, World!")
    (tmp_path / "file2.txt").write_text("Test data 123")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("Nested file content")
    return tmp_path

@pytest.fixture
def test_manifest(temp_dir):
    """Create a test manifest file."""
    checksums = generate_checksums_for_directory(temp_dir)
    manifest_path = temp_dir / "manifest.json"
    save_checksums(checksums, manifest_path)
    return manifest_path

def test_compute_file_checksum(temp_dir):
    """Test that checksum is computed correctly for a single file."""
    file_path = temp_dir / "file1.txt"
    checksum = compute_file_checksum(file_path)
    
    # Verify it's a valid SHA-256 hex string
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)
    
    # Verify determinism
    checksum2 = compute_file_checksum(file_path)
    assert checksum == checksum2

def test_compute_file_checksum_nonexistent():
    """Test that computing checksum on nonexistent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("/nonexistent/file.txt"))

def test_generate_checksums_for_directory(temp_dir):
    """Test checksum generation for all files in a directory."""
    checksums = generate_checksums_for_directory(temp_dir)
    
    # Should find all 3 files
    assert len(checksums) == 3
    
    # Verify keys are relative paths
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums
    assert "subdir/file3.txt" in checksums or "subdir\\file3.txt" in checksums

def test_generate_checksums_for_directory_nonexistent():
    """Test that generating checksums on nonexistent directory raises error."""
    with pytest.raises(FileNotFoundError):
        generate_checksums_for_directory(Path("/nonexistent/dir"))

def test_save_and_load_checksums(temp_dir):
    """Test saving and loading checksums from manifest."""
    checksums = generate_checksums_for_directory(temp_dir)
    manifest_path = temp_dir / "test_manifest.json"
    
    save_checksums(checksums, manifest_path)
    assert manifest_path.exists()
    
    loaded_checksums = load_checksums(manifest_path)
    assert loaded_checksums == checksums

def test_load_checksums_nonexistent():
    """Test that loading from nonexistent manifest raises error."""
    with pytest.raises(FileNotFoundError):
        load_checksums(Path("/nonexistent/manifest.json"))

def test_validate_data_integrity_passes(temp_dir, test_manifest):
    """Test that validation passes when files match manifest."""
    result = validate_data_integrity(temp_dir, test_manifest)
    
    assert result["valid"] is True
    assert result["missing_files"] == []
    assert result["new_files"] == []
    assert result["corrupted_files"] == []
    assert result["total_files_checked"] == 3

def test_validate_data_integrity_detects_missing_file(temp_dir, test_manifest):
    """Test that validation detects missing files."""
    # Remove a file
    (temp_dir / "file1.txt").unlink()
    
    result = validate_data_integrity(temp_dir, test_manifest)
    
    assert result["valid"] is False
    assert "file1.txt" in result["missing_files"]
    assert len(result["missing_files"]) == 1

def test_validate_data_integrity_detects_new_file(temp_dir, test_manifest):
    """Test that validation detects new files."""
    # Add a new file
    (temp_dir / "new_file.txt").write_text("New content")
    
    result = validate_data_integrity(temp_dir, test_manifest)
    
    assert result["valid"] is False
    assert "new_file.txt" in result["new_files"]
    assert len(result["new_files"]) == 1

def test_validate_data_integrity_detects_corrupted_file(temp_dir, test_manifest):
    """Test that validation detects corrupted files."""
    # Modify a file
    (temp_dir / "file1.txt").write_text("Modified content")
    
    result = validate_data_integrity(temp_dir, test_manifest)
    
    assert result["valid"] is False
    assert "file1.txt" in result["corrupted_files"]
    assert len(result["corrupted_files"]) == 1

def test_update_manifest(temp_dir):
    """Test that manifest update reflects current state."""
    manifest_path = temp_dir / "updated_manifest.json"
    
    # Initial manifest
    update_manifest(temp_dir, manifest_path)
    
    # Add new file
    (temp_dir / "added.txt").write_text("Added")
    
    # Update manifest
    update_manifest(temp_dir, manifest_path)
    
    # Verify new file is in manifest
    checksums = load_checksums(manifest_path)
    assert "added.txt" in checksums

def test_validate_data_integrity_empty_directory(tmp_path):
    """Test validation on empty directory."""
    manifest_path = tmp_path / "manifest.json"
    save_checksums({}, manifest_path)
    
    result = validate_data_integrity(tmp_path, manifest_path)
    
    assert result["valid"] is True
    assert result["total_files_checked"] == 0

def test_validate_data_integrity_nonexistent_raw_dir(tmp_path):
    """Test validation on nonexistent raw directory."""
    manifest_path = tmp_path / "manifest.json"
    save_checksums({}, manifest_path)
    
    with pytest.raises(FileNotFoundError):
        validate_data_integrity(tmp_path / "nonexistent", manifest_path)