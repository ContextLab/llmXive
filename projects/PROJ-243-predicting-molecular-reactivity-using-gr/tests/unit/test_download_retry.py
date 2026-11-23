"""
tests/unit/test_download_retry.py

Unit tests for the download retry logic in code/data/download.py.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock, Mock
from io import StringIO

# Add parent to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.download import download_with_retry, orchestrate_download
from code.config import get_config

class TestDownloadRetry(unittest.TestCase):
    """Test cases for the download retry mechanism."""

    def setUp(self):
        """Set up temporary directory and logger for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")
        
        # Mock logger
        self.mock_logger = MagicMock()
        self.mock_logger.info = MagicMock()
        self.mock_logger.warning = MagicMock()
        self.mock_logger.error = MagicMock()
        self.mock_logger.critical = MagicMock()

    @patch('code.data.download.urllib.request.urlretrieve')
    def test_download_success_first_attempt(self, mock_urlretrieve):
        """Test successful download on the first attempt."""
        mock_urlretrieve.return_value = None
        
        success, message = download_with_retry(
            url="http://example.com/file.txt",
            dest_path=self.test_file,
            logger=self.mock_logger,
            max_retries=3
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Download successful")
        self.assertEqual(self.mock_logger.info.call_count, 2) # Start + Success
        mock_urlretrieve.assert_called_once()

    @patch('code.data.download.urllib.request.urlretrieve')
    @patch('code.data.download.time.sleep')
    def test_download_success_after_retry(self, mock_sleep, mock_urlretrieve):
        """Test successful download after one failure."""
        from urllib.error import URLError
        
        # Fail once, then succeed
        mock_urlretrieve.side_effect = [
            URLError("Connection timeout"),
            None
        ]
        
        success, message = download_with_retry(
            url="http://example.com/file.txt",
            dest_path=self.test_file,
            logger=self.mock_logger,
            max_retries=3,
            initial_backoff=0.01 # Fast test
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Download successful")
        self.assertEqual(mock_urlretrieve.call_count, 2)
        self.assertEqual(self.mock_logger.warning.call_count, 1)
        self.assertEqual(self.mock_logger.info.call_count, 3) # Attempt 1, Retry msg, Attempt 2, Success

    @patch('code.data.download.urllib.request.urlretrieve')
    @patch('code.data.download.time.sleep')
    def test_download_exhausted_retries(self, mock_sleep, mock_urlretrieve):
        """Test behavior when all retries are exhausted."""
        from urllib.error import URLError
        
        # Fail every time
        mock_urlretrieve.side_effect = URLError("Connection timeout")
        
        success, message = download_with_retry(
            url="http://example.com/file.txt",
            dest_path=self.test_file,
            logger=self.mock_logger,
            max_retries=2, # 2 retries + 1 initial = 3 attempts
            initial_backoff=0.01
        )
        
        self.assertFalse(success)
        self.assertIn("failed after", message)
        self.assertEqual(mock_urlretrieve.call_count, 3)
        self.mock_logger.error.assert_called()
        self.mock_logger.critical.assert_not_called() # critical is in orchestrate_download

    @patch('code.data.download.urllib.request.urlretrieve')
    @patch('code.data.download.calculate_sha256')
    def test_download_checksum_mismatch(self, mock_sha256, mock_urlretrieve):
        """Test handling of checksum mismatch."""
        mock_urlretrieve.return_value = None
        mock_sha256.return_value = "wrong_hash"
        
        success, message = download_with_retry(
            url="http://example.com/file.txt",
            dest_path=self.test_file,
            logger=self.mock_logger,
            expected_sha256="correct_hash"
        )
        
        self.assertFalse(success)
        self.assertIn("Checksum mismatch", message)
        self.assertTrue(os.path.exists(self.test_file)) # File exists before removal in logic? 
        # Note: In the implementation, os.remove is called inside the function on mismatch.
        # However, since we are mocking, we need to check if the logic path was taken.
        # The implementation calls os.remove(dest_path) inside the try block on mismatch.
        # We can't easily verify file deletion in a mock without side effects, 
        # but we verify the return value and log message.

    def test_orchestrate_download_success(self):
        """Test orchestrate_download returns 0 on success."""
        with patch('code.data.download.download_with_retry') as mock_retry:
            mock_retry.return_value = (True, "Success")
            
            exit_code = orchestrate_download(
                url="http://example.com",
                dest_path=self.test_file,
                logger=self.mock_logger
            )
            
            self.assertEqual(exit_code, 0)
            self.mock_logger.info.assert_called_with("SUCCESS: Success")

    def test_orchestrate_download_failure(self):
        """Test orchestrate_download returns 1 on failure."""
        with patch('code.data.download.download_with_retry') as mock_retry:
            mock_retry.return_value = (False, "Failed")
            
            exit_code = orchestrate_download(
                url="http://example.com",
                dest_path=self.test_file,
                logger=self.mock_logger
            )
            
            self.assertEqual(exit_code, 1)
            self.mock_logger.critical.assert_called_with("FAILURE: Failed")

if __name__ == '__main__':
    unittest.main()