"""
Unit tests for code/utils/io.py utilities.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the functions to test
from code.utils.io import compute_checksum, check_disk_space, DiskSpaceError

def test_compute_checksum_sha256():
    """Test SHA256 checksum computation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        checksum = compute_checksum(temp_path, "sha256")
        # Known SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_compute_checksum_md5():
    """Test MD5 checksum computation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test Data")
        temp_path = f.name

    try:
        checksum = compute_checksum(temp_path, "md5")
        # Known MD5 for "Test Data"
        expected = "39f0b892673d067501f509534247d303"
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_compute_checksum_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_checksum("/nonexistent/path/file.txt")

def test_compute_checksum_invalid_algorithm():
    """Test that ValueError is raised for invalid algorithms."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Data")
        temp_path = f.name

    try:
        with pytest.raises(ValueError):
            compute_checksum(temp_path, "blake2")
    finally:
        os.unlink(temp_path)

def test_check_disk_space_sufficient():
    """Test disk space check with sufficient space."""
    # 100 bytes should always be available on a functioning system
    assert check_disk_space(100, Path.cwd()) is True

def test_check_disk_space_insufficient():
    """Test DiskSpaceError is raised when space is insufficient."""
    # Request a huge amount of space that is unlikely to be available
    # 10TB should trigger the error on almost any system
    huge_size = 10 * 1024 * 1024 * 1024 * 1024
    
    with pytest.raises(DiskSpaceError):
        check_disk_space(huge_size, Path.cwd())
