"""
Unit tests for the download module.

These tests verify the checksum validation and download logic
without actually downloading files from the internet.
"""
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.download import (
    calculate_sha256,
    validate_checksums,
    load_manifest,
)


def test_calculate_sha256():
    """Test SHA256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test data")
        temp_path = Path(f.name)
    
    try:
        # Known SHA256 for "test data"
        expected = hashlib.sha256(b"test data").hexdigest()
        actual = calculate_sha256(temp_path)
        assert actual == expected
    finally:
        temp_path.unlink()

def test_validate_checksums_success():
    """Test successful checksum validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a test file
        test_file = tmpdir / "test.zip"
        test_file.write_bytes(b"test content")
        
        # Calculate actual hash
        actual_hash = hashlib.sha256(b"test content").hexdigest()
        
        # Create manifest with correct hash
        manifest = {
            "test.zip": {
                "sha256": actual_hash,
                "size": 12
            }
        }
        
        manifest_path = tmpdir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        # Should not raise
        assert validate_checksums(manifest, test_file) is True

def test_validate_checksums_mismatch():
    """Test that checksum mismatch raises ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a test file
        test_file = tmpdir / "test.zip"
        test_file.write_bytes(b"test content")
        
        # Create manifest with wrong hash
        manifest = {
            "test.zip": {
                "sha256": "wronghash123",
                "size": 12
            }
        }
        
        with pytest.raises(ValueError, match="Checksum mismatch"):
            validate_checksums(manifest, test_file)

def test_validate_checksums_missing_hash():
    """Test that missing hash in manifest raises ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a test file
        test_file = tmpdir / "test.zip"
        test_file.write_bytes(b"test content")
        
        # Create manifest without hash
        manifest = {
            "test.zip": {
                "size": 12
            }
        }
        
        with pytest.raises(ValueError, match="not found in manifest"):
            validate_checksums(manifest, test_file)

def test_load_manifest():
    """Test loading a valid manifest file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        manifest_data = {
            "file1.zip": {"sha256": "abc123"},
            "file2.zip": {"sha256": "def456"}
        }
        
        manifest_path = tmpdir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        result = load_manifest(manifest_path)
        assert result == manifest_data
        assert "file1.zip" in result
        assert result["file1.zip"]["sha256"] == "abc123"
