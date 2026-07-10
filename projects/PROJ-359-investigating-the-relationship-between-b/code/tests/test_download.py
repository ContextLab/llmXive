"""
Tests for download.py functionality.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest import TestCase, mock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.download import get_dataset_files, main, DATASET_ID

class TestDownloadUtils(TestCase):
    
    def test_get_dataset_files_valid(self):
        """Test fetching file list with a mock response."""
        mock_data = {
            "files": [
                {"filename": "sub-01/func/sub-01_task-rest_bold.nii.gz", "path": "sub-01/func/sub-01_task-rest_bold.nii.gz"},
                {"filename": "dataset_description.json", "path": "dataset_description.json"}
            ]
        }
        
        with mock.patch('src.download.requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.json.return_value = mock_data
            mock_response.raise_for_status = mock.Mock()
            mock_get.return_value = mock_response
            
            files = get_dataset_files(DATASET_ID)
            self.assertEqual(len(files), 2)
            self.assertEqual(files[0]["filename"], "sub-01/func/sub-01_task-rest_bold.nii.gz")

    def test_get_dataset_files_empty(self):
        """Test fetching file list when empty."""
        mock_data = {"files": []}
        
        with mock.patch('src.download.requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.json.return_value = mock_data
            mock_response.raise_for_status = mock.Mock()
            mock_get.return_value = mock_response
            
            files = get_dataset_files(DATASET_ID)
            self.assertEqual(len(files), 0)

    def test_get_dataset_files_error(self):
        """Test fetching file list with network error."""
        with mock.patch('src.download.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with self.assertRaises(RuntimeError):
                get_dataset_files(DATASET_ID)

class TestDownloadIntegration(TestCase):
    """Integration tests for main() logic."""
    
    def test_main_no_files_found(self):
        """Test main() exits with error when no bold files found."""
        mock_files = [
            {"filename": "dataset_description.json", "path": "dataset_description.json"},
            {"filename": "participants.tsv", "path": "participants.tsv"}
        ]
        
        with mock.patch('src.download.get_dataset_files', return_value=mock_files):
            with mock.patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(1)

    def test_main_partial_success(self):
        """Test main() handles partial download."""
        mock_files = [
            {"filename": "sub-01/func/sub-01_task-rest_bold.nii.gz", "path": "sub-01/func/sub-01_task-rest_bold.nii.gz"}
        ]
        
        with mock.patch('src.download.get_dataset_files', return_value=mock_files):
            with mock.patch('src.download.download_file', side_effect=RuntimeError("Simulated download error")):
                with mock.patch('sys.exit') as mock_exit:
                    # Should exit 0 for partial or 1 for total failure depending on logic
                    # Our logic: if downloaded_count == 0 -> exit 1. If partial -> exit 0.
                    main()
                    # Since downloaded_count is 0, it should exit 1
                    mock_exit.assert_called_with(1)