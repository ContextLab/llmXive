import os
import sys
import json
import unittest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from download import (
    ensure_directories, 
    validate_and_aggregate, 
    check_validation_and_halt,
    fetch_openneuro_data,
    DATA_PROCESSED_DIR
)

class TestDownloadValidationHalt(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory structure for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        
        # Mock the global paths used in download.py
        self.original_project_root = None
        self.original_data_processed = None
        
        # We need to monkey-patch the module level variables if possible, 
        # but since they are evaluated at import time, we will mock the file system interactions
        # specifically for the functions we test.
        
        # Setup directories structure
        (self.project_root / "data" / "processed").mkdir(parents=True)
        (self.project_root / "data" / "raw").mkdir(parents=True)
        
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.data_raw_dir = self.project_root / "data" / "raw"

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_halt_on_zero_valid_subjects_writes_log(self):
        """
        Test that check_validation_and_halt writes to validation_errors.log 
        with prefix [VALIDATION_ERROR] and raises ValueError when count is 0.
        """
        # Prepare a mock result with 0 subjects
        mock_result = {"subjects": [], "count": 0}
        
        # Ensure the log file path exists
        log_path = self.data_processed_dir / "validation_errors.log"
        
        # We need to mock the DATA_PROCESSED_DIR inside the download module
        # Since it's a global constant, we patch the function's behavior or the path resolution.
        # A cleaner way for this specific test is to patch the open function and the path check.
        
        # Create a context where DATA_PROCESSED_DIR points to our test dir
        # We will re-implement the logic of check_validation_and_halt locally or patch the module.
        # Given the constraints, let's patch the specific file write and the path.
        
        import download as download_module
        
        original_path = download_module.DATA_PROCESSED_DIR
        download_module.DATA_PROCESSED_DIR = self.data_processed_dir
        
        try:
            with self.assertRaises(ValueError) as context:
                check_validation_and_halt(mock_result)
            
            self.assertEqual(str(context.exception), "No valid Fluid Intelligence data found in specified datasets")
            
            # Verify the log file was created and contains the correct prefix
            self.assertTrue(log_path.exists(), "validation_errors.log was not created")
            
            with open(log_path, 'r') as f:
                content = f.read()
            
            self.assertIn("[VALIDATION_ERROR]", content, "Log does not contain [VALIDATION_ERROR] prefix")
            self.assertIn("No valid Fluid Intelligence data found in specified datasets", content)
            
        finally:
            # Restore original path
            download_module.DATA_PROCESSED_DIR = original_path

    @patch('download.download_dataset')
    @patch('download.get_subject_list')
    @patch('download.validate_and_aggregate')
    @patch('download.check_validation_and_halt')
    def test_fetch_openneuro_halt_on_zero(self, mock_halt, mock_validate, mock_get_sub, mock_download):
        """
        Test that fetch_openneuro_data halts (raises) if validation returns 0 subjects.
        """
        # Setup mocks
        mock_get_sub.return_value = ["sub-01"]
        mock_validate.return_value = {"subjects": [], "count": 0}
        mock_download.return_value = True
        
        # Mock the halt function to raise ValueError as it should
        mock_halt.side_effect = ValueError("No valid Fluid Intelligence data found in specified datasets")
        
        # We need to temporarily set the global DATA_PROCESSED_DIR for the main function
        # to write the log file to our test location if we were testing the file write here,
        # but the task focuses on the halt logic and log write.
        # The test `test_halt_on_zero_valid_subjects_writes_log` covers the file write.
        # This test covers the flow.
        
        import download as download_module
        original_path = download_module.DATA_PROCESSED_DIR
        download_module.DATA_PROCESSED_DIR = self.data_processed_dir
        
        try:
            with self.assertRaises(ValueError):
                fetch_openneuro_data()
        finally:
            download_module.DATA_PROCESSED_DIR = original_path

    def test_validate_and_aggregate_creates_json(self):
        """
        Test that validate_and_aggregate creates valid_subjects.json with correct schema.
        """
        # Create a mock subject directory with behavioral data
        sub_dir = self.data_raw_dir / "sub-01"
        sub_dir.mkdir(parents=True)
        
        # Create a mock behavioral file
        behavioral_file = sub_dir / "behaviors.json"
        with open(behavioral_file, 'w') as f:
            json.dump({"FluidIntelligence": 85.5}, f)
        
        subjects = ["sub-01"]
        
        import download as download_module
        original_path = download_module.DATA_PROCESSED_DIR
        download_module.DATA_PROCESSED_DIR = self.data_processed_dir
        
        try:
            result = validate_and_aggregate(subjects, self.data_raw_dir)
            
            self.assertEqual(result["count"], 1)
            self.assertEqual(len(result["subjects"]), 1)
            self.assertEqual(result["subjects"][0]["id"], "sub-01")
            self.assertEqual(result["subjects"][0]["score"], 85.5)
            
            # Verify file exists
            json_path = self.data_processed_dir / "valid_subjects.json"
            self.assertTrue(json_path.exists())
            
            with open(json_path, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data["count"], 1)
        finally:
            download_module.DATA_PROCESSED_DIR = original_path

if __name__ == '__main__':
    unittest.main()