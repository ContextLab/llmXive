"""
Unit tests for the download module.
"""
import pytest
from pathlib import Path
import tempfile
import os
import hashlib

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(project_root))

from code.data.download import verify_checksum, decompress_gz
from code.utils.update_state import compute_file_hash

def test_verify_checksum_valid():
    """Test checksum verification with a valid file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = Path(tmp.name)
    
    # Compute actual hash
    actual_hash = compute_file_hash(tmp_path)
    
    try:
        result = verify_checksum(tmp_path, actual_hash)
        assert result is True
    finally:
        os.remove(tmp_path)

def test_verify_checksum_invalid():
    """Test checksum verification with an invalid hash."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = Path(tmp.name)
    
    try:
        result = verify_checksum(tmp_path, "invalid_hash")
        assert result is False
    finally:
        os.remove(tmp_path)

def test_decompress_gz():
    """Test gzip decompression."""
    import gzip
    with tempfile.TemporaryDirectory() as tmpdir:
        gz_path = Path(tmpdir) / "test.txt.gz"
        db_path = Path(tmpdir) / "test.txt"
        
        original_content = b"Hello, World!"
        
        # Create gzipped file
        with gzip.open(gz_path, 'wb') as f:
            f.write(original_content)
        
        # Decompress
        decompress_gz(gz_path, db_path)
        
        # Verify content
        with open(db_path, 'rb') as f:
            content = f.read()
        
        assert content == original_content
        assert db_path.exists()
        assert not gz_path.exists()  # Should be removed

def test_compute_file_hash():
    """Test file hash computation."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = Path(tmp.name)
    
    try:
        hash1 = compute_file_hash(tmp_path)
        hash2 = compute_file_hash(tmp_path)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    finally:
        os.remove(tmp_path)
