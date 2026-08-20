import json
import os
import hashlib
import tempfile
import zipfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from download import calculate_sha256, validate_checksums, load_manifest, cleanup_temp_files

def test_calculate_sha256():
    """Test SHA256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = b"Hello, World!"
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

def test_load_manifest():
    """Test loading a valid manifest file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        data = {"files": [{"filename": "test.txt", "sha256": "abc123"}]}
        json.dump(data, tmp)
        tmp_path = Path(tmp.name)
    
    try:
        manifest = load_manifest(tmp_path)
        assert manifest["files"][0]["filename"] == "test.txt"
        assert manifest["files"][0]["sha256"] == "abc123"
    finally:
        os.unlink(tmp_path)

def test_validate_checksums_success():
    """Test checksum validation when all files match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create a test file
        test_file = tmp_path / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Create manifest
        manifest = {
            "files": [
                {"filename": "test.txt", "sha256": expected_hash}
            ]
        }
        
        assert validate_checksums(manifest, tmp_path) is True

def test_validate_checksums_failure():
    """Test checksum validation when a file mismatch occurs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")
        
        # Create manifest with wrong hash
        manifest = {
            "files": [
                {"filename": "test.txt", "sha256": "wronghash"}
            ]
        }
        
        assert validate_checksums(manifest, tmp_path) is False

def test_cleanup_temp_files():
    """Test cleanup of temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "dummy.txt").write_text("dummy")
        
        cleanup_temp_files(tmp_path)
        
        assert not tmp_path.exists()