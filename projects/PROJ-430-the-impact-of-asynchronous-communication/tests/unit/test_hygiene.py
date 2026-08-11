import json
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.hygiene import (
    compute_sha256,
    load_manifest,
    save_manifest,
    update_state_manifest,
    MANIFEST_FILE
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_sha256(temp_dir):
    """Test SHA-256 computation on a known file."""
    test_file = temp_dir / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    # Known SHA-256 for "Hello, World!"
    expected_hash = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
    
    actual_hash = compute_sha256(test_file)
    assert actual_hash == expected_hash

def test_compute_sha256_large_file(temp_dir):
    """Test SHA-256 computation on a larger file (chunked reading)."""
    test_file = temp_dir / "large.txt"
    # Create a file larger than the chunk size (4096 bytes)
    content = b"A" * 10000
    test_file.write_bytes(content)
    
    # Compute hash manually to verify
    import hashlib
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    expected_hash = sha256_hash.hexdigest()
    
    actual_hash = compute_sha256(test_file)
    assert actual_hash == expected_hash

def test_load_manifest_missing(temp_dir):
    """Test loading a non-existent manifest returns empty dict."""
    manifest_path = temp_dir / "nonexistent.json"
    manifest = load_manifest(manifest_path)
    assert manifest == {}

def test_load_manifest_existing(temp_dir):
    """Test loading an existing manifest."""
    manifest_path = temp_dir / "manifest.json"
    test_data = {"key": "value", "number": 42}
    with open(manifest_path, 'w') as f:
        json.dump(test_data, f)
    
    loaded = load_manifest(manifest_path)
    assert loaded == test_data

def test_save_manifest(temp_dir):
    """Test saving a manifest to disk."""
    manifest_path = temp_dir / "manifest.json"
    test_data = {"file1": {"hash": "abc123", "size": 100}}
    
    save_manifest(manifest_path, test_data)
    
    assert manifest_path.exists()
    with open(manifest_path, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data == test_data

def test_update_state_manifest(temp_dir):
    """Test updating manifest with a new file's state."""
    test_file = temp_dir / "data.csv"
    test_file.write_text("col1,col2\n1,2\n3,4")
    
    manifest_path = temp_dir / MANIFEST_FILE
    
    # Initial manifest should be empty
    update_state_manifest(test_file, manifest_path)
    
    manifest = load_manifest(manifest_path)
    assert "data.csv" in manifest
    assert "hash" in manifest["data.csv"]
    assert "size" in manifest["data.csv"]
    assert "updated_at" in manifest["data.csv"]
    
    # Verify size is correct
    assert manifest["data.csv"]["size"] == test_file.stat().st_size

def test_update_state_manifest_nonexistent(temp_dir):
    """Test that updating manifest for non-existent file raises error."""
    nonexistent_file = temp_dir / "does_not_exist.txt"
    manifest_path = temp_dir / MANIFEST_FILE
    
    with pytest.raises(FileNotFoundError):
        update_state_manifest(nonexistent_file, manifest_path)

def test_update_state_manifest_overwrite(temp_dir):
    """Test that updating a file updates its entry in the manifest."""
    test_file = temp_dir / "update_test.txt"
    manifest_path = temp_dir / MANIFEST_FILE
    
    # First update
    test_file.write_text("version 1")
    update_state_manifest(test_file, manifest_path)
    manifest_v1 = load_manifest(manifest_path)
    size_v1 = manifest_v1["update_test.txt"]["size"]
    
    # Modify file
    test_file.write_text("version 2 - longer content")
    update_state_manifest(test_file, manifest_path)
    manifest_v2 = load_manifest(manifest_path)
    size_v2 = manifest_v2["update_test.txt"]["size"]
    
    # Size should have changed
    assert size_v1 != size_v2
    assert size_v2 == test_file.stat().st_size