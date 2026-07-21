import os
import gzip
import json
import hashlib
import tempfile
from pathlib import Path
import pytest

# Add project root to path
sys_path = Path(__file__).resolve().parent.parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from code.data.download_nvd import (
    calculate_sha256, 
    deduplicate_cves, 
    save_and_compress, 
    generate_checksum
)

def test_deduplicate_cves():
    """Test that deduplicate_cves removes duplicates based on CVE ID."""
    cves = [
        {"cve": {"id": "CVE-2021-1234"}},
        {"cve": {"id": "CVE-2021-5678"}},
        {"cve": {"id": "CVE-2021-1234"}},  # Duplicate
        {"cve": {"id": "CVE-2021-9999"}}
    ]
    result = deduplicate_cves(cves)
    assert len(result) == 3
    ids = [c["cve"]["id"] for c in result]
    assert ids.count("CVE-2021-1234") == 1
    assert "CVE-2021-5678" in ids
    assert "CVE-2021-9999" in ids

def test_calculate_sha256():
    """Test SHA256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Hello World")
        tmp_path = Path(tmp.name)
    
    try:
        checksum = calculate_sha256(tmp_path)
        # Known SHA256 for "Hello World"
        expected = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
        assert checksum == expected
    finally:
        os.unlink(tmp_path)

def test_save_and_compress():
    """Test saving data as gzipped JSON."""
    data = [{"test": "value"}]
    with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        save_and_compress(data, tmp_path)
        assert tmp_path.exists()
        
        with gzip.open(tmp_path, 'rt', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded == data
    finally:
        os.unlink(tmp_path)

def test_generate_checksum():
    """Test checksum generation and file writing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Test Data")
        tmp_path = Path(tmp.name)
    
    checksum_path = Path(str(tmp_path) + ".sha256")
    
    try:
        generate_checksum(tmp_path, checksum_path)
        assert checksum_path.exists()
        
        with open(checksum_path, 'r') as f:
            saved_checksum = f.read()
        
        assert saved_checksum == calculate_sha256(tmp_path)
    finally:
        os.unlink(tmp_path)
        if checksum_path.exists():
            os.unlink(checksum_path)