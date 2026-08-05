"""
Unit tests for download_gsm8k.py functionality.

These tests verify the logic of checksum computation and file handling
without actually downloading the dataset (which would be slow and flaky).
"""
import json
import os
import tempfile
from pathlib import Path
import hashlib

import pytest

# Import the functions we want to test
# Note: We import the module to access internal helpers if needed,
# but for unit tests we often mock the heavy lifting.
# Here we test the pure logic functions.
import sys
from code.src.data.download_gsm8k import compute_sha256, save_checksums, load_checksums

def test_compute_sha256():
    """Test SHA256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, world!")
        temp_path = f.name

    try:
        # "Hello, world!" sha256
        expected = hashlib.sha256(b"Hello, world!").hexdigest()
        result = compute_sha256(Path(temp_path))
        assert result == expected
    finally:
        os.unlink(temp_path)

def test_save_and_load_checksums():
    """Test saving and loading checksums from JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checksum_file = Path(tmpdir) / "checksums.json"
        
        test_data = {
            "file1.jsonl": "abc123",
            "file2.jsonl": "def456"
        }
        
        save_checksums(test_data, checksum_file)
        assert checksum_file.exists()
        
        loaded = load_checksums(checksum_file)
        assert loaded == test_data

def test_load_missing_checksums():
    """Test loading from a non-existent file returns empty dict."""
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_file = Path(tmpdir) / "nonexistent.json"
        result = load_checksums(missing_file)
        assert result == {}

def test_compute_sha256_binary_content():
    """Test SHA256 with binary content."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        f.write(b"\x00\x01\x02\x03")
        temp_path = f.name

    try:
        expected = hashlib.sha256(b"\x00\x01\x02\x03").hexdigest()
        result = compute_sha256(Path(temp_path))
        assert result == expected
    finally:
        os.unlink(temp_path)
