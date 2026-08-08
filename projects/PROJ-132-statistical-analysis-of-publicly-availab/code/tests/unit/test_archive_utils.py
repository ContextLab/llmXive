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
    src_dir = tempfile.mkdtemp()
    arc_dir = tempfile.mkdtemp()
    yield Path(src_dir), Path(arc_dir)
    shutil.rmtree(src_dir, ignore_errors=True)
    shutil.rmtree(arc_dir, ignore_errors=True)

def test_compute_sha256_basic(temp_dirs):
    src_dir, _ = temp_dirs
    test_file = Path(src_dir) / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_sha256(test_file)

    assert actual_hash == expected_hash

def test_compute_sha256_file_not_found():
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("non_existent_file.txt"))

def test_compute_sha256_large_file(temp_dirs):
    src_dir, _ = temp_dirs
    test_file = Path(src_dir) / "large.bin"
    # Create a 1MB file
    content = os.urandom(1024 * 1024)
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_sha256(test_file)

    assert actual_hash == expected_hash

def test_archive_data_basic(temp_dirs):
    src_dir, arc_dir = temp_dirs
    # Create nested structure
    (src_dir / "subdir").mkdir()
    file1 = src_dir / "file1.txt"
    file2 = src_dir / "subdir" / "file2.txt"
    file1.write_text("data1")
    file2.write_text("data2")

    count = archive_data(src_dir, arc_dir)

    assert count == 2
    assert (arc_dir / "file1.txt").exists()
    assert (arc_dir / "subdir" / "file2.txt").exists()

def test_archive_data_overwrite_false(temp_dirs):
    src_dir, arc_dir = temp_dirs
    file1 = src_dir / "file1.txt"
    file1.write_text("new_data")

    # Pre-existing file in archive
    arc_file = arc_dir / "file1.txt"
    arc_file.write_text("old_data")

    count = archive_data(src_dir, arc_dir, overwrite=False)

    assert count == 0  # Should skip existing
    assert arc_file.read_text() == "old_data"  # Content unchanged

def test_archive_data_overwrite_true(temp_dirs):
    src_dir, arc_dir = temp_dirs
    file1 = src_dir / "file1.txt"
    file1.write_text("new_data")

    # Pre-existing file in archive
    arc_file = arc_dir / "file1.txt"
    arc_file.write_text("old_data")

    count = archive_data(src_dir, arc_dir, overwrite=True)

    assert count == 1
    assert arc_file.read_text() == "new_data"

def test_archive_data_empty_source(temp_dirs):
    src_dir, arc_dir = temp_dirs
    count = archive_data(src_dir, arc_dir)
    assert count == 0

def test_archive_data_source_not_found(temp_dirs):
    _, arc_dir = temp_dirs
    count = archive_data(Path("/non/existent/path"), arc_dir)
    assert count == 0

def test_verify_archive_integrity_valid(temp_dirs):
    src_dir, arc_dir = temp_dirs
    file1 = src_dir / "file1.txt"
    file1.write_text("test")

    archive_data(src_dir, arc_dir)

    manifest_path = Path(arc_dir.parent) / "manifest.json"
    generate_checksum_manifest(arc_dir, manifest_path)

    assert verify_archive_integrity(arc_dir, manifest_path) is True

def test_verify_archive_integrity_invalid(temp_dirs):
    src_dir, arc_dir = temp_dirs
    file1 = src_dir / "file1.txt"
    file1.write_text("test")

    archive_data(src_dir, arc_dir)

    manifest_path = Path(arc_dir.parent) / "manifest.json"
    generate_checksum_manifest(arc_dir, manifest_path)

    # Corrupt the file in archive
    (arc_dir / "file1.txt").write_text("corrupted")

    assert verify_archive_integrity(arc_dir, manifest_path) is False

def test_verify_archive_integrity_missing_file(temp_dirs):
    src_dir, arc_dir = temp_dirs
    file1 = src_dir / "file1.txt"
    file1.write_text("test")

    archive_data(src_dir, arc_dir)

    manifest_path = Path(arc_dir.parent) / "manifest.json"
    generate_checksum_manifest(arc_dir, manifest_path)

    # Remove file from archive
    (arc_dir / "file1.txt").unlink()

    assert verify_archive_integrity(arc_dir, manifest_path) is False

def test_generate_checksum_manifest(temp_dirs):
    src_dir, arc_dir = temp_dirs
    file1 = src_dir / "file1.txt"
    file1.write_text("test")

    archive_data(src_dir, arc_dir)

    manifest_path = Path(arc_dir.parent) / "manifest.json"
    manifest = generate_checksum_manifest(arc_dir, manifest_path)

    assert "files" in manifest
    assert len(manifest["files"]) == 1
    assert manifest["files"][0]["path"] == "file1.txt"
    assert "sha256" in manifest["files"][0]
    assert "size_bytes" in manifest["files"][0]
