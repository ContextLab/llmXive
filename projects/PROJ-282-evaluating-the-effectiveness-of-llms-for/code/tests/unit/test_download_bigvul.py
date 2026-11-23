"""
Tests for T011: BigVul Download and Checksum Verification.
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

# Ensure code path is correct
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.download_bigvul import compute_sha256, save_checksums, load_checksums

class TestChecksumFunctions:
    def test_compute_sha256_success(self, tmp_path):
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_compute_sha256_empty_file(self, tmp_path):
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash

class TestChecksumPersistence:
    def test_save_and_load_checksums(self, tmp_path):
        checksums_file = tmp_path / "checksums.json"
        expected_data = {"file1.parquet": "abc123", "file2.parquet": "def456"}
        
        save_checksums(expected_data, checksums_file)
        
        assert checksums_file.exists()
        loaded_data = load_checksums(checksums_file)
        
        assert loaded_data == expected_data

class TestDownloadLogic:
    @patch("src.data.download_bigvul.load_dataset")
    @patch("src.data.download_bigvul.save_to_parquet")
    @patch("src.data.download_bigvul.compute_sha256")
    def test_download_success_scenario(self, mock_hash, mock_save, mock_load_ds, tmp_path):
        # Setup mocks
        mock_ds = MagicMock()
        mock_load_ds.return_value = mock_ds
        mock_hash.return_value = "d41d8cd98f00b204e9800998ecf8427e"
        
        # Mock config
        with patch("src.data.download_bigvul.get_project_root", return_value=tmp_path):
            # We can't easily run main() fully without network, but we can test the logic flow
            # by mocking the download function directly
            from src.data.download_bigvul import download_language_subset
            
            # This tests the mock setup, not the real network call
            result = download_language_subset("c")
            assert result is not None
            mock_load_ds.assert_called()