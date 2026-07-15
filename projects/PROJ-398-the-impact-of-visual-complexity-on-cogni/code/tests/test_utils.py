"""
Unit tests for src/lib/utils.py
"""
import os
import tempfile
from pathlib import Path

import pytest
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.lib.utils import (
    set_global_seed,
    compute_file_checksum,
    compute_directory_checksum,
    validate_checksum
)


class TestSetGlobalSeed:
    """Tests for set_global_seed function."""
    
    def test_set_seed_affects_python_random(self):
        """Verify that set_global_seed affects Python's random module."""
        set_global_seed(123)
        val1 = random.random()
        
        set_global_seed(123)
        val2 = random.random()
        
        assert val1 == val2
    
    def test_set_seed_affects_numpy(self):
        """Verify that set_global_seed affects NumPy's random module."""
        set_global_seed(456)
        arr1 = np.random.rand(3)
        
        set_global_seed(456)
        arr2 = np.random.rand(3)
        
        assert np.array_equal(arr1, arr2)
    
    def test_different_seeds_produce_different_results(self):
        """Verify that different seeds produce different random sequences."""
        set_global_seed(111)
        val1 = random.random()
        
        set_global_seed(222)
        val2 = random.random()
        
        assert val1 != val2


class TestComputeFileChecksum:
    """Tests for compute_file_checksum function."""
    
    def test_sha256_checksum(self):
        """Verify SHA256 checksum computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path, 'sha256')
            assert len(checksum) == 64  # SHA256 produces 64 hex chars
            # Verify it's a valid hex string
            int(checksum, 16)
        finally:
            os.unlink(temp_path)
    
    def test_md5_checksum(self):
        """Verify MD5 checksum computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path, 'md5')
            assert len(checksum) == 32  # MD5 produces 32 hex chars
        finally:
            os.unlink(temp_path)
    
    def test_file_not_found(self):
        """Verify that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("/nonexistent/file.txt")
    
    def test_unsupported_algorithm(self):
        """Verify that ValueError is raised for unsupported algorithms."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                compute_file_checksum(temp_path, 'invalid_algo')
        finally:
            os.unlink(temp_path)
    
    def test_consistent_checksum(self):
        """Verify that the same file produces the same checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("consistent content")
            temp_path = f.name
        
        try:
            checksum1 = compute_file_checksum(temp_path)
            checksum2 = compute_file_checksum(temp_path)
            assert checksum1 == checksum2
        finally:
            os.unlink(temp_path)


class TestComputeDirectoryChecksum:
    """Tests for compute_directory_checksum function."""
    
    def test_single_file_directory(self):
        """Verify checksum computation for a directory with one file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")
            
            checksums = compute_directory_checksum(tmpdir)
            
            assert len(checksums) == 1
            assert "test.txt" in checksums
    
    def test_nested_directories(self):
        """Verify checksum computation for nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            
            file1 = Path(tmpdir) / "file1.txt"
            file2 = subdir / "file2.txt"
            
            file1.write_text("content1")
            file2.write_text("content2")
            
            checksums = compute_directory_checksum(tmpdir, recursive=True)
            
            assert len(checksums) == 2
            assert "file1.txt" in checksums
            assert "subdir/file2.txt" in checksums
    
    def test_non_recursive(self):
        """Verify non-recursive directory checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            
            file1 = Path(tmpdir) / "file1.txt"
            file2 = subdir / "file2.txt"
            
            file1.write_text("content1")
            file2.write_text("content2")
            
            checksums = compute_directory_checksum(tmpdir, recursive=False)
            
            # Should only include file1.txt, not the subdir or its contents
            assert len(checksums) == 1
            assert "file1.txt" in checksums
    
    def test_not_a_directory(self):
        """Verify that NotADirectoryError is raised for files."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        
        try:
            with pytest.raises(NotADirectoryError):
                compute_directory_checksum(temp_path)
        finally:
            os.unlink(temp_path)


class TestValidateChecksum:
    """Tests for validate_checksum function."""
    
    def test_valid_checksum(self):
        """Verify that a correct checksum returns True."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path)
            assert validate_checksum(temp_path, checksum) is True
        finally:
            os.unlink(temp_path)
    
    def test_invalid_checksum(self):
        """Verify that an incorrect checksum returns False."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            assert validate_checksum(temp_path, "invalid_checksum") is False
        finally:
            os.unlink(temp_path)
    
    def test_case_insensitive(self):
        """Verify that checksum validation is case-insensitive."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path)
            assert validate_checksum(temp_path, checksum.upper()) is True
            assert validate_checksum(temp_path, checksum.lower()) is True
        finally:
            os.unlink(temp_path)
