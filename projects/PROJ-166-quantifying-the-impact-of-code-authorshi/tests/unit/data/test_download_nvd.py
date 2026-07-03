import os
import tempfile
import hashlib
import gzip
import json
from unittest.mock import patch, MagicMock
import pytest

from code.data.download_nvd import calculate_sha256, generate_checksum

def test_nvd_checksum_verification():
    """Assert SHA256 matches expected value for a known file."""
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        test_content = {"cve": "CVE-2023-1234", "description": "Test CVE"}
        json.dump(test_content, f)
        temp_path = f.name

    try:
        # Calculate SHA256 of the file
        calculated_hash = calculate_sha256(temp_path)
        
        # Verify it matches the expected hash for the content
        expected_hash = hashlib.sha256(json.dumps(test_content, sort_keys=True).encode('utf-8')).hexdigest()
        
        assert calculated_hash == expected_hash, f"Hash mismatch: {calculated_hash} != {expected_hash}"
    finally:
        os.unlink(temp_path)

def test_generate_checksum_creates_file():
    """Assert that generate_checksum creates a .sha256 file with correct content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_file = os.path.join(tmpdir, "test_data.json.gz")
        checksum_file = os.path.join(tmpdir, "test_data.json.gz.sha256")
        
        # Create a dummy gzipped file
        with gzip.open(data_file, 'wt') as f:
            f.write("test content")
        
        # Generate checksum
        generate_checksum(data_file)
        
        # Verify file exists
        assert os.path.exists(checksum_file), "Checksum file was not created"
        
        # Verify content format: "<hash>  <filename>"
        with open(checksum_file, 'r') as f:
            content = f.read().strip()
        
        parts = content.split()
        assert len(parts) == 2, "Checksum file should contain hash and filename"
        assert len(parts[0]) == 64, "SHA256 hash should be 64 characters"
        assert parts[1] == os.path.basename(data_file), "Filename in checksum should match"
