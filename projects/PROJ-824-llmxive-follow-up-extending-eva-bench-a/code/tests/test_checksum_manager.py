import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from data.checksum_manager import generate_checksums_for_directory, verify_checksums_against_file, create_checksum_file
from data.download import calculate_sha256

def test_generate_checksums_for_directory():
    """Test checksum generation for a directory with known files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.txt"
        
        content1 = "Hello, World!"
        content2 = "Test content"
        content3 = "Subdir content"
        
        file1.write_text(content1)
        file2.write_text(content2)
        file3.write_text(content3)
        
        # Generate checksums
        checksums = generate_checksums_for_directory(tmp_path, recursive=True)
        
        # Verify checksums
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        assert "subdir/file3.txt" in checksums
        
        # Verify actual hash values
        assert checksums["file1.txt"] == calculate_sha256(file1)
        assert checksums["file2.txt"] == calculate_sha256(file2)
        assert checksums["subdir/file3.txt"] == calculate_sha256(file3)

def test_verify_checksums_against_file():
    """Test verification of files against stored checksums."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        content1 = "Hello, World!"
        content2 = "Test content"
        
        file1.write_text(content1)
        file2.write_text(content2)
        
        # Create checksum file with correct hashes
        checksums = {
            "file1.txt": calculate_sha256(file1),
            "file2.txt": calculate_sha256(file2)
        }
        checksum_path = tmp_path / "checksums.json"
        with open(checksum_path, "w") as f:
            json.dump(checksums, f)
        
        # Verify with correct checksums
        success, errors = verify_checksums_against_file(checksum_path, tmp_path)
        assert success
        assert len(errors) == 0
        
        # Modify a file and verify failure
        file1.write_text("Modified content")
        success, errors = verify_checksums_against_file(checksum_path, tmp_path)
        assert not success
        assert len(errors) == 1
        assert "Checksum mismatch" in errors[0]
        
        # Add a missing file reference and verify failure
        checksums["missing.txt"] = "fake_hash"
        with open(checksum_path, "w") as f:
            json.dump(checksums, f)
        
        success, errors = verify_checksums_against_file(checksum_path, tmp_path)
        assert not success
        assert len(errors) == 1
        assert "Missing file" in errors[0]

def test_create_checksum_file():
    """Test creation of checksum file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create test file
        file1 = tmp_path / "file1.txt"
        file1.write_text("Test content")
        
        # Create checksum file
        checksum_path = tmp_path / "checksums.json"
        create_checksum_file(tmp_path, checksum_path)
        
        # Verify checksum file exists and contains correct data
        assert checksum_path.exists()
        
        with open(checksum_path, "r") as f:
            checksums = json.load(f)
        
        assert "file1.txt" in checksums
        assert checksums["file1.txt"] == calculate_sha256(file1)