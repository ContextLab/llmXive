"""
Unit tests for download_data.py focusing on network failure scenarios.

This test suite verifies that download_data.py raises the expected
RuntimeError when network failures occur and does NOT produce any
synthetic or placeholder files.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import json

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download_data import fetch_record_metadata, verify_material_type, download_file, main
from utils import setup_logging

class TestDownloadNetworkFailure(unittest.TestCase):
    """Tests for network failure scenarios in download_data.py"""

    def setUp(self):
        """Set up test fixtures"""
        self.logger = setup_logging("test_download")
        self.temp_dir = tempfile.mkdtemp()
        self.data_raw_dir = Path(self.temp_dir) / "data" / "raw"
        self.data_raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a mock verification status file (simulating T011 completion)
        self.verification_file = self.data_raw_dir.parent.parent / "data" / "raw" / "verification_status.json"
        self.verification_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.verification_file, 'w') as f:
            json.dump({
                "verified": True,
                "material": "316L",
                "timestamp": "2024-01-01T00:00:00Z"
            }, f)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('download_data.urllib.request.urlopen')
    def test_fetch_record_metadata_network_failure(self, mock_urlopen):
        """Test that fetch_record_metadata raises RuntimeError on network failure"""
        # Configure mock to raise an exception
        mock_urlopen.side_effect = Exception("Network timeout: Unable to connect")
        
        with self.assertRaises(RuntimeError) as context:
            fetch_record_metadata("https://example.com/metadata")
        
        self.assertIn("Failed to fetch metadata", str(context.exception))
        mock_urlopen.assert_called_once()

    @patch('download_data.urllib.request.urlopen')
    def test_verify_material_type_network_failure(self, mock_urlopen):
        """Test that verify_material_type raises RuntimeError on network failure"""
        mock_urlopen.side_effect = Exception("Connection refused")
        
        with self.assertRaises(RuntimeError) as context:
            verify_material_type("https://example.com/data.csv")
        
        self.assertIn("Failed to verify material", str(context.exception))
        mock_urlopen.assert_called_once()

    @patch('download_data.urllib.request.urlretrieve')
    def test_download_file_network_failure(self, mock_urlretrieve):
        """Test that download_file raises RuntimeError on network failure"""
        mock_urlretrieve.side_effect = Exception("Download failed: Connection reset")
        
        url = "https://example.com/data.csv"
        output_path = str(self.data_raw_dir / "test.csv")
        
        with self.assertRaises(RuntimeError) as context:
            download_file(url, output_path)
        
        self.assertIn("Failed to download file", str(context.exception))
        mock_urlretrieve.assert_called_once()

    @patch('download_data.urllib.request.urlretrieve')
    @patch('download_data.Path.exists')
    def test_download_file_no_synthetic_fallback(self, mock_exists, mock_urlretrieve):
        """
        Test that download_file does NOT create a synthetic file when download fails.
        
        This is the critical test for T046: ensuring no synthetic fallback occurs.
        """
        # Mock URL retrieval to fail
        mock_urlretrieve.side_effect = Exception("Network error")
        
        # Ensure the output file doesn't exist initially
        mock_exists.return_value = False
        
        url = "https://example.com/data.csv"
        output_path = str(self.data_raw_dir / "synthetic_test.csv")
        
        # Attempt to download - should raise RuntimeError
        with self.assertRaises(RuntimeError):
            download_file(url, output_path)
        
        # CRITICAL: Verify that NO file was created (no synthetic fallback)
        self.assertFalse(
            os.path.exists(output_path),
            "Synthetic file was created after download failure - this violates the no-synthetic-fallback rule!"
        )

    @patch('download_data.fetch_record_metadata')
    @patch('download_data.verify_material_type')
    @patch('download_data.download_file')
    @patch('download_data.main')
    def test_main_handles_network_failure_gracefully(self, mock_main, mock_download, mock_verify, mock_fetch):
        """Test that main() properly handles network failures without creating synthetic files"""
        # Configure mocks to simulate network failure
        mock_fetch.return_value = {"id": "test-id", "metadata": {}}
        mock_verify.return_value = True
        mock_download.side_effect = RuntimeError("Network failure: Connection timeout")
        
        with self.assertRaises(RuntimeError) as context:
            main()
        
        self.assertIn("Network failure", str(context.exception))
        
        # Verify no synthetic file creation was attempted
        self.assertFalse(mock_main.called)

    @patch('download_data.urllib.request.urlretrieve')
    def test_download_file_timeout_exception(self, mock_urlretrieve):
        """Test handling of timeout exceptions specifically"""
        from urllib.error import URLError
        
        mock_urlretrieve.side_effect = URLError("Timeout")
        
        url = "https://example.com/data.csv"
        output_path = str(self.data_raw_dir / "timeout_test.csv")
        
        with self.assertRaises(RuntimeError) as context:
            download_file(url, output_path)
        
        self.assertIn("Failed to download file", str(context.exception))
        self.assertFalse(os.path.exists(output_path))

    @patch('download_data.urllib.request.urlretrieve')
    def test_download_file_http_error(self, mock_urlretrieve):
        """Test handling of HTTP errors (404, 500, etc.)"""
        from urllib.error import HTTPError
        
        mock_response = Mock()
        mock_response.code = 404
        mock_urlretrieve.side_effect = HTTPError("https://example.com/data.csv", 404, "Not Found", {}, None)
        
        url = "https://example.com/data.csv"
        output_path = str(self.data_raw_dir / "http_error_test.csv")
        
        with self.assertRaises(RuntimeError) as context:
            download_file(url, output_path)
        
        self.assertIn("Failed to download file", str(context.exception))
        self.assertFalse(os.path.exists(output_path))

    def test_no_synthetic_data_in_download_file(self):
        """
        Static analysis test: Verify download_data.py does not contain synthetic data generation code.
        
        This ensures the implementation adheres to the "fail loudly" principle.
        """
        download_file_path = Path(__file__).parent.parent.parent / "code" / "download_data.py"
        
        if not download_file_path.exists():
            self.fail("download_data.py not found")
        
        with open(download_file_path, 'r') as f:
            content = f.read()
        
        # Check for common synthetic data patterns that should NOT exist
        forbidden_patterns = [
            'generate_synthetic',
            'mock_data',
            'np.random',
            'pd.DataFrame({',  # Direct DataFrame creation with hardcoded values
            'synthetic',
            'fake',
            'placeholder'
        ]
        
        for pattern in forbidden_patterns:
            self.assertNotIn(
                pattern, 
                content, 
                f"Found forbidden pattern '{pattern}' in download_data.py - synthetic data generation detected!"
            )

    @patch('download_data.urllib.request.urlretrieve')
    def test_download_file_creates_no_files_on_multiple_failures(self, mock_urlretrieve):
        """Test that multiple network failures don't result in any file creation"""
        mock_urlretrieve.side_effect = Exception("Repeated network failures")
        
        url = "https://example.com/data.csv"
        output_path = str(self.data_raw_dir / "multi_fail_test.csv")
        
        # Try multiple times
        for i in range(3):
            with self.assertRaises(RuntimeError):
                download_file(url, output_path)
        
        # Verify absolutely no file was created
        self.assertFalse(
            os.path.exists(output_path),
            "File was created after multiple download failures!"
        )

if __name__ == '__main__':
    unittest.main()