import json
import os
import tempfile
from pathlib import Path

import pytest

# Ensure code/ is in path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.checksum import (
    compute_file_checksum,
    compute_directory_checksums,
    validate_file_checksum,
    save_checksums,
    load_checksums,
    generate_checksum_manifest,
    verify_checksum_manifest,
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # Create nested structure
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file1.txt").write_text("Hello World")
        (tmp_path / "subdir" / "file2.txt").write_text("Test Data")
        yield tmp_path

def test_compute_file_checksum(temp_dir):
    """Test SHA-256 computation on a known string."""
    file_path = temp_dir / "file1.txt"
    checksum = compute_file_checksum(file_path)
    assert len(checksum) == 64  # SHA-256 hex length
    assert isinstance(checksum, str)

def test_compute_directory_checksums(temp_dir):
    """Test recursive directory checksumming."""
    checksums = compute_directory_checksums(temp_dir)
    assert "file1.txt" in checksums
    assert os.path.join("subdir", "file2.txt") in checksums
    assert len(checksums) == 2

def test_validate_file_checksum(temp_dir):
    """Test validation against a known checksum."""
    file_path = temp_dir / "file1.txt"
    expected = compute_file_checksum(file_path)
    assert validate_file_checksum(file_path, expected) is True
    assert validate_file_checksum(file_path, "invalid_checksum") is False

def test_save_and_load_checksums(temp_dir):
    """Test saving and loading checksums to/from JSON."""
    output_path = temp_dir / "checksums.json"
    checksums = {"test.txt": "abc123"}
    save_checksums(checksums, output_path)
    
    loaded = load_checksums(output_path)
    assert loaded == checksums

def test_generate_and_verify_manifest(temp_dir):
    """Test manifest generation and verification."""
    manifest_path = temp_dir / "manifest.json"
    
    # Generate
    manifest = generate_checksum_manifest(temp_dir, manifest_path)
    assert len(manifest) > 0
    
    # Verify (should pass)
    valid, errors = verify_checksum_manifest(temp_dir, manifest_path)
    assert valid is True
    assert len(errors) == 0
    
    # Corrupt a file to test failure
    (temp_dir / "file1.txt").write_text("Modified")
    valid, errors = verify_checksum_manifest(temp_dir, manifest_path)
    assert valid is False
    assert any("file1.txt" in e for e in errors)

def test_file_not_found_error():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum("/nonexistent/path/file.txt")

def test_not_a_directory_error(temp_dir):
    """Test that NotADirectoryError is raised for files."""
    with pytest.raises(NotADirectoryError):
        compute_directory_checksums(temp_dir / "file1.txt")