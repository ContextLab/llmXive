"""Unit tests for download module."""
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import hashlib

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from download import (
    calculate_sha256, 
    validate_checksums, 
    load_manifest,
    DATA_DIR
)

def test_calculate_sha256():
    """Test SHA256 calculation with known input."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        test_content = b"Hello, World!"
        tmp.write(test_content)
        tmp_path = Path(tmp.name)
    
    try:
        expected_hash = hashlib.sha256(test_content).hexdigest()
        actual_hash = calculate_sha256(tmp_path)
        assert actual_hash == expected_hash
    finally:
        tmp_path.unlink()

def test_validate_checksums_success():
    """Test checksum validation with matching hashes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("content2")
        
        # Create manifest
        manifest = {
            "files": [
                {
                    "filename": "file1.txt",
                    "sha256": hashlib.sha256(b"content1").hexdigest()
                },
                {
                    "filename": "file2.txt", 
                    "sha256": hashlib.sha256(b"content2").hexdigest()
                }
            ]
        }
        
        assert validate_checksums(manifest, tmp_path) is True

def test_validate_checksums_failure():
    """Test checksum validation with mismatched hashes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test file
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        # Create manifest with wrong hash
        manifest = {
            "files": [
                {
                    "filename": "file1.txt",
                    "sha256": "wronghash123"
                }
            ]
        }
        
        assert validate_checksums(manifest, tmp_path) is False

def test_validate_checksums_missing_file():
    """Test checksum validation with missing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create manifest referencing non-existent file
        manifest = {
            "files": [
                {
                    "filename": "missing.txt",
                    "sha256": "anyhash"
                }
            ]
        }
        
        assert validate_checksums(manifest, tmp_path) is False

def test_load_manifest_valid():
    """Test loading a valid manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_file = tmp_path / "manifest.json"
        
        manifest_data = {"files": [], "version": "1.0"}
        manifest_file.write_text(json.dumps(manifest_data))
        
        result = load_manifest(manifest_file)
        assert result == manifest_data
        assert result["version"] == "1.0"

def test_load_manifest_invalid_json():
    """Test loading an invalid JSON manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_manifest(manifest_file)