"""
Tests for the download service (T011).
"""
import pytest
from pathlib import Path
import sys
import os

# Ensure code/src is in path
code_root = Path(__file__).parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.services.download import download_from_huggingface, verify_download, DATASET_REPO, DATASET_FILE

class TestDownload:
    """Tests for download functionality."""

    def test_url_validity(self):
        """Assert that the download URL returns HTTP 200 and content is accessible."""
        # We test the logic by attempting a HEAD request or checking if the file exists in the repo
        # Since actual download might be slow, we verify the URL construction and accessibility
        import requests
        url = f"https://huggingface.co/datasets/{DATASET_REPO}/resolve/main/{DATASET_FILE}"
        
        # Perform a HEAD request to check existence without downloading full content
        response = requests.head(url, allow_redirects=True)
        assert response.status_code == 200, f"URL returned status {response.status_code}"
        assert "text/plain" in response.headers.get("Content-Type", "") or "application/json" in response.headers.get("Content-Type", "") or response.headers.get("Content-Type", "").startswith("application/octet-stream"), "Content type seems valid for a dataset file"

    def test_download_and_verify(self, tmp_path):
        """Test actual download to a temp directory and verify it is not empty."""
        output_dir = tmp_path / "raw"
        file_path = download_from_huggingface(DATASET_REPO, DATASET_FILE, output_dir)
        
        assert file_path.exists(), "Downloaded file does not exist"
        assert file_path.stat().st_size > 0, "Downloaded file is empty"
        
        # Verify function returns True for a valid file
        assert verify_download(file_path), "Verification failed for valid file"

    def test_checksum_verification(self, tmp_path):
        """Assert that checksum verification works (skipped if no expected checksum)."""
        # We can't easily test a specific checksum without the real value, 
        # but we can test that the function handles the logic correctly.
        # If EXPECTED_CHECKSUM is None, it should return True (as per implementation).
        output_dir = tmp_path / "raw"
        file_path = download_from_huggingface(DATASET_REPO, DATASET_FILE, output_dir)
        
        # Test with None expected checksum (should pass)
        assert verify_download(file_path, expected_checksum=None) is True
        
        # Test with wrong checksum (should fail)
        assert verify_download(file_path, expected_checksum="0" * 64) is False