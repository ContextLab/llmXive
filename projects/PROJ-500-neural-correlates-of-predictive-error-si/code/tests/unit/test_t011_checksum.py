"""
Unit tests for the checksum utility module (T011).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from src.utils.checksum import (
    compute_file_sha256,
    compute_directory_checksums,
    save_checksum_manifest,
    load_checksum_manifest,
    verify_checksums,
    generate_and_save_manifest
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test files
        (tmp_path / "file1.txt").write_text("Hello, World!")
        (tmp_path / "file2.json").write_text('{"key": "value"}')
        
        # Create subdirectory with files
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("Nested content")
        
        # Create a hidden file (should be ignored by default)
        (tmp_path / ".hidden").write_text("Hidden")
        
        yield tmp_path


def test_compute_file_sha256(temp_dir):
    """Test SHA-256 computation for a single file."""
    file_path = temp_dir / "file1.txt"
    checksum = compute_file_sha256(file_path)
    
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex length
    assert checksum.islower()
    assert all(c in '0123456789abcdef' for c in checksum)


def test_compute_file_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_file_sha256(Path("/nonexistent/file.txt"))


def test_compute_directory_checksums(temp_dir):
    """Test directory checksum computation."""
    checksums = compute_directory_checksums(temp_dir)
    
    assert isinstance(checksums, dict)
    assert len(checksums) == 3  # file1.txt, file2.json, subdir/file3.txt
    assert "file1.txt" in checksums
    assert "file2.json" in checksums
    assert "subdir/file3.txt" in checksums
    assert ".hidden" not in checksums  # Hidden files should be ignored


def test_compute_directory_checksums_with_extension_filter(temp_dir):
    """Test directory checksum with extension filter."""
    checksums = compute_directory_checksums(temp_dir, extensions=[".txt"])
    
    assert len(checksums) == 2  # Only .txt files
    assert "file1.txt" in checksums
    assert "subdir/file3.txt" in checksums
    assert "file2.json" not in checksums


def test_save_and_load_checksum_manifest(temp_dir):
    """Test saving and loading checksum manifest."""
    checksums = compute_directory_checksums(temp_dir)
    manifest_path = temp_dir / "manifest.json"
    
    save_checksum_manifest(checksums, manifest_path, temp_dir)
    
    assert manifest_path.exists()
    
    loaded_checksums, source_dir = load_checksum_manifest(manifest_path)
    
    assert loaded_checksums == checksums
    assert source_dir == temp_dir


def test_verify_checksums_success(temp_dir):
    """Test successful checksum verification."""
    checksums = compute_directory_checksums(temp_dir)
    manifest_path = temp_dir / "manifest.json"
    
    save_checksum_manifest(checksums, manifest_path, temp_dir)
    
    all_valid, passed, failed = verify_checksums(manifest_path, temp_dir)
    
    assert all_valid is True
    assert len(passed) == len(checksums)
    assert len(failed) == 0


def test_verify_checksums_failure(temp_dir):
    """Test verification failure when checksums mismatch."""
    checksums = compute_directory_checksums(temp_dir)
    manifest_path = temp_dir / "manifest.json"
    
    save_checksum_manifest(checksums, manifest_path, temp_dir)
    
    # Modify a file to cause mismatch
    (temp_dir / "file1.txt").write_text("Modified content")
    
    all_valid, passed, failed = verify_checksums(manifest_path, temp_dir)
    
    assert all_valid is False
    assert len(failed) == 1
    assert "file1.txt" in failed[0]


def test_verify_checksums_missing_file(temp_dir):
    """Test verification failure when a file is missing."""
    checksums = compute_directory_checksums(temp_dir)
    manifest_path = temp_dir / "manifest.json"
    
    save_checksum_manifest(checksums, manifest_path, temp_dir)
    
    # Delete a file
    (temp_dir / "file1.txt").unlink()
    
    all_valid, passed, failed = verify_checksums(manifest_path, temp_dir)
    
    assert all_valid is False
    assert len(failed) == 1
    assert "MISSING" in failed[0]


def test_generate_and_save_manifest(temp_dir):
    """Test the combined generate and save function."""
    manifest_path = temp_dir / "generated_manifest.json"
    
    checksums = generate_and_save_manifest(temp_dir, manifest_path)
    
    assert manifest_path.exists()
    assert len(checksums) == 3
    
    # Verify the manifest content
    with open(manifest_path) as f:
        manifest_data = json.load(f)
    
    assert manifest_data["version"] == "1.0"
    assert manifest_data["algorithm"] == "sha256"
    assert "source_directory" in manifest_data
    assert len(manifest_data["checksums"]) == 3