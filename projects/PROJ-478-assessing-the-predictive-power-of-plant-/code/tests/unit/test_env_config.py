import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

from src.utils.env_config import (
    load_environment_config,
    compute_file_checksum,
    verify_checksum,
    register_checksum,
    verify_all_downloads,
)

@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        path = Path(f.name)
    yield path
    path.unlink()

@pytest.fixture
def temp_manifest_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_file_checksum(temp_file):
    checksum = compute_file_checksum(temp_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 length

def test_compute_file_checksum_file_not_found():
    non_existent = Path("/non/existent/file.txt")
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(non_existent)

def test_verify_checksum_success(temp_file):
    checksum = compute_file_checksum(temp_file)
    assert verify_checksum(temp_file, checksum) is True

def test_verify_checksum_failure(temp_file):
    bad_checksum = "a" * 64
    assert verify_checksum(temp_file, bad_checksum) is False

def test_register_checksum(temp_manifest_dir, temp_file):
    checksum = compute_file_checksum(temp_file)
    manifest_path = temp_manifest_dir / "manifest.json"
    register_checksum(temp_file, checksum, manifest_path)
    
    assert manifest_path.exists()
    with open(manifest_path) as f:
        data = json.load(f)
    assert str(temp_file) in data
    assert data[str(temp_file)] == checksum

def test_verify_all_downloads(temp_manifest_dir, temp_file):
    checksum = compute_file_checksum(temp_file)
    manifest_path = temp_manifest_dir / "manifest.json"
    register_checksum(temp_file, checksum, manifest_path)
    
    # Add a fake entry for a missing file
    with open(manifest_path) as f:
        data = json.load(f)
    data["/non/existent/file.txt"] = checksum
    with open(manifest_path, 'w') as f:
        json.dump(data, f)
    
    # Should fail because one file is missing
    result = verify_all_downloads(manifest_path)
    assert result is False

def test_load_environment_config():
    # Test with default behavior (no specific env file provided)
    config = load_environment_config()
    assert isinstance(config, dict)
