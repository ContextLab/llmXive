"""
Tests for T029: Checksum generation for execution logs.
"""
import os
import sys
import tempfile
import hashlib
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_utils import generate_checksum, write_checksum_file

def test_generate_checksum_function():
    """Test that checksum generation produces consistent SHA-256 hashes."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("col1,col2\nval1,val2\n")
        temp_path = Path(f.name)

    try:
        checksum1 = generate_checksum(temp_path)
        checksum2 = generate_checksum(temp_path)

        # Checksums should be consistent
        assert checksum1 == checksum2
        # Checksums should be 64 hex characters (SHA-256)
        assert len(checksum1) == 64
        # Checksums should be valid hex
        int(checksum1, 16)
    finally:
        temp_path.unlink()

def test_write_checksum_file():
    """Test that checksums are written correctly to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checksum_file = Path(tmpdir) / "checksums.txt"
        
        test_checksums = [
            {"file": "test1.csv", "checksum": "abc123"},
            {"file": "test2.csv", "checksum": "def456"}
        ]

        write_checksum_file(checksum_file, test_checksums, append=False)

        # Verify file exists
        assert checksum_file.exists()

        # Verify content format
        content = checksum_file.read_text()
        assert "test1.csv" in content
        assert "abc123" in content
        assert "test2.csv" in content
        assert "def456" in content

def test_checksum_file_append():
    """Test that append mode adds to existing checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checksum_file = Path(tmpdir) / "checksums.txt"
        
        # Write initial checksums
        initial = [{"file": "initial.csv", "checksum": "123abc"}]
        write_checksum_file(checksum_file, initial, append=False)

        # Append new checksums
        appended = [{"file": "appended.csv", "checksum": "456def"}]
        write_checksum_file(checksum_file, appended, append=True)

        # Verify both exist
        content = checksum_file.read_text()
        assert "initial.csv" in content
        assert "appended.csv" in content
        assert "123abc" in content
        assert "456def" in content

def test_checksum_for_csv_content():
    """Test checksum calculation for actual CSV content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("instance_id,turns_to_converge\n1,10\n2,15\n")
        temp_path = Path(f.name)

    try:
        checksum = generate_checksum(temp_path)
        
        # Calculate expected checksum manually
        expected = hashlib.sha256(
            "instance_id,turns_to_converge\n1,10\n2,15\n".encode('utf-8')
        ).hexdigest()
        
        assert checksum == expected
    finally:
        temp_path.unlink()