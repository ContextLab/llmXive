import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.download_nlcd import (
    compute_sha256,
    load_metadata_config,
    save_metadata_config,
    main
)
from utils.config import get_raw_data_dir, get_metadata_file, get_project_root

class TestDownloadNLCD(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_project_root = get_project_root()
        
        # Mock the project root
        import utils.config
        original_get_project_root = utils.config.get_project_root
        utils.config.get_project_root = lambda: Path(self.test_dir)
        
        # Ensure directories exist
        get_raw_data_dir().mkdir(parents=True, exist_ok=True)
        get_metadata_file().parent.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
        # Restore original function
        import utils.config
        utils.config.get_project_root = self.original_project_root

    def test_compute_sha256(self):
        """Test SHA-256 computation."""
        test_file = Path(self.test_dir) / "test.txt"
        test_content = "Hello, World!"
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        hash_result = compute_sha256(test_file)
        self.assertEqual(len(hash_result), 64)  # SHA-256 hex length
        self.assertIsInstance(hash_result, str)

    def test_load_metadata_config_empty(self):
        """Test loading empty metadata."""
        metadata = load_metadata_config()
        self.assertIn("data_sources", metadata)
        self.assertIn("artifacts", metadata)
        self.assertIn("steps", metadata)

    def test_save_metadata_config(self):
        """Test saving metadata configuration."""
        test_metadata = {
            "data_sources": {"test": {"url": "http://test.com"}},
            "artifacts": [],
            "steps": []
        }
        save_metadata_config(test_metadata)
        
        # Verify file exists and can be loaded
        metadata_path = get_metadata_file()
        self.assertTrue(metadata_path.exists())
        
        loaded = load_metadata_config()
        self.assertEqual(loaded["data_sources"]["test"]["url"], "http://test.com")

    @patch('data.download_nlcd.requests.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        from data.download_nlcd import download_file
        
        # Mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"test content"]
        mock_response.headers = {'content-length': '12'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        output_path = Path(self.test_dir) / "downloaded.txt"
        result = download_file("http://test.com/file.txt", output_path)
        
        self.assertTrue(result)
        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            self.assertEqual(f.read(), "test content")

    @patch('data.download_nlcd.requests.get')
    def test_download_file_failure(self, mock_get):
        """Test failed file download raises error."""
        from data.download_nlcd import download_file
        
        mock_get.side_effect = Exception("Network error")
        
        output_path = Path(self.test_dir) / "failed.txt"
        result = download_file("http://test.com/file.txt", output_path)
        
        self.assertFalse(result)
        self.assertFalse(output_path.exists())

    @patch('data.download_nlcd.download_file')
    def test_main_download_success(self, mock_download):
        """Test main function with successful download."""
        from data.download_nlcd import main
        
        mock_download.return_value = True
        
        # Create necessary directories
        get_raw_data_dir().mkdir(parents=True, exist_ok=True)
        
        # Run main
        main()
        
        # Verify metadata was updated
        metadata = load_metadata_config()
        self.assertIn("NLCD", metadata.get("data_sources", {}))

    @patch('data.download_nlcd.download_file')
    def test_main_download_failure(self, mock_download):
        """Test main function with failed download raises FileNotFoundError."""
        from data.download_nlcd import main
        
        mock_download.return_value = False
        
        get_raw_data_dir().mkdir(parents=True, exist_ok=True)
        
        with self.assertRaises(FileNotFoundError):
            main()

if __name__ == '__main__':
    unittest.main()