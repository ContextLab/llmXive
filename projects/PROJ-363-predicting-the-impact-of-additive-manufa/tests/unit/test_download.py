"""
Unit tests for code/download_data.py focusing on network failure handling.

This test suite verifies that the download script fails loudly when the
network is unavailable, ensuring no synthetic data is generated as a fallback.
"""
import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from download_data import (
    compute_file_hash,
    fetch_record_metadata,
    verify_material_type,
    get_download_url,
    download_file,
    update_state_with_checksum,
    main
)

class TestNetworkFailureHandling(unittest.TestCase):
    """Tests to ensure download_data.py raises errors on network failure."""

    def setUp(self):
        """Set up a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_raw_dir = os.path.join(self.temp_dir, 'data', 'raw')
        os.makedirs(self.data_raw_dir, exist_ok=True)
        self.state_file = os.path.join(self.temp_dir, 'state.yaml')
        
        # Initialize a minimal state file
        with open(self.state_file, 'w') as f:
            f.write("version: 1\nartifacts: {}\n")

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    @patch('download_data.urllib.request.urlopen')
    def test_network_failure_on_metadata_fetch(self, mock_urlopen):
        """
        Test that fetch_record_metadata raises RuntimeError when the network fails.
        
        This simulates a scenario where the Zenodo API is unreachable.
        """
        # Configure the mock to raise a network error
        mock_urlopen.side_effect = Exception("Network timeout: Connection refused")

        with self.assertRaises(RuntimeError) as context:
            fetch_record_metadata("https://zenodo.org/api/records/6826006")

        self.assertIn("Failed to fetch metadata", str(context.exception))

    @patch('download_data.urllib.request.urlopen')
    def test_network_failure_on_download(self, mock_urlopen):
        """
        Test that download_file raises RuntimeError when the download fails.
        
        This simulates a scenario where the file stream cannot be opened.
        """
        # Configure the mock to raise a network error immediately
        mock_urlopen.side_effect = Exception("Network error: Host unreachable")

        url = "https://zenodo.org/record/6826006/files/data.csv"
        output_path = os.path.join(self.data_raw_dir, "test_data.csv")

        with self.assertRaises(RuntimeError) as context:
            download_file(url, output_path)

        self.assertIn("Failed to download file", str(context.exception))
        self.assertFalse(os.path.exists(output_path))

    @patch('download_data.fetch_record_metadata')
    @patch('download_data.get_download_url')
    @patch('download_data.download_file')
    def test_no_synthetic_fallback_on_network_failure(
        self, mock_download, mock_get_url, mock_fetch_meta
    ):
        """
        Test that main() does NOT produce a synthetic file when the network fails.
        
        This is the critical test for the "Fail Loudly" constraint.
        It verifies that if the download fails, the script exits with an error
        and does not create a placeholder or synthetic dataset.
        """
        # Simulate network failure during download
        mock_fetch_meta.return_value = {"files": [{"id": "1", "title": "test"}]}
        mock_get_url.return_value = "https://example.com/data.csv"
        mock_download.side_effect = RuntimeError("Network failure: Simulated timeout")

        # Prepare arguments for main
        test_args = [
            'download_data.py',
            '--output-dir', self.temp_dir,
            '--state-file', self.state_file
        ]

        # Capture the exit behavior
        with self.assertRaises(SystemExit) as context:
            with patch('sys.argv', test_args):
                main()

        # Verify the script exited with an error code (non-zero)
        self.assertEqual(context.exception.code, 1)

        # CRITICAL: Verify NO synthetic file was created in data/raw
        potential_synthetic_files = [
            "cleaned_316L.csv",
            "synthetic_316L.csv",
            "mock_data.csv",
            "data.csv"
        ]

        for filename in potential_synthetic_files:
            file_path = os.path.join(self.data_raw_dir, filename)
            self.assertFalse(
                os.path.exists(file_path),
                f"Synthetic/placeholder file {filename} was created despite network failure!"
            )

    @patch('download_data.urllib.request.urlopen')
    def test_timeout_handling(self, mock_urlopen):
        """
        Test that a timeout exception is caught and re-raised as a RuntimeError.
        """
        import socket
        mock_urlopen.side_effect = socket.timeout("Connection timed out")

        with self.assertRaises(RuntimeError) as context:
            fetch_record_metadata("https://zenodo.org/api/records/6826006")

        self.assertIn("Failed to fetch metadata", str(context.exception))

    @patch('download_data.urllib.request.urlopen')
    def test_http_error_handling(self, mock_urlopen):
        """
        Test that an HTTP error (e.g., 404) is caught and re-raised as a RuntimeError.
        """
        from urllib.error import HTTPError
        mock_response = Mock()
        mock_response.code = 404
        mock_response.read.return_value = b"Not Found"
        
        mock_urlopen.side_effect = HTTPError(
            url="https://zenodo.org/data.csv",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=Mock()
        )

        with self.assertRaises(RuntimeError) as context:
            download_file("https://zenodo.org/data.csv", "/tmp/test.csv")

        self.assertIn("Failed to download file", str(context.exception))

if __name__ == '__main__':
    unittest.main()