"""
Unit tests for checksum generation functionality.
"""

import os
import tempfile
import hashlib
import pytest
from pathlib import Path
import shutil

from code.utils.checksum import compute_sha256, scan_directory, generate_checksums

def test_compute_sha256():
    """Test SHA256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        computed_hash = compute_sha256(temp_path)
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        assert computed_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("non_existent_file.txt"))

def test_scan_directory():
    """Test directory scanning."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create some files
        (temp_path / "file1.txt").touch()
        (temp_path / "file2.txt").touch()
        subdir = temp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").touch()
        
        files = scan_directory(temp_path)
        
        assert len(files) == 3
        file_names = {f.name for f in files}
        assert file_names == {"file1.txt", "file2.txt", "file3.txt"}

def test_scan_directory_empty():
    """Test scanning an empty directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        files = scan_directory(Path(temp_dir))
        assert len(files) == 0

def test_generate_checksums():
    """Test checksum generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        data_dir = temp_path / "data"
        data_dir.mkdir()
        
        # Create a test file
        test_file = data_dir / "test.txt"
        test_content = "checksum test data"
        test_file.write_text(test_content)
        
        output_file = temp_path / "checksums.txt"
        
        checksums = generate_checksums(data_dir, output_file, mode="test")
        
        assert len(checksums) == 1
        expected_hash = hashlib.sha256(test_content.encode()).hexdigest()
        assert checksums[0][0] == expected_hash
        
        # Verify file was written
        assert output_file.exists()
        content = output_file.read_text()
        assert expected_hash in content
        assert "test.txt" in content

def test_generate_checksums_no_files():
    """Test checksum generation with no files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        data_dir = temp_path / "data"
        data_dir.mkdir()
        
        output_file = temp_path / "checksums.txt"
        
        checksums = generate_checksums(data_dir, output_file, mode="test")
        
        assert len(checksums) == 0
        assert output_file.exists()