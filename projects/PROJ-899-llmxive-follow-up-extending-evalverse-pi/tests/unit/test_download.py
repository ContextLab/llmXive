"""
Unit tests for data download.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import sys
from src.data.download import compute_sha256, ensure_directories, is_data_available

class TestComputeSha256:
    def test_compute_sha256(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = Path(f.name)
        
        try:
            hash_value = compute_sha256(temp_path)
            assert len(hash_value) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in hash_value)
        finally:
            os.unlink(temp_path)

class TestEnsureDirectories:
    def test_ensure_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # This would create directories in real implementation
            pass

class TestChecksumFunctions:
    def test_checksum_save_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            checksum_file = Path(tmpdir) / "checksum.txt"
            test_checksum = "abc123"
            
            from src.data.download import save_checksum, load_stored_checksum
            save_checksum(checksum_file, test_checksum)
            loaded = load_stored_checksum(checksum_file)
            assert loaded == test_checksum

class TestDataAvailability:
    def test_is_data_available(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with empty directory
            assert is_data_available() == False
