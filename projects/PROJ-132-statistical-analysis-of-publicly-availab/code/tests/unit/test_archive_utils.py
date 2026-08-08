import os
import tempfile
import shutil
from pathlib import Path
import pytest
import hashlib
import json
from src.data.archive_utils import (
    compute_sha256,
    archive_data,
    verify_archive_integrity,
    generate_checksum_manifest,
    run_archive_pipeline
)

@pytest.fixture
def temp_dirs():
    """Create temporary source and archive directories for testing."""
    temp_base = tempfile.mkdtemp()
    source_dir = Path(temp_base) / "source"
    archive_dir = Path(temp_base) / "archive"
    source_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some test files
    (source_dir / "file1.txt").write_text("content1")
    (source_dir / "subdir").mkdir()
    (source_dir / "subdir" / "file2.txt").write_text("content2")
    
    yield source_dir, archive_dir
    
    # Cleanup
    shutil.rmtree(temp_base, ignore_errors=True)

def test_compute_sha256_basic():
    """Test basic SHA-256 computation on a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = Path(f.name)
    
    try:
        hash_val = compute_sha256(temp_path)
        expected = hashlib.sha256(b"test content").hexdigest()
        assert hash_val == expected
    finally:
        os.unlink(temp_path)

def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/file.txt"))

def test_compute_sha256_large_file():
    """Test SHA-256 computation on a larger file."""
    content = b"x" * (1024 * 1024)  # 1MB of data
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    try:
        hash_val = compute_sha256(temp_path)
        expected = hashlib.sha256(content).hexdigest()
        assert hash_val == expected
    finally:
        os.unlink(temp_path)

def test_archive_data_basic(temp_dirs):
    """Test basic archiving functionality."""
    source_dir, archive_dir = temp_dirs
    result = archive_data(source_dir, archive_dir)
    
    assert result["status"] == "success"
    assert result["files_archived"] == 2
    assert (archive_dir / "file1.txt").exists()
    assert (archive_dir / "subdir" / "file2.txt").exists()

def test_archive_data_overwrite_false(temp_dirs):
    """Test archiving with overwrite=False when files exist."""
    source_dir, archive_dir = temp_dirs
    
    # Pre-populate archive with a different content
    (archive_dir / "file1.txt").parent.mkdir(parents=True, exist_ok=True)
    (archive_dir / "file1.txt").write_text("different content")
    
    result = archive_data(source_dir, archive_dir, overwrite=False)
    
    # Should skip existing file
    assert result["files_archived"] == 1  # Only subdir/file2.txt
    assert (archive_dir / "file1.txt").read_text() == "different content"

def test_archive_data_overwrite_true(temp_dirs):
    """Test archiving with overwrite=True."""
    source_dir, archive_dir = temp_dirs
    
    # Pre-populate archive
    (archive_dir / "file1.txt").parent.mkdir(parents=True, exist_ok=True)
    (archive_dir / "file1.txt").write_text("different content")
    
    result = archive_data(source_dir, archive_dir, overwrite=True)
    
    assert result["files_archived"] == 2
    assert (archive_dir / "file1.txt").read_text() == "content1"

def test_archive_data_empty_source(temp_dirs):
    """Test archiving from an empty source directory."""
    source_dir, archive_dir = temp_dirs
    
    # Remove all files from source
    for item in source_dir.rglob("*"):
        if item.is_file():
            item.unlink()
    
    result = archive_data(source_dir, archive_dir)
    assert result["status"] == "success"
    assert result["files_archived"] == 0

def test_archive_data_source_not_found():
    """Test that FileNotFoundError is raised for missing source directory."""
    with pytest.raises(FileNotFoundError):
        archive_data(Path("/nonexistent/source"), Path("/tmp/archive"))

def test_verify_archive_integrity_valid(temp_dirs):
    """Test integrity verification with correct checksums."""
    source_dir, archive_dir = temp_dirs
    archive_data(source_dir, archive_dir)
    
    checksums = generate_checksum_manifest(archive_dir, archive_dir / "checksums.json")
    assert verify_archive_integrity(archive_dir, checksums) is True

def test_verify_archive_integrity_invalid(temp_dirs):
    """Test integrity verification with incorrect checksums."""
    source_dir, archive_dir = temp_dirs
    archive_data(source_dir, archive_dir)
    
    # Create wrong checksums
    checksums = {
        "file1.txt": "wrong_hash_value",
        "subdir/file2.txt": "another_wrong_hash"
    }
    
    assert verify_archive_integrity(archive_dir, checksums) is False

def test_verify_archive_integrity_missing_file(temp_dirs):
    """Test integrity verification when a file is missing."""
    source_dir, archive_dir = temp_dirs
    archive_data(source_dir, archive_dir)
    
    checksums = {
        "file1.txt": compute_sha256(archive_dir / "file1.txt"),
        "nonexistent.txt": "some_hash"
    }
    
    assert verify_archive_integrity(archive_dir, checksums) is False

def test_generate_checksum_manifest(temp_dirs):
    """Test checksum manifest generation."""
    source_dir, archive_dir = temp_dirs
    archive_data(source_dir, archive_dir)
    
    manifest_path = archive_dir / "manifest.json"
    checksums = generate_checksum_manifest(archive_dir, manifest_path)
    
    assert manifest_path.exists()
    assert len(checksums) == 2
    assert "file1.txt" in checksums
    assert "subdir/file2.txt" in checksums
    
    # Verify JSON content
    with open(manifest_path) as f:
        data = json.load(f)
    assert data == checksums

def test_run_archive_pipeline(temp_dirs):
    """Test the full archive pipeline."""
    source_dir, archive_dir = temp_dirs
    manifest_path = archive_dir / "pipeline_manifest.json"
    
    result = run_archive_pipeline(source_dir, archive_dir, manifest_path)
    
    assert result["status"] == "success"
    assert result["files_archived"] == 2
    assert manifest_path.exists()
    assert result["total_checksums"] == 2
