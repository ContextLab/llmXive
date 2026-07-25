import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import h5py

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download_data import (
    load_expected_checksum,
    save_checksum,
    compute_file_hash,
    verify_checksum,
    verify_downloaded_data,
    download_stratified_sample,
    main
)
from config import get_project_root, get_data_path

class TestDownloadData:
    """Tests for the download_data module."""

    def test_compute_file_hash(self, tmp_path):
        """Test that file hash computation works correctly."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        # Compute hash
        hash_value = compute_file_hash(test_file)
        
        # Verify hash is a valid hex string
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64 hex characters
        
        # Verify the same content produces the same hash
        hash_value2 = compute_file_hash(test_file)
        assert hash_value == hash_value2

    def test_save_and_load_checksum(self, tmp_path):
        """Test checksum saving and loading."""
        checksum_file = tmp_path / "checksums.json"
        
        # Save a checksum
        save_checksum("test_file.h5", "abc123", checksum_file)
        
        # Load and verify
        checksums = load_expected_checksum(checksum_file)
        assert "test_file.h5" in checksums
        assert checksums["test_file.h5"] == "abc123"

    def test_verify_checksum(self, tmp_path):
        """Test checksum verification."""
        checksum_file = tmp_path / "checksums.json"
        
        # Save a checksum
        save_checksum("test_file.h5", "abc123", checksum_file)
        
        # Load checksums
        checksums = load_expected_checksum(checksum_file)
        
        # Test matching checksum
        assert verify_checksum("test_file.h5", "abc123", checksums)
        
        # Test mismatching checksum
        assert not verify_checksum("test_file.h5", "xyz789", checksums)
        
        # Test missing checksum (should return True per implementation)
        assert verify_checksum("missing_file.h5", "abc123", checksums)

    def test_verify_downloaded_data_exists(self, tmp_path):
        """Test verification of existing file."""
        test_file = tmp_path / "test.h5"
        test_file.write_text("dummy content")
        
        assert verify_downloaded_data(test_file)

    def test_verify_downloaded_data_missing(self, tmp_path):
        """Test verification of missing file."""
        missing_file = tmp_path / "nonexistent.h5"
        
        assert not verify_downloaded_data(missing_file)

    def test_verify_downloaded_data_empty(self, tmp_path):
        """Test verification of empty file."""
        empty_file = tmp_path / "empty.h5"
        empty_file.touch()  # Create empty file
        
        assert not verify_downloaded_data(empty_file)

    @pytest.mark.integration
    def test_download_stratified_sample(self):
        """
        Integration test for downloading stratified sample.
        This test requires network access and the OC20 dataset on HuggingFace.
        """
        # This is an integration test that would download real data
        # We skip it in unit test environments but it should pass when run
        # with network access and sufficient resources
        pytest.skip("Integration test requiring network access and OC20 dataset")

    def test_main_function(self, tmp_path, monkeypatch):
        """Test the main function with mocked download."""
        # Mock the download function to avoid actual download
        def mock_download(*args, **kwargs):
            # Create a dummy file
            data_dir = get_data_path()
            output_path = data_dir / "raw" / "oc20_sample.h5"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a minimal H5 file
            with h5py.File(output_path, 'w') as f:
                f.create_dataset('dummy', data=[1, 2, 3])
            
            return output_path

        monkeypatch.setattr("download_data.download_stratified_sample", mock_download)
        
        # Run main
        result = main()
        
        # Verify it returned 0 (success)
        assert result == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])