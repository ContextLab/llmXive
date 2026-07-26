"""
Unit tests for the GPU Escape Hatch mechanism.
"""
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import json

from code.escape_hatch import KaggleGPUEscapeHatch

class TestKaggleGPUEscapeHatch(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = {
            "kaggle": {
                "kernel_id": "test_kernel_123"
            }
        }
        self.original_username = os.environ.get("KAGGLE_USERNAME")
        self.original_key = os.environ.get("KAGGLE_KEY")
        
        # Set up test environment variables
        os.environ["KAGGLE_USERNAME"] = "test_user"
        os.environ["KAGGLE_KEY"] = "test_key"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.original_username:
            os.environ["KAGGLE_USERNAME"] = self.original_username
        elif "KAGGLE_USERNAME" in os.environ:
            del os.environ["KAGGLE_USERNAME"]
            
        if self.original_key:
            os.environ["KAGGLE_KEY"] = self.original_key
        elif "KAGGLE_KEY" in os.environ:
            del os.environ["KAGGLE_KEY"]

    @patch('code.escape_hatch.load_config')
    @patch('os.path.exists', return_value=True)
    @patch('subprocess.run')
    def test_activate_with_valid_credentials(self, mock_run, mock_exists, mock_load_config):
        """Test activation with valid credentials and kernel ID."""
        mock_load_config.return_value = self.mock_config
        mock_run.return_value = MagicMock(returncode=0)
        
        escape_hatch = KaggleGPUEscapeHatch()
        success = escape_hatch.activate("Test failure")
        
        self.assertTrue(success)
        mock_run.assert_called_once()

    @patch('code.escape_hatch.load_config')
    def test_activate_without_kernel_id(self, mock_load_config):
        """Test activation fails when kernel ID is missing."""
        mock_load_config.return_value = {}
        
        escape_hatch = KaggleGPUEscapeHatch()
        success = escape_hatch.activate("Test failure")
        
        self.assertFalse(success)

    @patch('code.escape_hatch.load_config')
    def test_activate_without_credentials(self, mock_load_config):
        """Test activation fails when credentials are missing."""
        mock_load_config.return_value = self.mock_config
        
        # Remove credentials
        if "KAGGLE_USERNAME" in os.environ:
            del os.environ["KAGGLE_USERNAME"]
        if "KAGGLE_KEY" in os.environ:
            del os.environ["KAGGLE_KEY"]
        
        escape_hatch = KaggleGPUEscapeHatch()
        success = escape_hatch.activate("Test failure")
        
        self.assertFalse(success)

    @patch('code.escape_hatch.load_config')
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.chmod')
    @patch('subprocess.run')
    def test_prepare_kaggle_json_creates_file(
        self, mock_run, mock_chmod, mock_open_file, mock_exists, mock_load_config
    ):
        """Test that kaggle.json is created when missing."""
        mock_load_config.return_value = self.mock_config
        mock_run.return_value = MagicMock(returncode=0)
        
        escape_hatch = KaggleGPUEscapeHatch()
        success = escape_hatch.activate("Test failure")
        
        self.assertTrue(success)
        mock_open_file.assert_called()
        mock_chmod.assert_called()

    @patch('code.escape_hatch.load_config')
    @patch('subprocess.run')
    def test_kaggle_cli_not_found(self, mock_run, mock_load_config):
        """Test failure when kaggle CLI is not found."""
        mock_load_config.return_value = self.mock_config
        mock_run.return_value = MagicMock(returncode=1, stderr="command not found")
        
        escape_hatch = KaggleGPUEscapeHatch()
        success = escape_hatch.activate("Test failure")
        
        self.assertFalse(success)

    @patch('code.escape_hatch.load_config')
    @patch('subprocess.run')
    def test_kernel_trigger_timeout(self, mock_run, mock_load_config):
        """Test failure when kernel trigger times out."""
        mock_load_config.return_value = self.mock_config
        mock_run.side_effect = TimeoutError("Timed out")
        
        escape_hatch = KaggleGPUEscapeHatch()
        success = escape_hatch.activate("Test failure")
        
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()