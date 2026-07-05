"""
Unit tests for code/utils/data_hygiene.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.data_hygiene import (
    compute_sha256,
    validate_file_exists,
    validate_files_exist,
    create_checksum_manifest,
    verify_checksums,
    ensure_directory
)


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with known content."""
    content = b"Hello, World! This is a test file for checksumming."
    file_path = tmp_path / "test_file.txt"
    file_path.write_bytes(content)
    return file_path, content


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory structure."""
    dir_path = tmp_path / "subdir" / "nested"
    return dir_path


def test_compute_sha256(temp_file):
    """Test that compute_sha256 returns a valid hex string."""
    file_path, _ = temp_file
    checksum = compute_sha256(file_path)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex length
    assert all(c in "0123456789abcdef" for c in checksum)


def test_compute_sha256_file_not_found():
    """Test that compute_sha256 raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/non/existent/path/file.txt")


def test_compute_sha256_directory():
    """Test that compute_sha256 raises IsADirectoryError for directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(IsADirectoryError):
            compute_sha256(tmp_dir)


def test_validate_file_exists_existing(temp_file):
    """Test validate_file_exists returns True for existing files."""
    file_path, _ = temp_file
    exists, error = validate_file_exists(file_path)
    assert exists is True
    assert error is None


def test_validate_file_exists_missing():
    """Test validate_file_exists returns False for missing files."""
    exists, error = validate_file_exists("/non/existent/path/file.txt")
    assert exists is False
    assert error is not None
    assert "File missing" in error


def test_validate_files_exist():
    """Test validate_files_exist with mixed existing and missing files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        existing = os.path.join(tmp_dir, "exists.txt")
        Path(existing).write_text("data")
        missing = os.path.join(tmp_dir, "missing.txt")
        
        results = validate_files_exist([existing, missing])
        assert results[existing] is True
        assert results[missing] is False


def test_create_checksum_manifest(temp_file, tmp_path):
    """Test create_checksum_manifest generates correct JSON."""
    file_path, content = temp_file
    manifest_path = tmp_path / "manifest.json"
    
    manifest = create_checksum_manifest([file_path], output_path=manifest_path)
    
    assert str(file_path) in manifest
    assert len(manifest[str(file_path)]) == 64
    
    # Verify file was written
    assert manifest_path.exists()
    with open(manifest_path, "r") as f:
        loaded = json.load(f)
    assert loaded == manifest


def test_verify_checksums_success(temp_file, tmp_path):
    """Test verify_checksums returns True for matching checksums."""
    file_path, _ = temp_file
    checksum = compute_sha256(file_path)
    expected = {str(file_path): checksum}
    
    results = verify_checksums([file_path], expected)
    
    assert results[str(file_path)][0] is True
    assert "valid" in results[str(file_path)][1].lower()


def test_verify_checksums_mismatch(temp_file, tmp_path):
    """Test verify_checksums returns False for mismatched checksums."""
    file_path, _ = temp_file
    expected = {str(file_path): "0" * 64}  # Fake checksum
    
    results = verify_checksums([file_path], expected)
    
    assert results[str(file_path)][0] is False
    assert "mismatch" in results[str(file_path)][1].lower()


def test_ensure_directory_creates(tmp_path):
    """Test ensure_directory creates a new directory."""
    new_dir = tmp_path / "new" / "nested" / "dir"
    result = ensure_directory(new_dir)
    assert result.exists()
    assert result.is_dir()


def test_ensure_directory_existing(tmp_path):
    """Test ensure_directory does not fail on existing directory."""
    existing = tmp_path / "exists"
    existing.mkdir()
    result = ensure_directory(existing)
    assert result.exists()