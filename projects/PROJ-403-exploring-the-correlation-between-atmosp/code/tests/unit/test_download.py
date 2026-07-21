import os
import tempfile
import hashlib
import pytest
from pathlib import Path
import yaml
from src.data.download import calculate_sha256, verify_checksum, store_metadata

def test_calculate_sha256():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data for checksum")
        tmp_path = tmp.name

    try:
        checksum = calculate_sha256(tmp_path)
        expected = hashlib.sha256(b"test data for checksum").hexdigest()
        assert checksum == expected
    finally:
        os.unlink(tmp_path)

def test_verify_checksum_success():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = tmp.name

    try:
        checksum = calculate_sha256(tmp_path)
        assert verify_checksum(tmp_path, checksum) is True
    finally:
        os.unlink(tmp_path)

def test_verify_checksum_failure():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError):
            verify_checksum(tmp_path, "wrong_checksum")
    finally:
        os.unlink(tmp_path)

def test_store_metadata():
    metadata = {
        "file1.nc": {
            "path": "data/raw/file1.nc",
            "checksum": "abc123",
            "size_bytes": 1024
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "metadata.yaml")
        store_metadata(metadata, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded == metadata
