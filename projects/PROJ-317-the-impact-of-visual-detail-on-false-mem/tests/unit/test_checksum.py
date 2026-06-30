"""
Unit tests for checksum utilities.
"""

import json
import tempfile
from pathlib import Path
import pytest

from code.data.checksum import (
    compute_sha256,
    compute_checksums_for_directory,
    save_checksum_manifest,
    load_checksum_manifest,
    verify_checksums_against_manifest,
    create_checksum_manifest_for_directory,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_files(temp_dir):
    """Create sample files with known content."""
    # Create test files
    (temp_dir / "file1.txt").write_text("Hello, World!")
    (temp_dir / "file2.txt").write_text("Test content 123")
    
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("Nested file content")
    
    return temp_dir

def test_compute_sha256_single_file(temp_dir):
    """Test computing SHA-256 for a single file."""
    test_file = temp_dir / "test.txt"
    test_content = "Test content for hashing"
    test_file.write_text(test_content)
    
    checksum = compute_sha256(test_file)
    
    # Verify it's a valid hex string of correct length
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)

def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/file.txt")

def test_compute_sha256_deterministic(temp_dir):
    """Test that same content produces same checksum."""
    test_file = temp_dir / "deterministic.txt"
    test_file.write_text("Deterministic content")
    
    checksum1 = compute_sha256(test_file)
    checksum2 = compute_sha256(test_file)
    
    assert checksum1 == checksum2

def test_compute_checksums_for_directory(sample_files):
    """Test computing checksums for all files in a directory."""
    checksums = compute_checksums_for_directory(sample_files, recursive=False)
    
    # Should find only file1.txt and file2.txt (not subdir contents)
    assert len(checksums) == 2
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums

def test_compute_checksums_recursive(sample_files):
    """Test recursive directory scanning."""
    checksums = compute_checksums_for_directory(sample_files, recursive=True)
    
    # Should find all 3 files
    assert len(checksums) == 3
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums
    assert "subdir/file3.txt" in checksums

def test_compute_checksums_with_extension_filter(sample_files):
    """Test filtering by file extension."""
    # Add a non-txt file
    (sample_files / "image.jpg").write_text("fake image data")
    
    checksums = compute_checksums_for_directory(
        sample_files,
        recursive=True,
        extensions=[".txt"]
    )
    
    # Should only find txt files
    assert len(checksums) == 3
    assert "image.jpg" not in checksums

def test_save_and_load_checksum_manifest(temp_dir):
    """Test saving and loading checksum manifest."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")
    
    checksums = {"test.txt": compute_sha256(test_file)}
    manifest_path = temp_dir / "manifest.json"
    
    save_checksum_manifest(checksums, manifest_path)
    
    assert manifest_path.exists()
    
    loaded = load_checksum_manifest(manifest_path)
    
    assert loaded == checksums

def test_load_checksum_manifest_not_found():
    """Test that FileNotFoundError is raised for missing manifest."""
    with pytest.raises(FileNotFoundError):
        load_checksum_manifest("/nonexistent/manifest.json")

def test_verify_checksums_all_valid(sample_files):
    """Test verification when all files are valid."""
    manifest_path = sample_files / "manifest.json"
    create_checksum_manifest_for_directory(sample_files, manifest_path, recursive=True)
    
    all_valid, results = verify_checksums_against_manifest(sample_files, manifest_path)
    
    assert all_valid is True
    for status in results.values():
        assert status == "valid"

def test_verify_checksums_with_modified_file(sample_files):
    """Test verification detects modified files."""
    manifest_path = sample_files / "manifest.json"
    create_checksum_manifest_for_directory(sample_files, manifest_path, recursive=True)
    
    # Modify a file
    (sample_files / "file1.txt").write_text("Modified content")
    
    all_valid, results = verify_checksums_against_manifest(sample_files, manifest_path)
    
    assert all_valid is False
    assert results["file1.txt"] == "invalid"

def test_verify_checksums_with_missing_file(sample_files):
    """Test verification detects missing files."""
    manifest_path = sample_files / "manifest.json"
    create_checksum_manifest_for_directory(sample_files, manifest_path, recursive=True)
    
    # Remove a file
    (sample_files / "file1.txt").unlink()
    
    all_valid, results = verify_checksums_against_manifest(sample_files, manifest_path)
    
    assert all_valid is False
    assert results["file1.txt"] == "missing"

def test_create_checksum_manifest_for_directory(sample_files):
    """Test creating a checksum manifest."""
    manifest_path = sample_files / "output_manifest.json"
    
    create_checksum_manifest_for_directory(
        sample_files,
        manifest_path,
        recursive=True
    )
    
    assert manifest_path.exists()
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    assert "version" in manifest
    assert manifest["version"] == "1.0"
    assert manifest["algorithm"] == "sha256"
    assert "checksums" in manifest
    assert len(manifest["checksums"]) == 3