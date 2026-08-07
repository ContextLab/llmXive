"""
Unit tests for archive_utils module (T005d).
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import hashlib

from src.data.archive_utils import (
    compute_sha256,
    archive_data,
    verify_archive_integrity,
    generate_checksum_manifest
)


@pytest.fixture
def temp_dirs():
    """Create temporary source and archive directories for testing."""
    with tempfile.TemporaryDirectory() as temp_base:
        source_dir = Path(temp_base) / "source"
        archive_dir = Path(temp_base) / "archive"
        source_dir.mkdir()
        archive_dir.mkdir()
        yield source_dir, archive_dir


def test_compute_sha256_basic(temp_dirs):
    """Test basic SHA-256 computation."""
    source_dir, _ = temp_dirs
    
    # Create a test file with known content
    test_file = source_dir / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_sha256(test_file)
    
    assert actual_hash == expected_hash


def test_compute_sha256_file_not_found(temp_dirs):
    """Test that FileNotFoundError is raised for missing files."""
    source_dir, _ = temp_dirs
    
    non_existent_file = source_dir / "nonexistent.txt"
    
    with pytest.raises(FileNotFoundError):
        compute_sha256(non_existent_file)


def test_compute_sha256_large_file(temp_dirs):
    """Test SHA-256 computation on a larger file."""
    source_dir, _ = temp_dirs
    
    # Create a larger file (1MB)
    large_file = source_dir / "large.bin"
    content = b"X" * (1024 * 1024)
    large_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_sha256(large_file)
    
    assert actual_hash == expected_hash


def test_archive_data_basic(temp_dirs):
    """Test basic archiving functionality."""
    source_dir, archive_dir = temp_dirs
    
    # Create test files
    (source_dir / "file1.txt").write_text("Content 1")
    (source_dir / "file2.txt").write_text("Content 2")
    subdir = source_dir / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("Content 3")
    
    checksums = archive_data(source_dir, archive_dir)
    
    # Verify all files were archived
    assert len(checksums) == 3
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums
    assert "subdir/file3.txt" in checksums
    
    # Verify files exist in archive
    assert (archive_dir / "file1.txt").exists()
    assert (archive_dir / "file2.txt").exists()
    assert (archive_dir / "subdir/file3.txt").exists()


def test_archive_data_overwrite_false(temp_dirs):
    """Test archiving with overwrite=False skips existing files."""
    source_dir, archive_dir = temp_dirs
    
    # Create test file in source
    (source_dir / "file1.txt").write_text("New Content")
    
    # Create same file in archive with different content
    (archive_dir / "file1.txt").write_text("Old Content")
    
    checksums = archive_data(source_dir, archive_dir, overwrite=False)
    
    # Verify file was skipped
    assert len(checksums) == 1
    assert (archive_dir / "file1.txt").read_text() == "Old Content"


def test_archive_data_overwrite_true(temp_dirs):
    """Test archiving with overwrite=True replaces existing files."""
    source_dir, archive_dir = temp_dirs
    
    # Create test file in source
    (source_dir / "file1.txt").write_text("New Content")
    
    # Create same file in archive with different content
    (archive_dir / "file1.txt").write_text("Old Content")
    
    checksums = archive_data(source_dir, archive_dir, overwrite=True)
    
    # Verify file was overwritten
    assert len(checksums) == 1
    assert (archive_dir / "file1.txt").read_text() == "New Content"


def test_archive_data_empty_source(temp_dirs):
    """Test archiving from an empty source directory."""
    source_dir, archive_dir = temp_dirs
    
    checksums = archive_data(source_dir, archive_dir)
    
    assert checksums == {}


def test_archive_data_source_not_found():
    """Test that FileNotFoundError is raised for non-existent source."""
    with tempfile.TemporaryDirectory() as temp_dir:
        non_existent_source = Path(temp_dir) / "nonexistent"
        archive_dir = Path(temp_dir) / "archive"
        
        with pytest.raises(FileNotFoundError):
            archive_data(non_existent_source, archive_dir)


def test_verify_archive_integrity_valid(temp_dirs):
    """Test verification with valid checksums."""
    source_dir, archive_dir = temp_dirs
    
    # Archive some files
    (source_dir / "file1.txt").write_text("Content 1")
    (source_dir / "file2.txt").write_text("Content 2")
    checksums = archive_data(source_dir, archive_dir)
    
    # Verify all files pass
    results = verify_archive_integrity(archive_dir, checksums)
    
    assert all(results.values())
    assert len(results) == 2


def test_verify_archive_integrity_invalid(temp_dirs):
    """Test verification with corrupted file."""
    source_dir, archive_dir = temp_dirs
    
    # Archive files
    (source_dir / "file1.txt").write_text("Content 1")
    checksums = archive_data(source_dir, archive_dir)
    
    # Corrupt the archived file
    (archive_dir / "file1.txt").write_text("Corrupted Content")
    
    results = verify_archive_integrity(archive_dir, checksums)
    
    assert results["file1.txt"] is False


def test_verify_archive_integrity_missing_file(temp_dirs):
    """Test verification with missing file."""
    source_dir, archive_dir = temp_dirs
    
    # Archive files
    (source_dir / "file1.txt").write_text("Content 1")
    checksums = archive_data(source_dir, archive_dir)
    
    # Remove the archived file
    (archive_dir / "file1.txt").unlink()
    
    results = verify_archive_integrity(archive_dir, checksums)
    
    assert results["file1.txt"] is False


def test_generate_checksum_manifest(temp_dirs):
    """Test manifest generation."""
    source_dir, archive_dir = temp_dirs
    
    # Archive files
    (source_dir / "file1.txt").write_text("Content 1")
    (source_dir / "file2.txt").write_text("Content 2")
    archive_data(source_dir, archive_dir)
    
    manifest_path = archive_dir.parent / "manifest.txt"
    generate_checksum_manifest(archive_dir, manifest_path)
    
    # Verify manifest exists and has content
    assert manifest_path.exists()
    content = manifest_path.read_text()
    assert "file1.txt" in content
    assert "file2.txt" in content
    assert len(content.splitlines()) == 2
