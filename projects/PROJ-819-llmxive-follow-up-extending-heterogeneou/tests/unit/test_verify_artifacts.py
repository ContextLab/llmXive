"""
Unit tests for T041 verification logic.
"""
import json
import hashlib
import tempfile
import os
from pathlib import Path
import pytest

# Mock the calculate_sha256 function for testing if needed, 
# but we will test the logic by creating temp files.

def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def test_verify_artifacts_success(tmp_path):
    """Test successful verification when files match manifest."""
    # Setup directory structure
    data_derived = tmp_path / "data" / "derived"
    data_derived.mkdir(parents=True)
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    # Create a dummy file
    test_file = data_derived / "test.json"
    content = b'{"test": "data"}'
    test_file.write_bytes(content)
    file_hash = calculate_sha256(str(test_file))

    # Create manifest
    manifest = {
        "files": [
            {"path": "data/derived/test.json", "sha256": file_hash}
        ]
    }
    manifest_path = state_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    # Import and run verification logic (inline for test simplicity)
    from code.verify_artifacts import verify_artifacts
    success, errors = verify_artifacts(tmp_path)

    assert success is True
    assert len(errors) == 0

def test_verify_artifacts_missing_file(tmp_path):
    """Test verification fails when file is missing."""
    data_derived = tmp_path / "data" / "derived"
    data_derived.mkdir(parents=True)
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    # Create manifest with non-existent file
    manifest = {
        "files": [
            {"path": "data/derived/missing.json", "sha256": "fakehash"}
        ]
    }
    manifest_path = state_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    from code.verify_artifacts import verify_artifacts
    success, errors = verify_artifacts(tmp_path)

    assert success is False
    assert len(errors) == 1
    assert "MISSING" in errors[0]

def test_verify_artifacts_hash_mismatch(tmp_path):
    """Test verification fails when hash does not match."""
    data_derived = tmp_path / "data" / "derived"
    data_derived.mkdir(parents=True)
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    # Create a file
    test_file = data_derived / "test.json"
    test_file.write_bytes(b"real content")
    
    # Create manifest with wrong hash
    manifest = {
        "files": [
            {"path": "data/derived/test.json", "sha256": "wronghash"}
        ]
    }
    manifest_path = state_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    from code.verify_artifacts import verify_artifacts
    success, errors = verify_artifacts(tmp_path)

    assert success is False
    assert len(errors) == 1
    assert "MISMATCH" in errors[0]

def test_verify_artifacts_no_derived_files(tmp_path):
    """Test behavior when manifest has no derived files."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    manifest = {
        "files": [
            {"path": "code/main.py", "sha256": "somehash"}
        ]
    }
    manifest_path = state_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    from code.verify_artifacts import verify_artifacts
    # This should not crash, just report no derived files to check
    success, errors = verify_artifacts(tmp_path)
    
    # Depending on implementation, this might be success or a warning.
    # Our implementation returns True if no errors are collected.
    assert success is True
    assert len(errors) == 0
