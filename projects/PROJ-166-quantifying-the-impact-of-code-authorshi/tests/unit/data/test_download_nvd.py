import os
import gzip
import json
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.data.download_nvd import (
    calculate_sha256,
    deduplicate_cves,
    generate_checksum,
    save_and_compress
)

def test_calculate_sha256():
    """Test SHA256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"hello world")
        tmp_path = Path(tmp.name)
    
    try:
        checksum = calculate_sha256(tmp_path)
        # Expected SHA256 for "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert checksum == expected
    finally:
        os.unlink(tmp_path)

def test_deduplicate_cves():
    """Test deduplication logic."""
    cves = [
        {"cve": {"id": "CVE-2021-1"}},
        {"cve": {"id": "CVE-2021-2"}},
        {"cve": {"id": "CVE-2021-1"}}, # Duplicate
        {"cve": {"id": "CVE-2021-3"}},
        {"cve": {"id": None}}, # Invalid
    ]
    
    result = deduplicate_cves(cves)
    
    assert len(result) == 3
    ids = [cve["cve"]["id"] for cve in result]
    assert "CVE-2021-1" in ids
    assert "CVE-2021-2" in ids
    assert "CVE-2021-3" in ids
    assert ids.count("CVE-2021-1") == 1

def test_save_and_compress():
    """Test saving and compressing JSON data."""
    data = [{"test": "value"}]
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.json.gz"
        save_and_compress(data, output_path)
        
        assert output_path.exists()
        
        # Verify content
        with gzip.open(output_path, 'rt', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert loaded == data

def test_generate_checksum():
    """Test checksum generation and file writing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "data.json"
        checksum_path = Path(tmpdir) / "checksum.txt"
        
        # Create dummy data file
        with open(data_path, 'w') as f:
            f.write("test content")
        
        generate_checksum(data_path, checksum_path)
        
        assert checksum_path.exists()
        with open(checksum_path, 'r') as f:
            checksum = f.read().strip()
        
        # Verify checksum manually
        manual_hash = hashlib.sha256(b"test content").hexdigest()
        assert checksum == manual_hash
