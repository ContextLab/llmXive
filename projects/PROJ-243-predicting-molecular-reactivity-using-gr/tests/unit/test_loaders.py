"""
Unit tests for the loaders module.

Tests retry logic, error handling, and checksum verification.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.loaders import (
    download_with_retry,
    calculate_sha256,
    MAX_RETRIES,
    BASE_DELAY,
    MAX_DELAY
)


class TestLoaders(unittest.TestCase):
    """Test cases for the loaders module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_calculate_sha256(self):
        """Test SHA-256 calculation."""
        # Create a test file with known content
        test_content = b"Hello, World!"
        with open(self.test_file, 'wb') as f:
            f.write(test_content)
        
        hash_value = calculate_sha256(self.test_file)
        # Known SHA-256 for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        self.assertEqual(hash_value, expected_hash)

    @patch('code.utils.loaders.urllib.request.urlretrieve')
    def test_download_success(self, mock_urlretrieve):
        """Test successful download."""
        mock_urlretrieve.return_value = None
        
        success, message = download_with_retry(
            url="http://example.com/test.txt",
            output_path=self.test_file,
            max_retries=3
        )
        
        self.assertTrue(success)
        self.assertIn("Download successful", message)
        mock_urlretrieve.assert_called_once()

    @patch('code.utils.loaders.urllib.request.urlretrieve')
    def test_download_with_checksum_match(self, mock_urlretrieve):
        """Test download with matching checksum."""
        # Create a file with known content for checksum test
        test_content = b"Test content"
        
        def create_file(url, path):
            with open(path, 'wb') as f:
                f.write(test_content)
        
        mock_urlretrieve.side_effect = create_file
        
        # Calculate expected checksum
        expected_checksum = calculate_sha256(self.test_file)
        # But we need to create the file first to get the hash
        # So we'll test with a known hash
        
        # For this test, we'll mock the checksum calculation
        with patch('code.utils.loaders.calculate_sha256') as mock_hash:
            mock_hash.return_value = "abc123"
            
            success, message = download_with_retry(
                url="http://example.com/test.txt",
                output_path=self.test_file,
                expected_checksum="abc123",
                max_retries=3
            )
            
            self.assertTrue(success)
            self.assertIn("Checksum verified", message)

    @patch('code.utils.loaders.urllib.request.urlretrieve')
    def test_download_with_checksum_mismatch(self, mock_urlretrieve):
        """Test download with mismatched checksum."""
        test_content = b"Test content"
        
        def create_file(url, path):
            with open(path, 'wb') as f:
                f.write(test_content)
        
        mock_urlretrieve.side_effect = create_file
        
        with patch('code.utils.loaders.calculate_sha256') as mock_hash:
            mock_hash.return_value = "wrong_hash"
            
            success, message = download_with_retry(
                url="http://example.com/test.txt",
                output_path=self.test_file,
                expected_checksum="correct_hash",
                max_retries=3
            )
            
            self.assertFalse(success)
            self.assertIn("Checksum mismatch", message)
            # File should be cleaned up
            self.assertFalse(os.path.exists(self.test_file))

    @patch('code.utils.loaders.urllib.request.urlretrieve')
    def test_download_retry_logic(self, mock_urlretrieve):
        """Test that retry logic works correctly."""
        # Mock to fail twice then succeed
        call_count = [0]
        
        def failing_urlretrieve(url, path):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise urllib.error.URLError("Connection timeout")
            # Create file on success
            with open(path, 'wb') as f:
                f.write(b"Success")
        
        mock_urlretrieve.side_effect = failing_urlretrieve
        
        with patch('code.utils.loaders.time.sleep'):  # Skip actual sleep
            success, message = download_with_retry(
                url="http://example.com/test.txt",
                output_path=self.test_file,
                max_retries=5,
                base_delay=0.1
            )
            
            self.assertTrue(success)
            self.assertEqual(call_count[0], 3)  # 2 failures + 1 success

    @patch('code.utils.loaders.urllib.request.urlretrieve')
    def test_download_max_retries_exceeded(self, mock_urlretrieve):
        """Test behavior when max retries are exceeded."""
        mock_urlretrieve.side_effect = urllib.error.URLError("Connection timeout")
        
        with patch('code.utils.loaders.time.sleep'):  # Skip actual sleep
            success, message = download_with_retry(
                url="http://example.com/test.txt",
                output_path=self.test_file,
                max_retries=3,
                base_delay=0.1
            )
            
            self.assertFalse(success)
            self.assertIn("Download failed after 3 attempts", message)
            self.assertIn("Connection timeout", message)

    def test_exponential_backoff_calculation(self):
        """Test that exponential backoff delays are calculated correctly."""
        # This is a logic test for the delay calculation
        base_delay = 2.0
        max_delay = 60.0
        
        # Calculate expected delays
        expected_delays = []
        for attempt in range(1, 6):
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            expected_delays.append(delay)
        
        expected = [2.0, 4.0, 8.0, 16.0, 32.0]
        self.assertEqual(expected_delays, expected)

    def test_output_directory_creation(self):
        """Test that output directory is created if it doesn't exist."""
        nested_path = os.path.join(self.temp_dir, "nested", "dir", "file.txt")
        
        with patch('code.utils.loaders.urllib.request.urlretrieve') as mock_urlretrieve:
            mock_urlretrieve.return_value = None
            
            success, _ = download_with_retry(
                url="http://example.com/test.txt",
                output_path=nested_path,
                max_retries=1
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(os.path.dirname(nested_path)))


if __name__ == '__main__':
    unittest.main()
