"""
Unit tests for checksum verification logic in data_loader.py.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Mock config for testing if real config is not fully set up in test env
# We assume the project structure is correct as per T001/T004
from code.data_loader import verify_checksum, _compute_sha256, _load_checksums
from code.config import get_path


def test_compute_sha256():
    """Test that SHA256 is computed correctly."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        hash_val = _compute_sha256(temp_path)
        assert len(hash_val) == 64  # SHA256 hex length
        assert isinstance(hash_val, str)
    finally:
        os.unlink(temp_path)


def test_verify_checksum_success():
    """Test successful checksum verification."""
    content = "test data for checksum"
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    try:
        expected_hash = _compute_sha256(temp_path)
        checksums = {"test_file.txt": expected_hash}
        
        # Create a mock path structure for the test
        # We need to mock the relative path logic or pass the correct key
        # The function uses relative path or filename. Let's test filename matching.
        result = verify_checksum(temp_path, checksums)
        assert result is True
    finally:
        os.unlink(temp_path)


def test_verify_checksum_mismatch():
    """Test that verification fails on mismatch."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test data")
        temp_path = Path(f.name)
    
    try:
        wrong_hash = "a" * 64
        checksums = {"test_file.txt": wrong_hash}
        
        with pytest.raises(ValueError, match="Checksum mismatch"):
            verify_checksum(temp_path, checksums)
    finally:
        os.unlink(temp_path)


def test_verify_checksum_file_not_found_in_map():
    """Test that verification fails if file not in checksum map."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test data")
        temp_path = Path(f.name)
    
    try:
        checksums = {"other_file.txt": "hash"}
        
        with pytest.raises(ValueError, match="No checksum entry found"):
            verify_checksum(temp_path, checksums)
    finally:
        os.unlink(temp_path)


def test_verify_checksum_file_missing_on_disk():
    """Test that verification fails if file does not exist."""
    fake_path = Path("/nonexistent/file.txt")
    checksums = {"file.txt": "hash"}
    
    with pytest.raises(FileNotFoundError, match="Data file not found"):
        verify_checksum(fake_path, checksums)


def test_load_checksums_success():
    """Test loading checksums from a valid file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump({"file.txt": "hash123"}, f)
        temp_path = Path(f.name)
    
    try:
        result = _load_checksums(temp_path)
        assert result == {"file.txt": "hash123"}
    finally:
        os.unlink(temp_path)


def test_load_checksums_missing_file():
    """Test loading checksums from a missing file."""
    with pytest.raises(FileNotFoundError):
        _load_checksums(Path("/nonexistent/checksums.json"))