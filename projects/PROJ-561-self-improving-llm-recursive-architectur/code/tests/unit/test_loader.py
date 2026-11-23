import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os
import time
import tempfile
import hashlib
import requests

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.loader import (
    verify_urls, 
    download_and_checksum, 
    calculate_directory_checksum,
    HFTransientError,
    exponential_backoff
)

class TestLoaderFunctions(unittest.TestCase):

    def test_verify_urls_success(self):
        """Test that verify_urls returns True for valid URLs."""
        with patch('pipeline.loader.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            urls = ["https://example.com", "https://huggingface.co"]
            result = verify_urls(urls)
            self.assertTrue(result)
            self.assertEqual(mock_head.call_count, 2)

    def test_verify_urls_failure(self):
        """Test that verify_urls raises error for invalid URLs."""
        with patch('pipeline.loader.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_head.return_value = mock_response
            
            urls = ["https://invalid-url-12345.com"]
            with self.assertRaises(HFTransientError):
                verify_urls(urls)

    def test_verify_urls_empty_list(self):
        """Test that verify_urls returns True for empty list."""
        result = verify_urls([])
        self.assertTrue(result)

    def test_exponential_backoff_retry_logic(self):
        """Test that the decorator retries on failure."""
        call_count = 0
        
        @exponential_backoff
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise HFTransientError("Transient error")
            return "success"
        
        # Patch time.sleep to speed up test
        with patch('pipeline.loader.time.sleep'):
            result = failing_func()
            self.assertEqual(result, "success")
            self.assertEqual(call_count, 3)

    def test_download_and_checksum_creates_file(self):
        """Test that download_and_checksum creates the destination directory and returns a checksum."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = os.path.join(tmp_dir, "test_dataset")
            
            # Mock load_dataset to avoid actual download
            with patch('pipeline.loader.load_dataset') as mock_load:
                mock_dataset = MagicMock()
                mock_dataset.save_to_disk = MagicMock()
                mock_load.return_value = mock_dataset
                
                # Mock calculate_directory_checksum to return a fixed value
                with patch('pipeline.loader.calculate_directory_checksum') as mock_calc:
                    mock_calc.return_value = "abc123checksum"
                    
                    checksum = download_and_checksum("test_dataset", dest_path)
                    
                    self.assertEqual(checksum, "abc123checksum")
                    self.assertTrue(os.path.exists(dest_path))
                    mock_dataset.save_to_disk.assert_called_once()

    def test_calculate_directory_checksum(self):
        """Test directory checksum calculation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a file
            file_path = os.path.join(tmp_dir, "test.txt")
            with open(file_path, "w") as f:
                f.write("hello world")
            
            checksum = calculate_directory_checksum(tmp_dir)
            self.assertIsInstance(checksum, str)
            self.assertEqual(len(checksum), 64) # SHA256 hex length

    def test_calculate_directory_checksum_empty(self):
        """Test directory checksum for empty directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            checksum = calculate_directory_checksum(tmp_dir)
            # Hash of empty input
            expected = hashlib.sha256().hexdigest()
            self.assertEqual(checksum, expected)

    def test_calculate_directory_checksum_nonexistent(self):
        """Test that checksum raises error for non-existent directory."""
        with self.assertRaises(FileNotFoundError):
            calculate_directory_checksum("/nonexistent/path")

    @patch('pipeline.loader.load_dataset')
    @patch('pipeline.loader.calculate_directory_checksum')
    def test_load_openwebtext(self, mock_calc, mock_load):
        """Test load_openwebtext wrapper."""
        mock_calc.return_value = "checksum123"
        mock_dataset = MagicMock()
        mock_load.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "owt")
            result = load_openwebtext(path)
            
            self.assertEqual(result, path)
            mock_load.assert_called_once_with("openwebtext", trust_remote_code=False)
            mock_dataset.save_to_disk.assert_called_once()

    @patch('pipeline.loader.load_dataset')
    @patch('pipeline.loader.calculate_directory_checksum')
    def test_load_gsm8k(self, mock_calc, mock_load):
        """Test load_gsm8k wrapper."""
        mock_calc.return_value = "checksum456"
        mock_dataset = MagicMock()
        mock_load.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "gsm8k")
            result = load_gsm8k(path)
            
            self.assertEqual(result, path)
            mock_load.assert_called_once_with("gsm8k", trust_remote_code=False)

    @patch('pipeline.loader.load_dataset')
    @patch('pipeline.loader.calculate_directory_checksum')
    def test_load_boolq(self, mock_calc, mock_load):
        """Test load_boolq wrapper."""
        mock_calc.return_value = "checksum789"
        mock_dataset = MagicMock()
        mock_load.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "boolq")
            result = load_boolq(path)
            
            self.assertEqual(result, path)
            mock_load.assert_called_once_with("boolq", trust_remote_code=False)

    @patch('pipeline.loader.load_dataset')
    @patch('pipeline.loader.calculate_directory_checksum')
    def test_load_arc_challenge(self, mock_calc, mock_load):
        """Test load_arc_challenge wrapper (uses ai2_arc)."""
        mock_calc.return_value = "checksumarc"
        mock_dataset = MagicMock()
        mock_load.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "arc")
            result = load_arc_challenge(path)
            
            self.assertEqual(result, path)
            # Verify it calls with 'ai2_arc'
            mock_load.assert_called_once_with("ai2_arc", trust_remote_code=False)

    @patch('pipeline.loader.load_dataset')
    @patch('pipeline.loader.calculate_directory_checksum')
    def test_load_and_verify(self, mock_calc, mock_load):
        """Test load_and_verify function."""
        mock_calc.return_value = "checksum_verify"
        mock_dataset = MagicMock()
        mock_load.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "verify")
            result_path, result_checksum = load_and_verify("test", path)
            
            self.assertEqual(result_path, path)
            self.assertEqual(result_checksum, "checksum_verify")

    @patch('pipeline.loader.load_dataset')
    def test_load_local_dataset(self, mock_load):
        """Test load_local_dataset."""
        mock_load.return_value = "dataset_obj"
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a dummy file to satisfy os.path.exists
            with open(os.path.join(tmp_dir, "dummy"), "w") as f:
                f.write("x")
            
            result = load_local_dataset(tmp_dir)
            self.assertEqual(result, "dataset_obj")
            mock_load.assert_called_once_with(tmp_dir)

    @patch('pipeline.loader.load_dataset')
    def test_load_all_datasets(self, mock_load):
        """Test load_all_datasets orchestrator."""
        mock_dataset = MagicMock()
        mock_load.return_value = mock_dataset
        
        with patch('pipeline.loader.calculate_directory_checksum') as mock_calc:
            mock_calc.return_value = "cs"
            
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Patch the paths to use temp dir
                with patch('pipeline.loader.os.makedirs'):
                    results = load_all_datasets()
                    
                    self.assertIn("openwebtext", results)
                    self.assertIn("gsm8k", results)
                    self.assertIn("arc_challenge", results)
                    self.assertIn("boolq", results)
                    # arc_challenge uses ai2_arc
                    # Check that ai2_arc was called
                    calls = [str(call) for call in mock_load.call_args_list]
                    ai2_called = any("ai2_arc" in c for c in calls)
                    self.assertTrue(ai2_called)

if __name__ == '__main__':
    unittest.main()
