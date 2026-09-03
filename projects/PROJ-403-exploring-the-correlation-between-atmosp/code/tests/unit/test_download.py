import os
import tempfile
import hashlib
import pytest
from pathlib import Path
import yaml
from src.data.download import calculate_sha256, verify_checksum, store_metadata

def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"hello world")
        tmp_path = tmp.name

    try:
        checksum = calculate_sha256(tmp_path)
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert checksum == expected
    finally:
        os.unlink(tmp_path)

def test_verify_checksum_success():
    """Test successful checksum verification."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = tmp.name

    try:
        checksum = calculate_sha256(tmp_path)
        assert verify_checksum(tmp_path, checksum) is True
    finally:
        os.unlink(tmp_path)

def test_verify_checksum_failure():
    """Test failed checksum verification."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = tmp.name

    try:
        wrong_checksum = "0" * 64
        assert verify_checksum(tmp_path, wrong_checksum) is False
    finally:
        os.unlink(tmp_path)

def test_store_metadata():
    """Test storing metadata to a YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_metadata.yaml")
        metadata = {
            "test_key": "test_value",
            "numbers": [1, 2, 3]
        }
        
        store_metadata(metadata, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded == metadata
