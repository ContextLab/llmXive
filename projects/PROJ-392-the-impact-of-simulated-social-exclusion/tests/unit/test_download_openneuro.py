"""
Unit tests for code/data_download/download_openneuro.py
"""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import json
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data_download.download_openneuro import (
    DATASETS,
    check_dependencies,
    validate_bids_structure,
    process_dataset,
    main
)

class TestDownloadOpenNeuro(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        
        # Mock the PROJECT_ROOT and sys.path logic if necessary
        # Since the script sets sys.path in the module, we ensure imports work
        # by running tests in an environment where the module is importable.
        
        # Create mock dataset structure
        self.mock_dataset_dir = self.project_root / "data" / "raw-fmri" / "ds000246"
        self.mock_dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a mock dataset_description.json
        desc_file = self.mock_dataset_dir / "dataset_description.json"
        desc_file.write_text(json.dumps({
            "Name": "Test Dataset",
            "BIDSVersion": "1.6.0"
        }))
        
        # Create a mock sub directory
        sub_dir = self.mock_dataset_dir / "sub-01"
        sub_dir.mkdir()
        (sub_dir / "func").mkdir()
        (sub_dir / "func" / "task-exclusion_bold.nii.gz").touch()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch('code.data_download.download_openneuro.subprocess.run')
    def test_check_dependencies_success(self, mock_run):
        """Test that check_dependencies returns True when tools are found."""
        mock_run.return_value = MagicMock(returncode=0)
        result = check_dependencies()
        # Note: check_dependencies checks for curl AND openneuro-cli
        # If openneuro is missing, it returns True but logs warning.
        # If curl is missing, it returns False.
        # We mock subprocess to succeed for both.
        # The function checks curl first.
        # Then checks openneuro.
        # If openneuro fails, it returns True (fallback).
        # So if both succeed, it returns True.
        self.assertTrue(result)

    @patch('code.data_download.download_openneuro.subprocess.run')
    def test_check_dependencies_missing_curl(self, mock_run):
        """Test that check_dependencies returns False when curl is missing."""
        # First call (curl) fails
        mock_run.side_effect = FileNotFoundError("curl not found")
        result = check_dependencies()
        self.assertFalse(result)

    def test_validate_bids_structure_valid(self):
        """Test validation with a valid BIDS structure."""
        result = validate_bids_structure(self.mock_dataset_dir, "ds000246")
        self.assertTrue(result)

    def test_validate_bids_structure_missing_desc(self):
        """Test validation fails when dataset_description.json is missing."""
        desc_file = self.mock_dataset_dir / "dataset_description.json"
        desc_file.unlink()
        
        result = validate_bids_structure(self.mock_dataset_dir, "ds000246")
        self.assertFalse(result)

    def test_validate_bids_structure_missing_dir(self):
        """Test validation fails when directory does not exist."""
        non_existent = self.project_root / "non_existent"
        result = validate_bids_structure(non_existent, "ds000246")
        self.assertFalse(result)

    @patch('code.data_download.download_openneuro.download_with_curl')
    @patch('code.data_download.download_openneuro.validate_bids_structure')
    @patch('code.data_download.download_openneuro.generate_checksum_manifest')
    @patch('code.data_download.download_openneuro.generate_provenance_sidecar')
    def test_process_dataset_success(
        self, mock_prov, mock_checksum, mock_validate, mock_download
    ):
        """Test successful processing of a dataset."""
        mock_download.return_value = True
        mock_validate.return_value = True
        
        # Mock the output directory to exist (created in setup)
        output_dir = self.mock_dataset_dir
        
        # We need to patch the DATASETS config to point to our temp dir
        # But process_dataset uses the global DATASETS which has hardcoded paths.
        # We will patch the specific path in the function or use a different approach.
        # For unit testing, we can mock the Path operations.
        
        # Actually, let's just test the logic flow with mocks.
        # We need to ensure the function doesn't crash with our temp dir setup.
        # Since process_dataset uses global DATASETS, we might need to patch it.
        
        with patch('code.data_download.download_openneuro.DATASETS', {
            "ds000246": {
                "name": "Test",
                "output_dir": str(self.mock_dataset_dir),
                "expected_tasks": ["exclusion"]
            }
        }):
            result = process_dataset("ds000246")
            self.assertTrue(result)
            mock_download.assert_called_once()
            mock_validate.assert_called_once()
            mock_checksum.assert_called_once()
            mock_prov.assert_called_once()

    @patch('code.data_download.download_openneuro.download_with_curl')
    def test_process_dataset_download_failure(self, mock_download):
        """Test process_dataset returns False if download fails."""
        mock_download.return_value = False
        
        with patch('code.data_download.download_openneuro.DATASETS', {
            "ds000246": {
                "name": "Test",
                "output_dir": str(self.mock_dataset_dir),
                "expected_tasks": ["exclusion"]
            }
        }):
            result = process_dataset("ds000246")
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()