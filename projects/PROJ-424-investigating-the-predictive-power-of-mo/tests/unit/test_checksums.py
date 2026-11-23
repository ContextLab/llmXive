"""
Unit tests for checksum utilities.
"""
import hashlib
import json
import tempfile
from pathlib import Path
import pytest

from utils.checksums import (
    compute_file_hash,
    verify_file_hash,
    generate_checksum_manifest,
    load_checksum_manifest,
    verify_manifest,
    get_checksum_report,
    ALGORITHM,
)


def test_compute_file_hash():
    """Test computing hash of a file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        hash_value = compute_file_hash(temp_path)
        assert len(hash_value) == 64  # SHA256 hex length
        
        # Verify against known hash
        expected = hashlib.sha256(b"test content").hexdigest()
        assert hash_value == expected
    finally:
        temp_path.unlink()


def test_compute_file_hash_not_found():
    """Test computing hash of non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash(Path("/nonexistent/file.txt"))


def test_verify_file_hash_match():
    """Test verifying a file with correct hash."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        hash_value = compute_file_hash(temp_path)
        assert verify_file_hash(temp_path, hash_value) is True
    finally:
        temp_path.unlink()


def test_verify_file_hash_mismatch():
    """Test verifying a file with incorrect hash."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        assert verify_file_hash(temp_path, "wronghash123") is False
    finally:
        temp_path.unlink()


def test_generate_checksum_manifest():
    """Test generating checksum manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")
        
        manifest = generate_checksum_manifest([file1, file2])
        
        assert str(file1) in manifest
        assert str(file2) in manifest
        assert manifest[str(file1)]["hash"] == compute_file_hash(file1)


def test_verify_manifest_success():
    """Test verifying manifest with all valid files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")
        
        manifest_path = tmp_path / "manifest.json"
        generate_checksum_manifest([file1], manifest_path)
        
        all_valid, failed = verify_manifest(manifest_path)
        
        assert all_valid is True
        assert len(failed) == 0


def test_verify_manifest_failure():
    """Test verifying manifest with missing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")
        
        manifest_path = tmp_path / "manifest.json"
        generate_checksum_manifest([file1], manifest_path)
        
        # Delete the file
        file1.unlink()
        
        all_valid, failed = verify_manifest(manifest_path)
        
        assert all_valid is False
        assert len(failed) == 1
        assert "File not found" in failed[0]


def test_get_checksum_report():
    """Test generating checksum report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")
        
        report = get_checksum_report([file1])
        
        assert "Checksum Report" in report
        assert file1.name in report
        assert compute_file_hash(file1) in report
