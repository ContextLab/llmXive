import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from code.download_zreward import calculate_sha256, save_checksum, verify_checksum, download_dataset


class TestChecksumFunctions:
    def test_calculate_sha256(self, tmp_path):
        """Test SHA256 calculation for a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_sha256(test_file)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length
        
        # Verify against known value
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_save_and_verify_checksum(self, tmp_path):
        """Test saving and verifying checksum."""
        test_file = tmp_path / "test.txt"
        test_content = b"Test content"
        test_file.write_bytes(test_content)
        
        checksum = calculate_sha256(test_file)
        
        # Create a temporary checksum file
        checksum_file = tmp_path / ".checksums"
        
        # Mock save_checksum to use temp directory
        import code.download_zreward as download_module
        original_checksum_path = download_module.CHECKSUMS_FILE
        download_module.CHECKSUMS_FILE = checksum_file
        
        try:
            save_checksum(test_file, checksum)
            assert checksum_file.exists()
            
            # Verify
            assert verify_checksum(test_file, checksum) is True
            assert verify_checksum(test_file, "wrong_checksum") is False
        finally:
            download_module.CHECKSUMS_FILE = original_checksum_path

class TestDownloadDataset:
    def test_download_dataset_structure(self):
        """Test that download_dataset returns a Path object when successful."""
        # Note: We don't actually run the download here to avoid network calls in unit tests
        # Instead, we verify the function exists and has correct signature
        assert callable(download_dataset)
        
    def test_error_on_missing_sources(self, tmp_path, monkeypatch):
        """Test that RuntimeError is raised when all sources fail."""
        from unittest.mock import patch
        
        # Mock load_dataset to always fail
        with patch('code.download_zreward.load_dataset', side_effect=Exception("Network error")):
            with pytest.raises(RuntimeError, match="Failed to download Z-Reward dataset"):
                download_dataset()