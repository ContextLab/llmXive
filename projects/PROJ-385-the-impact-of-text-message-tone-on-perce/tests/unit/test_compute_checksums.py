import json
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code_05_compute_checksums import compute_sha256, load_existing_checksums, save_checksums


def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        checksum = compute_sha256(temp_path)
        expected = hashlib.sha256(b"test content").hexdigest()
        assert checksum == expected
    finally:
        temp_path.unlink()


def test_load_existing_checksums_empty():
    """Test loading checksums from non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checksums_path = Path(tmpdir) / "nonexistent.json"
        result = load_existing_checksums(checksums_path)
        assert result == {}


def test_load_existing_checksums_with_data():
    """Test loading checksums from existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checksums_path = Path(tmpdir) / "checksums.json"
        test_data = {"file1.csv": "abc123", "file2.csv": "def456"}
        
        with open(checksums_path, 'w') as f:
            json.dump(test_data, f)
        
        result = load_existing_checksums(checksums_path)
        assert result == test_data


def test_save_checksums():
    """Test saving checksums to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checksums_path = Path(tmpdir) / "checksums.json"
        test_data = {"file1.csv": "abc123"}
        
        save_checksums(test_data, checksums_path)
        
        assert checksums_path.exists()
        with open(checksums_path, 'r') as f:
            result = json.load(f)
        
        assert result == test_data