import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from download import (
    validate_and_aggregate,
    check_validation_and_halt,
    fetch_openneuro_data,
    ensure_directories
)

class TestDownloadValidation(unittest.TestCase):
    """Test suite for download validation logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / 'data' / 'raw'
        self.processed_dir = Path(self.test_dir) / 'data' / 'processed'
        
        # Create directories
        self.data_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)
        
        # Create mock subject directories with behavioral data
        self.subject1_dir = self.data_dir / 'ds000224' / 'sub-01'
        self.subject1_dir.mkdir(parents=True)
        
        self.subject2_dir = self.data_dir / 'ds000224' / 'sub-02'
        self.subject2_dir.mkdir(parents=True)
        
        # Create mock behavioral data with Fluid Intelligence score
        behavioral_file = self.subject1_dir / 'sub-01_task-rest_bold.json'
        with open(behavioral_file, 'w') as f:
            json.dump({
                'fluid_intelligence_score': 1.5,
                'age': 25,
                'gender': 'M'
            }, f)
        
        # Subject 2 has no score (missing file)
        
        # Mock environment variables for testing
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_validate_and_aggregate_with_fluid_intelligence(self):
        """Test validation finds subjects with Fluid Intelligence scores."""
        subjects = ['sub-01', 'sub-02']
        
        result = validate_and_aggregate(subjects, str(self.data_dir / 'ds000224'))
        
        # Should find 1 valid subject
        self.assertEqual(result['count'], 1)
        self.assertEqual(len(result['subjects']), 1)
        self.assertEqual(result['subjects'][0]['id'], 'sub-01')
        self.assertEqual(result['subjects'][0]['score'], 1.5)
        
        # Should have 1 error for sub-02
        self.assertEqual(len(result['errors']), 1)
        self.assertEqual(result['errors'][0]['subject_id'], 'sub-02')
        self.assertIn('Missing Fluid Intelligence score', result['errors'][0]['reason'])

    def test_check_validation_and_halt_with_valid_subjects(self):
        """Test that halt does NOT occur when valid subjects exist."""
        validation_result = {
            'count': 5,
            'subjects': [{'id': 'sub-01', 'score': 1.5}],
            'errors': []
        }
        
        # This should NOT raise an exception
        try:
            check_validation_and_halt(validation_result)
            success = True
        except RuntimeError:
            success = False
        
        self.assertTrue(success, "Should not halt when valid subjects exist")

    def test_check_validation_and_halt_with_zero_subjects(self):
        """Test that halt DOES occur when zero valid subjects found."""
        validation_result = {
            'count': 0,
            'subjects': [],
            'errors': [{'subject_id': 'sub-01', 'reason': 'Missing Fluid Intelligence score'}]
        }
        
        # This SHOULD raise an exception
        with self.assertRaises(RuntimeError) as context:
            check_validation_and_halt(validation_result)
        
        self.assertIn("No valid Fluid Intelligence data found", str(context.exception))
        
        # Verify error log was written
        error_log_path = Path('data/processed/validation_errors.log')
        self.assertTrue(error_log_path.exists(), "Error log should be created")
        
        with open(error_log_path, 'r') as f:
            content = f.read()
            self.assertIn("[VALIDATION_ERROR]", content)
            self.assertIn("No valid Fluid Intelligence data found", content)

    def test_old_creativity_error_path_removed(self):
        """
        Test that the old 'No valid creativity proxy found' error path is removed.
        
        This verifies that the code does NOT contain the old error message
        and instead uses the new Fluid Intelligence error path.
        """
        # Read the download.py source code
        download_py_path = Path(__file__).parent.parent.parent / 'code' / 'download.py'
        with open(download_py_path, 'r') as f:
            source_code = f.read()
        
        # Verify old error message is NOT present
        old_error_phrases = [
            "No valid creativity proxy found",
            "Musical Creativity",
            "TTCT",
            "AUT"
        ]
        
        for phrase in old_error_phrases:
            self.assertNotIn(phrase, source_code, 
                f"Old error phrase '{phrase}' should be removed from download.py")
        
        # Verify new error message IS present
        self.assertIn("No valid Fluid Intelligence data found", source_code,
            "New Fluid Intelligence error message should be present")

    def test_validation_proceeds_without_old_creativity_check(self):
        """
        Test that validation proceeds to check Fluid Intelligence even when
        old creativity checks would have failed.
        
        This simulates a scenario where the old check (if it existed) would fail,
        but the new check succeeds.
        """
        # Create a subject with only Fluid Intelligence score (no creativity data)
        behavioral_file = self.data_dir / 'ds000224' / 'sub-01' / 'sub-01_task-rest_bold.json'
        
        # Write data with only Fluid Intelligence
        with open(behavioral_file, 'w') as f:
            json.dump({
                'fluid_intelligence_score': 1.8
                # No creativity fields
            }, f)
        
        subjects = ['sub-01']
        result = validate_and_aggregate(subjects, str(self.data_dir / 'ds000224'))
        
        # Should still find the subject because Fluid Intelligence is present
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['subjects'][0]['score'], 1.8)

    @patch('download.download_dataset')
    @patch('download.get_subject_list')
    @patch('download.validate_and_aggregate')
    @patch('download.check_validation_and_halt')
    def test_fetch_openneuro_data_with_zero_valid_subjects(self, mock_halt, mock_validate, mock_get, mock_download):
        """
        Test that fetch_openneuro_data halts correctly when zero valid subjects.
        
        This verifies the full pipeline flow with mocked components.
        """
        # Mock validation result with zero subjects
        mock_validate.return_value = {
            'count': 0,
            'subjects': [],
            'errors': [{'subject_id': 'sub-01', 'reason': 'Missing Fluid Intelligence score'}]
        }
        
        # Mock subject list
        mock_get.return_value = ['sub-01']
        
        # Mock download success
        mock_download.return_value = True
        
        # Should raise RuntimeError
        with self.assertRaises(RuntimeError) as context:
            fetch_openneuro_data()
        
        self.assertIn("No valid Fluid Intelligence data found", str(context.exception))
        mock_halt.assert_called_once()

    def test_error_log_prefix_correct(self):
        """Test that error log uses correct prefix [VALIDATION_ERROR]."""
        validation_result = {
            'count': 0,
            'subjects': [],
            'errors': []
        }
        
        with self.assertRaises(RuntimeError):
            check_validation_and_halt(validation_result)
        
        error_log_path = Path('data/processed/validation_errors.log')
        with open(error_log_path, 'r') as f:
            content = f.read()
            self.assertIn("[VALIDATION_ERROR]", content)

if __name__ == '__main__':
    unittest.main()