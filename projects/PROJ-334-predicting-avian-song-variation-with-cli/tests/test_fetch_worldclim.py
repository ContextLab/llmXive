import pytest
import os
import sys
from pathlib import Path
import tempfile
import csv

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from fetch_worldclim import calculate_sha256, update_checksums_file

def test_calculate_sha256():
    """Test SHA256 calculation on a known string."""
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        # Known SHA256 for "test content"
        expected_hash = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        result = calculate_sha256(temp_path)
        assert result == expected_hash
    finally:
        temp_path.unlink()

def test_update_checksums_file():
    """Test updating checksums file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        checksums_file = tmpdir / "checksums.txt"
        
        # First call creates the file with header
        update_checksums_file(tmpdir / "file1.txt", "hash1", None)
        
        with open(checksums_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        assert rows[0] == ['filename', 'hash']
        assert rows[1] == ['file1.txt', 'hash1']
        
        # Second call appends
        update_checksums_file(tmpdir / "file2.txt", "hash2", None)
        
        with open(checksums_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        assert rows[2] == ['file2.txt', 'hash2']

# Note: We cannot test the full download without network and large files.
# The integration test would be in test_ingestion.py or a separate integration test.
