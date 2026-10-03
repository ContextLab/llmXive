"""
Tests for the NF-BoT-IoT dataset download functionality.
"""
import os
import sys
import tempfile
import hashlib
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.data.download_bot_iot import (
    calculate_sha256,
    download_file,
    validate_file,
    download_bot_iot_dataset,
    trigger_fallback
)

class TestCalculateSha256(unittest.TestCase):
    def test_calculate_sha256(self):
        """Test SHA256 calculation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        try:
            expected_hash = hashlib.sha256(b"test data").hexdigest()
            actual_hash = calculate_sha256(tmp_path)
            self.assertEqual(actual_hash, expected_hash)
        finally:
            os.unlink(tmp_path)

    def test_calculate_sha256_file_not_found(self):
        """Test SHA256 calculation with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            calculate_sha256("non_existent_file.txt")

class TestDownloadFile(unittest.TestCase):
    @patch('urllib.request.urlretrieve')
    def test_download_success(self, mock_urlretrieve):
        """Test successful download."""
        mock_urlretrieve.return_value = None
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            result = download_file("http://example.com/file.csv", tmp_path)
            self.assertTrue(result)
            mock_urlretrieve.assert_called_once_with("http://example.com/file.csv", tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch('urllib.request.urlretrieve')
    def test_download_failure(self, mock_urlretrieve):
        """Test failed download."""
        mock_urlretrieve.side_effect = Exception("Network error")
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            result = download_file("http://example.com/file.csv", tmp_path)
            self.assertFalse(result)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

class TestValidateFile(unittest.TestCase):
    def test_validate_file_success(self):
        """Test successful validation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        try:
            expected_hash = hashlib.sha256(b"test data").hexdigest()
            result = validate_file(tmp_path, expected_hash)
            self.assertTrue(result)
        finally:
            os.unlink(tmp_path)

    def test_validate_file_failure(self):
        """Test failed validation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        try:
            result = validate_file(tmp_path, "wrong_hash")
            self.assertFalse(result)
        finally:
            os.unlink(tmp_path)

    def test_validate_file_not_found(self):
        """Test validation with non-existent file."""
        result = validate_file("non_existent_file.txt", "some_hash")
        self.assertFalse(result)

class TestTriggerFallback(unittest.TestCase):
    def test_trigger_fallback_raises_error(self):
        """Test that trigger_fallback raises an error."""
        with self.assertRaises(RuntimeError):
            trigger_fallback()

class TestDownloadBotIotDataset(unittest.TestCase):
    @patch('code.data.download_bot_iot.download_file')
    @patch('code.data.download_bot_iot.validate_file')
    @patch('code.data.download_bot_iot.load_state')
    @patch('code.data.download_bot_iot.update_state')
    def test_download_and_validate_success(self, mock_update_state, mock_load_state, mock_validate, mock_download):
        """Test successful download and validation."""
        mock_download.return_value = True
        mock_validate.return_value = True
        mock_load_state.return_value = {}
        
        # Mock os.makedirs to avoid file system changes
        with patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch('code.data.download_bot_iot.OUTPUT_FILE', '/tmp/test.csv'):
            
            result = download_bot_iot_dataset()
            self.assertTrue(result)
            mock_download.assert_called_once()
            mock_validate.assert_called_once()

    @patch('code.data.download_bot_iot.download_file')
    @patch('code.data.download_bot_iot.validate_file')
    @patch('code.data.download_bot_iot.trigger_fallback')
    def test_download_failure_triggers_fallback(self, mock_fallback, mock_validate, mock_download):
        """Test that download failure triggers fallback."""
        mock_download.return_value = False
        
        with patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch('code.data.download_bot_iot.OUTPUT_FILE', '/tmp/test.csv'):
            
            with self.assertRaises(RuntimeError):
                download_bot_iot_dataset()
            mock_fallback.assert_called_once()

    @patch('code.data.download_bot_iot.download_file')
    @patch('code.data.download_bot_iot.validate_file')
    @patch('code.data.download_bot_iot.trigger_fallback')
    def test_validation_failure_triggers_fallback(self, mock_fallback, mock_validate, mock_download):
        """Test that validation failure triggers fallback."""
        mock_download.return_value = True
        mock_validate.return_value = False
        
        with patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch('code.data.download_bot_iot.OUTPUT_FILE', '/tmp/test.csv'):
            
            with self.assertRaises(RuntimeError):
                download_bot_iot_dataset()
            mock_fallback.assert_called_once()

if __name__ == '__main__':
    unittest.main()