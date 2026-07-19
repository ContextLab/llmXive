"""
Unit tests for T028: Checksum generation for the full pool.
"""
import os
import hashlib
import tempfile
from pathlib import Path
import pytest

# We need to add the code directory to the path to import the module under test
# assuming tests are run from project root
sys_path = Path(__file__).resolve().parent.parent.parent / "code"
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from checksum_pool import main
from utils.checksum_utils import compute_sha256, write_checksum_file


def test_compute_sha256_on_temp_file():
    """Test that compute_sha256 returns the correct hash for a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("id,value\n1,100\n2,200\n")
        temp_path = Path(f.name)

    try:
        # Calculate expected hash manually
        expected_hash = hashlib.sha256(b"id,value\n1,100\n2,200\n").hexdigest()
        
        actual_hash = compute_sha256(temp_path)
        
        assert actual_hash == expected_hash, f"Hash mismatch: {actual_hash} != {expected_hash}"
    finally:
        temp_path.unlink()


def test_write_checksum_file_format():
    """Test that write_checksum_file writes the correct format."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("data")
        temp_path = Path(f.name)
    
    checksum_path = temp_path.with_suffix(temp_path.suffix + ".sha256")

    try:
        write_checksum_file(temp_path, checksum_path)
        
        assert checksum_path.exists(), "Checksum file was not created"
        
        content = checksum_path.read_text()
        # Format should be: <hash>  <filename>
        parts = content.split()
        assert len(parts) == 2, f"Expected 2 parts in checksum file, got {len(parts)}"
        assert parts[0] == compute_sha256(temp_path), "Hash in file does not match computed hash"
        assert parts[1] == temp_path.name, f"Filename in checksum file ({parts[1]}) does not match ({temp_path.name})"
    finally:
        temp_path.unlink()
        if checksum_path.exists():
            checksum_path.unlink()