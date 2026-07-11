"""
Tests for the download module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import calculate_sha256, verify_downloaded_files, save_checksums, load_existing_checksums

def test_calculate_sha256():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = Path(tmp.name)
    
    try:
        hash_val = calculate_sha256(tmp_path)
        assert len(hash_val) == 64  # SHA256 hex length
        # Verify specific value for "test data"
        # echo -n "test data" | sha256sum -> 916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9
        assert hash_val == "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    finally:
        os.unlink(tmp_path)

def test_save_and_load_checksums():
    with tempfile.TemporaryDirectory() as tmpdir:
        checksum_file = Path(tmpdir) / "checksums.json"
        test_data = {"file1.txt": "abc123", "file2.txt": "def456"}
        
        save_checksums(test_data)
        loaded = load_existing_checksums()
        
        assert loaded == test_data

def test_verify_downloaded_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        checksums = {
            "file1.txt": calculate_sha256(file1),
            "missing.txt": "somehash"
        }
        
        is_valid, errors = verify_downloaded_files(checksums, tmp_path)
        assert not is_valid
        assert any("missing" in e for e in errors)
        
        # Add missing file
        (tmp_path / "missing.txt").write_text("content2")
        # Update checksum to match
        checksums["missing.txt"] = calculate_sha256(tmp_path / "missing.txt")
        
        is_valid, errors = verify_downloaded_files(checksums, tmp_path)
        assert is_valid
        assert len(errors) == 0
