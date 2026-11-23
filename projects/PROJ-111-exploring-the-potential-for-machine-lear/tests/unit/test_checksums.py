import os
import tempfile
import numpy as np
import pytest
from pathlib import Path
import shutil

# Import the functions we are testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils import write_checksums, verify_checksums, compute_file_checksum

def test_compute_file_checksum():
    """Test SHA256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        checksum = compute_file_checksum(temp_path)
        # Known SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_write_checksums():
    """Test writing checksums for files in a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test structure
        raw_dir = Path(tmpdir) / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        test_file = raw_dir / "test.npy"
        np.save(test_file, np.array([1, 2, 3]))
        
        # Run write_checksums
        output_path = Path(tmpdir) / "checksums.txt"
        write_checksums(data_dirs=[str(raw_dir)], output_path=str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "test.npy" in content
        assert len(content.split('\n')) > 1  # Checksum + newline

def test_verify_checksums_valid():
    """Test verification passes for valid checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        test_file = raw_dir / "test.npy"
        np.save(test_file, np.array([1, 2, 3]))
        
        output_path = Path(tmpdir) / "checksums.txt"
        write_checksums(data_dirs=[str(raw_dir)], output_path=str(output_path))
        
        # Verify should pass
        assert verify_checksums(str(output_path)) is True

def test_verify_checksums_corrupted():
    """Test verification fails for corrupted files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        test_file = raw_dir / "test.npy"
        np.save(test_file, np.array([1, 2, 3]))
        
        output_path = Path(tmpdir) / "checksums.txt"
        write_checksums(data_dirs=[str(raw_dir)], output_path=str(output_path))
        
        # Corrupt the file
        np.save(test_file, np.array([9, 9, 9]))
        
        # Verify should fail
        with pytest.raises(RuntimeError):
            verify_checksums(str(output_path))

def test_verify_checksums_missing_file():
    """Test verification fails for missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        test_file = raw_dir / "test.npy"
        np.save(test_file, np.array([1, 2, 3]))
        
        output_path = Path(tmpdir) / "checksums.txt"
        write_checksums(data_dirs=[str(raw_dir)], output_path=str(output_path))
        
        # Delete the file
        os.unlink(test_file)
        
        # Verify should fail
        with pytest.raises(RuntimeError):
            verify_checksums(str(output_path))