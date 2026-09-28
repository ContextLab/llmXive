"""
Unit tests for src/lib/utils.py
"""
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import sys

# Add code directory to path if not already present
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.lib.utils import (
    set_global_seed,
    compute_file_checksum,
    compute_directory_checksum,
    validate_checksum
)


class TestSetGlobalSeed:
    def test_seed_sets_python_random(self):
        """Test that set_global_seed affects Python's random module."""
        import random
        set_global_seed(12345)
        val1 = random.random()
        
        set_global_seed(12345)
        val2 = random.random()
        
        assert val1 == val2

    def test_seed_sets_numpy(self):
        """Test that set_global_seed affects numpy's random state."""
        set_global_seed(42)
        arr1 = np.random.rand(5)
        
        set_global_seed(42)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2)

    def test_seed_default_value(self):
        """Test that calling without arguments uses a default seed."""
        # Just ensure it doesn't crash
        set_global_seed()


class TestComputeFileChecksum:
    def test_sha256_consistency(self):
        """Test that SHA256 checksum is consistent for the same file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Hello, World!")
            tmp_path = tmp.name

        try:
            checksum1 = compute_file_checksum(tmp_path)
            checksum2 = compute_file_checksum(tmp_path)
            assert checksum1 == checksum2
        finally:
            os.unlink(tmp_path)

    def test_sha256_vs_content_change(self):
        """Test that changing content changes the checksum."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Content A")
            tmp_path = tmp.name

        try:
            checksum_a = compute_file_checksum(tmp_path)
            
            with open(tmp_path, "wb") as f:
                f.write(b"Content B")
            
            checksum_b = compute_file_checksum(tmp_path)
            
            assert checksum_a != checksum_b
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("/nonexistent/path/file.txt")

    def test_md5_algorithm(self):
        """Test MD5 checksum calculation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Test data")
            tmp_path = tmp.name

        try:
            checksum = compute_file_checksum(tmp_path, algorithm="md5")
            # MD5 of "Test data" is known
            assert len(checksum) == 32  # MD5 hex string length
            assert all(c in "0123456789abcdef" for c in checksum.lower())
        finally:
            os.unlink(tmp_path)

    def test_invalid_algorithm(self):
        """Test that ValueError is raised for unsupported algorithm."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Data")
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError):
                compute_file_checksum(tmp_path, algorithm="sha999")
        finally:
            os.unlink(tmp_path)


class TestComputeDirectoryChecksum:
    def test_directory_checksum_consistency(self):
        """Test that directory checksum is consistent for same content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "file1.txt").write_text("Content 1")
            (path / "file2.txt").write_text("Content 2")
            (path / "subdir").mkdir()
            (path / "subdir" / "file3.txt").write_text("Content 3")

            checksum1 = compute_directory_checksum(tmpdir)
            checksum2 = compute_directory_checksum(tmpdir)
            
            assert checksum1 == checksum2

    def test_directory_checksum_content_change(self):
        """Test that changing file content changes directory checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "file1.txt").write_text("Original")

            checksum1 = compute_directory_checksum(tmpdir)
            
            (path / "file1.txt").write_text("Modified")
            
            checksum2 = compute_directory_checksum(tmpdir)
            
            assert checksum1 != checksum2

    def test_directory_checksum_structure_change(self):
        """Test that adding a file changes directory checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "file1.txt").write_text("Content")

            checksum1 = compute_directory_checksum(tmpdir)
            
            (path / "file2.txt").write_text("New content")
            
            checksum2 = compute_directory_checksum(tmpdir)
            
            assert checksum1 != checksum2

    def test_not_a_directory(self):
        """Test that NotADirectoryError is raised for a file path."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"data")
            tmp_path = tmp.name

        try:
            with pytest.raises(NotADirectoryError):
                compute_directory_checksum(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestValidateChecksum:
    def test_valid_checksum(self):
        """Test validation returns True for correct checksum."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Test content")
            tmp_path = tmp.name

        try:
            actual_checksum = compute_file_checksum(tmp_path)
            assert validate_checksum(tmp_path, actual_checksum) is True
        finally:
            os.unlink(tmp_path)

    def test_invalid_checksum(self):
        """Test validation returns False for incorrect checksum."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Test content")
            tmp_path = tmp.name

        try:
            assert validate_checksum(tmp_path, "invalid_checksum_string") is False
        finally:
            os.unlink(tmp_path)

    def test_missing_file(self):
        """Test validation returns False for missing file."""
        assert validate_checksum("/nonexistent/file.txt", "somehash") is False