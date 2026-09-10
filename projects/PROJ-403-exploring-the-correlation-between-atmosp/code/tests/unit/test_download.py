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
        test_content = b"Hello, World!"
        tmp.write(test_content)
        tmp_path = tmp.name

    try:
        expected_hash = hashlib.sha256(test_content).hexdigest()
        actual_hash = calculate_sha256(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

def test_verify_checksum_success():
    """Test successful checksum verification."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        test_content = b"Test data for verification"
        tmp.write(test_content)
        tmp_path = tmp.name

    try:
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert verify_checksum(tmp_path, expected_hash) is True
    finally:
        os.unlink(tmp_path)

def test_verify_checksum_failure():
    """Test failed checksum verification."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        test_content = b"Test data"
        tmp.write(test_content)
        tmp_path = tmp.name

    try:
        wrong_hash = "a" * 64
        assert verify_checksum(tmp_path, wrong_hash) is False
    finally:
        os.unlink(tmp_path)

def test_store_metadata():
    """Test storing metadata to YAML file."""
    test_metadata = {
        "files": [
            {
                "file": "data/raw/test.nc",
                "checksum": "abc123",
                "variable": "test_var"
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_metadata.yaml")
        store_metadata(test_metadata, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            loaded_metadata = yaml.safe_load(f)
        
        assert loaded_metadata == test_metadata