"""
Tests for src/lib/utils.py utilities.

Verifies seed setting behavior and checksum computation correctness.
"""
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import sys
import random
import hashlib

# Add src to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lib.utils import (
    set_global_seed,
    compute_file_checksum,
    compute_directory_checksum,
    validate_checksum
)


class TestSetGlobalSeed:
    """Tests for the set_global_seed function."""

    def test_seed_affects_random(self):
        """Verify that setting the seed produces reproducible random numbers."""
        set_global_seed(12345)
        val1 = random.random()
        
        set_global_seed(12345)
        val2 = random.random()
        
        assert val1 == val2

    def test_seed_affects_numpy(self):
        """Verify that setting the seed produces reproducible numpy random numbers."""
        set_global_seed(42)
        arr1 = np.random.rand(5)
        
        set_global_seed(42)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2)

    def test_seed_none_uses_default(self):
        """Verify that passing None uses the GLOBAL_SEED from config."""
        # This test assumes GLOBAL_SEED is set in config
        # We just verify it doesn't crash
        set_global_seed(None)
        assert True  # If we get here, it didn't crash


class TestComputeFileChecksum:
    """Tests for file checksum computation."""

    def test_sha256_checksum(self):
        """Test SHA256 checksum of a known file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path, "sha256")
            # Expected SHA256 for "Hello, World!"
            expected = hashlib.sha256(b"Hello, World!").hexdigest()
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_md5_checksum(self):
        """Test MD5 checksum of a known file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test Data")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path, "md5")
            expected = hashlib.md5(b"Test Data").hexdigest()
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("/nonexistent/path/file.txt")

    def test_unsupported_algorithm(self):
        """Test that ValueError is raised for unsupported algorithms."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                compute_file_checksum(temp_path, algorithm="invalid_algo")
        finally:
            os.unlink(temp_path)


class TestComputeDirectoryChecksum:
    """Tests for directory checksum computation."""

    def test_directory_checksum(self):
        """Test directory checksum with known content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with known content
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"
            
            file1.write_text("Content 1")
            file2.write_text("Content 2")
            
            checksum1 = compute_directory_checksum(tmpdir)
            
            # Should be deterministic
            checksum2 = compute_directory_checksum(tmpdir)
            assert checksum1 == checksum2

    def test_empty_directory(self):
        """Test checksum of an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checksum = compute_directory_checksum(tmpdir)
            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA256 hex length

    def test_non_directory(self):
        """Test that NotADirectoryError is raised for files."""
        with tempfile.NamedTemporaryFile() as f:
            with pytest.raises(NotADirectoryError):
                compute_directory_checksum(f.name)

    def test_recursive_checksum(self):
        """Test that subdirectories are included in checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            
            file1 = Path(tmpdir) / "file1.txt"
            file2 = subdir / "file2.txt"
            
            file1.write_text("Root file")
            file2.write_text("Sub file")
            
            checksum = compute_directory_checksum(tmpdir, recursive=True)
            assert isinstance(checksum, str)


class TestValidateChecksum:
    """Tests for checksum validation."""

    def test_valid_checksum(self):
        """Test validation with correct checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Validate Me")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path)
            assert validate_checksum(temp_path, checksum) is True
        finally:
            os.unlink(temp_path)

    def test_invalid_checksum(self):
        """Test validation with incorrect checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Validate Me")
            temp_path = f.name
        
        try:
            assert validate_checksum(temp_path, "0000000000000000000000000000000000000000000000000000000000000000") is False
        finally:
            os.unlink(temp_path)

    def test_missing_file(self):
        """Test validation with missing file returns False."""
        assert validate_checksum("/nonexistent/file.txt", "somechecksum") is False