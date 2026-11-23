import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import logging

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from download import (
    fetch_openneuro_data, 
    validate_and_aggregate, 
    check_validation_and_halt, 
    ensure_directories,
    get_subject_list,
    download_dataset
)

class TestDownloadValidation(unittest.TestCase):
    
    def setUp(self):
        # Ensure directories exist for the test
        ensure_directories()
        # Clear any existing logs or outputs from previous runs
        if Path("data/processed/valid_subjects.json").exists():
            Path("data/processed/valid_subjects.json").unlink()
        if Path("data/processed/validation_errors.log").exists():
            Path("data/processed/validation_errors.log").unlink()
        
        # Setup logging to suppress noise during tests if needed, 
        # but we want to see errors for debugging
        self.logger = logging.getLogger("download")

    def tearDown(self):
        # Cleanup generated files
        for f in ["data/processed/valid_subjects.json", "data/processed/validation_errors.log"]:
            if Path(f).exists():
                Path(f).unlink()

    @patch('download.download_dataset')
    @patch('download.get_subject_list')
    @patch('download.Path')
    def test_fetch_openneuro_data_with_valid_fluid_intelligence(self, mock_path, mock_get_list, mock_download):
        """
        Test that the pipeline successfully fetches data and validates Fluid Intelligence scores.
        """
        # Mock download success
        mock_download.return_value = True
        
        # Mock subject list
        mock_get_list.return_value = [
            {"id": "01", "dataset": "ds000224"},
            {"id": "02", "dataset": "ds000224"}
        ]
        
        # Mock Path to simulate file existence for validation
        # We need to mock the behavior of load_behavioral_scores indirectly via validate_and_aggregate
        # Since validate_and_aggregate calls load_behavioral_scores which reads files,
        # we mock the file reading logic inside validate_and_aggregate or the helper.
        # However, validate_and_aggregate is called internally.
        # Let's mock the specific file check in load_behavioral_scores logic.
        
        # We will patch the logic inside validate_and_aggregate to return scores
        with patch('download.load_behavioral_scores') as mock_load_scores:
            mock_load_scores.return_value = 0.85 # Valid score
            
            result = fetch_openneuro_data()
            
            self.assertTrue(result)
            self.assertTrue(Path("data/processed/valid_subjects.json").exists())
            
            with open("data/processed/valid_subjects.json", 'r') as f:
                data = json.load(f)
            
            self.assertEqual(data["count"], 2)
            self.assertEqual(len(data["subjects"]), 2)
            self.assertEqual(data["subjects"][0]["score"], 0.85)

    @patch('download.download_dataset')
    @patch('download.get_subject_list')
    @patch('download.load_behavioral_scores')
    def test_fetch_openneuro_data_zero_valid_subjects(self, mock_load_scores, mock_get_list, mock_download):
        """
        Test that the pipeline halts with correct error when no valid Fluid Intelligence scores are found.
        This simulates the 'count 0' scenario.
        """
        # Mock download success
        mock_download.return_value = True
        
        # Mock subject list
        mock_get_list.return_value = [
            {"id": "01", "dataset": "ds000224"}
        ]
        
        # Mock load_behavioral_scores to return None (no score)
        mock_load_scores.return_value = None
        
        # Expect RuntimeError
        with self.assertRaises(RuntimeError) as context:
            fetch_openneuro_data()
        
        self.assertIn("No valid Fluid Intelligence data found", str(context.exception))
        
        # Verify error log was written
        self.assertTrue(Path("data/processed/validation_errors.log").exists())
        with open("data/processed/validation_errors.log", 'r') as f:
            content = f.read()
            self.assertIn("[VALIDATION_ERROR]", content)
            self.assertIn("No valid Fluid Intelligence data found", content)

    @patch('download.download_dataset')
    @patch('download.get_subject_list')
    def test_fetch_openneuro_data_download_failure(self, mock_get_list, mock_download):
        """
        Test behavior when both primary and fallback datasets fail.
        """
        # Mock download failure
        mock_download.return_value = False
        
        # get_subject_list is not called if download fails, but we need to ensure the flow continues
        # to validation which will create an empty JSON and halt.
        
        with self.assertRaises(RuntimeError) as context:
            fetch_openneuro_data()
        
        self.assertIn("No valid Fluid Intelligence data found", str(context.exception))
        self.assertTrue(Path("data/processed/validation_errors.log").exists())

    def test_enforce_sample_limit(self):
        """Test that the sample limit is correctly enforced."""
        subjects = [{"id": str(i)} for i in range(15)]
        limited = validate_and_aggregate.__globals__['enforce_sample_limit'](subjects, limit=10)
        self.assertEqual(len(limited), 10)
        
        limited_small = validate_and_aggregate.__globals__['enforce_sample_limit'](subjects[:5], limit=10)
        self.assertEqual(len(limited_small), 5)

if __name__ == '__main__':
    unittest.main()