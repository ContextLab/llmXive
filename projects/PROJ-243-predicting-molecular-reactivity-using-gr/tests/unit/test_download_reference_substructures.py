import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.loaders import download_with_retry, calculate_sha256
from config import get_config, ensure_directories

class TestDownloadReferenceSubstructures(unittest.TestCase):
    """Test cases for reference substructures download functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.test_dir, "data", "raw")
        os.makedirs(self.raw_dir, exist_ok=True)
        
        # Mock config paths for testing
        self.original_config = get_config()
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('urllib.request.urlretrieve')
    def test_download_with_retry_success(self, mock_urlretrieve):
        """Test successful download with retry logic."""
        # Mock successful download
        mock_urlretrieve.return_value = None
        
        output_path = os.path.join(self.raw_dir, "test_file.csv")
        
        # Create a dummy file to simulate successful download
        with open(output_path, 'w') as f:
            f.write("test,data\n1,2\n")
        
        result = download_with_retry(
            "http://example.com/test.csv",
            output_path,
            max_retries=3
        )
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_path))

    @patch('urllib.request.urlretrieve')
    def test_download_with_retry_failure(self, mock_urlretrieve):
        """Test download fails after all retries."""
        # Mock failure
        mock_urlretrieve.side_effect = Exception("Network error")
        
        output_path = os.path.join(self.raw_dir, "test_file.csv")
        
        result = download_with_retry(
            "http://example.com/test.csv",
            output_path,
            max_retries=2,
            backoff_factor=0.1  # Faster retries for testing
        )
        
        self.assertFalse(result)
        self.assertFalse(os.path.exists(output_path))

    def test_calculate_sha256(self):
        """Test SHA-256 calculation."""
        output_path = os.path.join(self.raw_dir, "test_hash.csv")
        
        with open(output_path, 'w') as f:
            f.write("test,data\n1,2\n")
        
        hash_value = calculate_sha256(output_path)
        
        self.assertEqual(len(hash_value), 64)  # SHA-256 produces 64 hex chars
        self.assertIsInstance(hash_value, str)

    def test_ensure_directories(self):
        """Test that ensure_directories creates required folders."""
        # Temporarily change config paths for testing
        import config
        original_get_config = config.get_config
        
        def mock_get_config():
            return {
                "paths": {
                    "raw": os.path.join(self.test_dir, "data", "raw"),
                    "processed": os.path.join(self.test_dir, "data", "processed"),
                    "assets": os.path.join(self.test_dir, "data", "assets"),
                    "code": os.path.join(self.test_dir, "code"),
                    "artifacts": os.path.join(self.test_dir, "artifacts"),
                    "tests": os.path.join(self.test_dir, "tests"),
                    "logs": os.path.join(self.test_dir, "artifacts", "logs")
                }
            }
        
        config.get_config = mock_get_config
        
        try:
            ensure_directories()
            
            # Verify directories were created
            self.assertTrue(os.path.exists(self.raw_dir))
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, "data", "processed")))
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, "data", "assets")))
        finally:
            config.get_config = original_get_config

if __name__ == "__main__":
    unittest.main()
