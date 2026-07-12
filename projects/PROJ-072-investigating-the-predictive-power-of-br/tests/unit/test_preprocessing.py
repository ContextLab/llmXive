"""
Unit tests for preprocessing pipeline download and validation functions.
"""
import pytest
import os
import sys
from pathlib import Path
import tempfile
import hashlib
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocessing.download import download_url_exists, verify_checksum, get_dataset_download_url

class TestDownloadValidation:
    def test_download_url_exists(self):
        """
        Asserts that the OpenNeuro ds000030 dataset URL is accessible.
        """
        base_url = "https://openneuro.org/datasets/ds000030"
        # The download module likely constructs a specific download URL or checks the landing page.
        # We verify the landing page exists first, then check the download logic if available.
        assert download_url_exists(base_url) is True, "The OpenNeuro dataset URL should be accessible."

    def test_get_dataset_download_url(self):
        """
        Verifies that the helper function returns a valid URL string for the dataset.
        """
        url = get_dataset_download_url("ds000030")
        assert url is not None
        assert isinstance(url, str)
        assert "openneuro.org" in url or "s3" in url

    def test_verify_checksum(self):
        """
        Asserts that verify_checksum works correctly with a temporary file.
        We create a known file, compute its hash, and verify the function returns True.
        Then we verify it returns False for a mismatched hash.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_file.zip"
            content = b"test content for checksum validation"
            test_file.write_bytes(content)
            
            # Calculate expected hash
            expected_hash = hashlib.sha256(content).hexdigest()
            
            # Test positive case
            assert verify_checksum(str(test_file), expected_hash) is True, "Checksum should match for correct hash."
            
            # Test negative case
            wrong_hash = "0" * 64
            assert verify_checksum(str(test_file), wrong_hash) is False, "Checksum should fail for incorrect hash."

    def test_verify_checksum_missing_file(self):
        """
        Asserts that verify_checksum returns False when the file does not exist.
        """
        assert verify_checksum("data/raw/non_existent_file.zip", "some_hash") is False, "Should return False for missing file."