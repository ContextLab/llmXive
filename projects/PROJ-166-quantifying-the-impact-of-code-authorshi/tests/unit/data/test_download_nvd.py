"""
Unit tests for code/data/download_nvd.py
"""
import os
import json
import gzip
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the functions to test
# Note: We assume the module is importable as 'code.data.download_nvd'
# or we adjust the import path based on the project structure.
# Since the task says 'code/data/download_nvd.py', we import relative to 'code'.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download_nvd import (
    calculate_sha256,
    deduplicate_cves,
    generate_checksum,
    save_and_compress
)

@pytest.fixture
def sample_cves():
    """Sample CVE data structure."""
    return [
        {
            "cveMetadata": {"cveId": "CVE-2021-1234"},
            "id": "CVE-2021-1234"
        },
        {
            "cveMetadata": {"cveId": "CVE-2021-5678"},
            "id": "CVE-2021-5678"
        },
        {
            "cveMetadata": {"cveId": "CVE-2021-1234"}, # Duplicate
            "id": "CVE-2021-1234"
        }
    ]

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file I/O tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_deduplicate_cves(sample_cves):
    """Test that duplicate CVEs are removed."""
    result = deduplicate_cves(sample_cves)
    assert len(result) == 2
    ids = [cve["cveMetadata"]["cveId"] for cve in result]
    assert "CVE-2021-1234" in ids
    assert "CVE-2021-5678" in ids

def test_calculate_sha256(temp_dir):
    """Test SHA256 calculation."""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    expected_hash = hashlib.sha256(test_content).hexdigest()
    calculated_hash = calculate_sha256(test_file)
    
    assert calculated_hash == expected_hash

def test_save_and_compress(temp_dir):
    """Test saving JSON and compressing to GZ."""
    data = [{"test": "data"}]
    output_path = temp_dir / "test.json.gz"
    
    save_and_compress(data, output_path)
    
    assert output_path.exists()
    assert output_path.suffix == ".gz"
    
    # Verify content can be read
    with gzip.open(output_path, 'rt', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    assert loaded_data == data

def test_generate_checksum(temp_dir):
    """Test checksum generation."""
    test_file = temp_dir / "test.txt"
    test_file.write_bytes(b"Test content")
    
    checksum_path = temp_dir / "test.sha256"
    generate_checksum(test_file, checksum_path)
    
    assert checksum_path.exists()
    with open(checksum_path, 'r') as f:
        saved_hash = f.read().strip()
    
    expected_hash = calculate_sha256(test_file)
    assert saved_hash == expected_hash