"""
Unit tests for checksum_utils.py
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest

from checksum_utils import compute_checksum, generate_checksums, verify_checksums, update_checksum_for_file
from config import get_project_root

def test_compute_checksum_sha256():
    """Test SHA256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello World")
        temp_path = Path(f.name)
    
    try:
        expected = hashlib.sha256(b"Hello World").hexdigest()
        result = compute_checksum(temp_path, "sha256")
        assert result == expected
    finally:
        os.unlink(temp_path)

def test_compute_checksum_md5():
    """Test MD5 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello World")
        temp_path = Path(f.name)
    
    try:
        expected = hashlib.md5(b"Hello World").hexdigest()
        result = compute_checksum(temp_path, "md5")
        assert result == expected
    finally:
        os.unlink(temp_path)

def test_compute_checksum_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_checksum(Path("/nonexistent/file.txt"))

def test_compute_checksum_invalid_algorithm():
    """Test that ValueError is raised for invalid algorithm."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test")
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError):
            compute_checksum(temp_path, "invalid_algo")
    finally:
        os.unlink(temp_path)

def test_generate_checksums():
    """Test generating checksums for multiple files."""
    temp_files = []
    try:
        # Create 2 temp files
        for i in range(2):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(f"Content {i}")
                temp_files.append(Path(f.name))
        
        checksums = generate_checksums(temp_files, "sha256")
        
        # Should return 2 entries
        assert len(checksums) == 2
        
        # Verify keys are relative paths (or at least strings)
        for key in checksums.keys():
            assert isinstance(key, str)
            assert isinstance(checksums[key], str)
            assert len(checksums[key]) == 64 # SHA256 length
    finally:
        for f in temp_files:
            if f.exists():
                os.unlink(f)

def test_verify_checksums_missing_file():
    """Test verification fails when a file is missing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Content")
        temp_path = Path(f.name)
    
    # Create a fake checksum file
    checksum_content = f"{hashlib.sha256(b'Content').hexdigest()}  {temp_path.name}\n"
    checksum_content += f"{hashlib.sha256(b'Missing').hexdigest()}  missing_file.txt\n"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as cf:
        cf.write(checksum_content)
        cf_path = Path(cf.name)
    
    try:
        valid, failed = verify_checksums(cf_path)
        assert not valid
        assert "missing_file.txt" in failed
    finally:
        os.unlink(temp_path)
        os.unlink(cf_path)

def test_update_checksum_for_file():
    """Test updating the global checksum file."""
    # Create a temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test Update")
        temp_path = Path(f.name)
    
    # Create a temp checksum file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as cf:
        cf_path = Path(cf.name)
    
    try:
        # Update the checksum
        success = update_checksum_for_file(temp_path, "sha256", cf_path)
        assert success
        
        # Verify file content
        with open(cf_path, 'r') as f:
            content = f.read()
        
        assert "Test Update" not in content # Content shouldn't be in file, just hash
        assert hashlib.sha256(b"Test Update").hexdigest() in content
        assert str(temp_path.relative_to(get_project_root())) in content or str(temp_path) in content
    finally:
        os.unlink(temp_path)
        os.unlink(cf_path)