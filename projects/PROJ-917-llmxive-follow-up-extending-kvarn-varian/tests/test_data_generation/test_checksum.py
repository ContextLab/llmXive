import pytest
from data_generation.utils import compute_checksum
import hashlib
import tempfile
from pathlib import Path
import os

def test_checksum_deterministic():
    """Test that computing the checksum of the same file twice yields the same result."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data for checksum")
        tmp_path = Path(tmp.name)
    
    try:
        checksum1 = compute_checksum(tmp_path)
        checksum2 = compute_checksum(tmp_path)
        
        assert checksum1 == checksum2
        assert isinstance(checksum1, str)
        assert len(checksum1) == 64  # SHA256 hex length
    finally:
        os.unlink(tmp_path)

def test_checksum_unique():
    """Test that different files produce different checksums."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp1:
        tmp1.write(b"data set A")
        path1 = Path(tmp1.name)
        
    with tempfile.NamedTemporaryFile(delete=False) as tmp2:
        tmp2.write(b"data set B")
        path2 = Path(tmp2.name)
    
    try:
        checksum1 = compute_checksum(path1)
        checksum2 = compute_checksum(path2)
        
        assert checksum1 != checksum2
    finally:
        os.unlink(path1)
        os.unlink(path2)

def test_checksum_empty_file():
    """Test checksum of an empty file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        # Write nothing, file is empty
        checksum = compute_checksum(tmp_path)
        
        # SHA256 of empty string
        expected = hashlib.sha256(b"").hexdigest()
        assert checksum == expected
    finally:
        os.unlink(tmp_path)

def test_checksum_large_file():
    """Test checksum of a large file to ensure chunked reading works."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        # Write 1MB of data
        chunk = b"x" * 1024
        for _ in range(1024):
            tmp.write(chunk)
        tmp_path = Path(tmp.name)
    
    try:
        checksum = compute_checksum(tmp_path)
        assert isinstance(checksum, str)
        assert len(checksum) == 64
    finally:
        os.unlink(tmp_path)

def test_checksum_nonexistent_file():
    """Test that computing checksum of a non-existent file raises an error."""
    from data_checksum_manager import compute_file_checksum
    
    non_existent_path = Path("/tmp/does_not_exist_12345.txt")
    
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(non_existent_path)

def test_checksum_directory():
    """Test that computing checksum of a directory raises an error."""
    from data_checksum_manager import compute_file_checksum
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(ValueError):
            compute_file_checksum(Path(tmp_dir))