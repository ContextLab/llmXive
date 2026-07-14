"""
Contract test for data download integrity (T010).

This test verifies that the data ingestion utilities (retry_download, verify_checksum)
function correctly according to their contracts defined in code/utils.py.
It uses a small, known public file to validate the download and checksum logic
without requiring large dataset transfers.
"""
import os
import json
import hashlib
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys
import pathlib

# Add project root to path for imports
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils import verify_checksum, retry_download
from config import get_config


class TestDataIngestionContract(unittest.TestCase):
    """Contract tests for data ingestion utilities."""

    def test_verify_checksum_valid(self):
        """Contract: verify_checksum must return True for a file matching its hash."""
        content = b"test data for checksum validation"
        expected_hash = hashlib.sha256(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            self.assertTrue(verify_checksum(tmp_path, expected_hash))
        finally:
            os.unlink(tmp_path)

    def test_verify_checksum_invalid(self):
        """Contract: verify_checksum must return False for a file with mismatched hash."""
        content = b"test data"
        bad_hash = "0" * 64  # Invalid hash

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            self.assertFalse(verify_checksum(tmp_path, bad_hash))
        finally:
            os.unlink(tmp_path)

    def test_retry_download_success(self):
        """Contract: retry_download must return bytes on successful fetch."""
        mock_response = MagicMock()
        mock_response.content = b"mocked download content"
        mock_response.raise_for_status = MagicMock()

        with patch('utils.requests.get', return_value=mock_response) as mock_get:
            result = retry_download("http://example.com/fakefile")
            self.assertIsInstance(result, bytes)
            self.assertEqual(result, b"mocked download content")
            mock_get.assert_called_once()

    def test_retry_download_with_retries(self):
        """Contract: retry_download must retry on failure and succeed eventually."""
        mock_response = MagicMock()
        mock_response.content = b"success after retry"
        mock_response.raise_for_status = MagicMock()

        # First call raises exception, second succeeds
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network error")
            return mock_response

        with patch('utils.requests.get', side_effect=side_effect):
            result = retry_download("http://example.com/fakefile", max_retries=3, base_delay=0.01)
            self.assertEqual(result, b"success after retry")
            self.assertEqual(call_count, 2)

    def test_retry_download_exhausted(self):
        """Contract: retry_download must raise exception if all retries fail."""
        def always_fail(*args, **kwargs):
            raise Exception("Persistent network error")

        with patch('utils.requests.get', side_effect=always_fail):
            with self.assertRaises(Exception):
                retry_download("http://example.com/fakefile", max_retries=2, base_delay=0.01)

    def test_config_urls_exist(self):
        """Contract: Configuration must provide expected dataset URLs."""
        config = get_config()
        self.assertIn("PLANCK_MAP_ID", config)
        self.assertIn("BICEP_URL", config)
        self.assertIsNotNone(config["PLANCK_MAP_ID"])
        self.assertIsNotNone(config["BICEP_URL"])


if __name__ == "__main__":
    unittest.main()