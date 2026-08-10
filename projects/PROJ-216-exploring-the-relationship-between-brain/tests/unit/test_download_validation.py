import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from download import fetch_openneuro_data, validate_and_aggregate, check_validation_and_halt, load_behavioral_scores

class TestDownloadValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name) / 'data' / 'raw'
        self.data_dir.mkdir(parents=True)
        self.processed_dir = Path(self.temp_dir.name) / 'data' / 'processed'
        self.processed_dir.mkdir(parents=True)
        
        # Mock the ensure_directories function
        patcher = patch('download.ensure_directories')
        self.mock_ensure_dirs = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('download.get_subject_list')
    @patch('download.download_dataset')
    @patch('download.enforce_sample_limit')
    @patch('download.validate_and_aggregate')
    @patch('download.check_validation_and_halt')
    def test_fetch_openneuro_data_with_valid_subjects(
        self, mock_halt, mock_agg, mock_limit, mock_download, mock_get_subjects
    ):
        """Test that fetch_openneuro_data correctly processes valid subjects."""
        mock_get_subjects.return_value = ['sub-01', 'sub-02']
        mock_limit.return_value = ['sub-01', 'sub-02']
        mock_agg.return_value = {'subjects': [{'id': 'sub-01', 'fluid_intelligence_score': 0.8}], 'count': 1}
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps({'fluid_intelligence_score': 0.8}))):
                result = fetch_openneuro_data()
                
                self.assertEqual(result['count'], 1)
                self.assertEqual(result['subjects'][0]['id'], 'sub-01')
                mock_halt.assert_called_once()

    @patch('download.get_subject_list')
    @patch('download.download_dataset')
    @patch('download.enforce_sample_limit')
    @patch('download.validate_and_aggregate')
    def test_fetch_openneuro_data_with_no_valid_subjects(
        self, mock_agg, mock_limit, mock_download, mock_get_subjects
    ):
        """Test that fetch_openneuro_data halts when no valid subjects are found."""
        mock_get_subjects.return_value = ['sub-01']
        mock_limit.return_value = ['sub-01']
        mock_agg.return_value = {'subjects': [], 'count': 0}
        
        with self.assertRaises(ValueError) as context:
            with patch.object(Path, 'exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps({'other_score': 0.5}))):
                    fetch_openneuro_data()
        
        self.assertIn("No valid Fluid Intelligence data found", str(context.exception))

    @patch('download.get_subject_list')
    def test_fallback_dataset_fetch(self, mock_get_subjects):
        """Test that fallback dataset is fetched when primary fails."""
        mock_get_subjects.side_effect = [
            [],  # Primary returns no subjects
            ['sub-01']  # Fallback returns subjects
        ]
        
        with patch('download.download_dataset') as mock_download:
            with patch('download.enforce_sample_limit', return_value=['sub-01']):
                with patch('download.validate_and_aggregate', return_value={'subjects': [{'id': 'sub-01', 'fluid_intelligence_score': 0.9}], 'count': 1}):
                    with patch.object(Path, 'exists', return_value=True):
                        with patch('builtins.open', mock_open(read_data=json.dumps({'fluid_intelligence_score': 0.9}))):
                            result = fetch_openneuro_data()
                            
                            # Should have called download_dataset for fallback
                            self.assertTrue(any('ds000230' in str(call) for call in mock_download.call_args_list))

    def test_load_behavioral_scores_missing_score(self):
        """Test that load_behavioral_scores returns None when score is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subject_dir = Path(tmpdir) / 'sub-01'
            subject_dir.mkdir()
            behav_file = subject_dir / 'behav.json'
            
            with open(behav_file, 'w') as f:
                json.dump({'other_score': 0.5}, f)
            
            result = load_behavioral_scores(subject_dir)
            self.assertIsNone(result)

    def test_load_behavioral_scores_valid(self):
        """Test that load_behavioral_scores returns correct data when score is present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subject_dir = Path(tmpdir) / 'sub-01'
            subject_dir.mkdir()
            behav_file = subject_dir / 'behav.json'
            
            with open(behav_file, 'w') as f:
                json.dump({'fluid_intelligence_score': 0.85}, f)
            
            result = load_behavioral_scores(subject_dir)
            self.assertIsNotNone(result)
            self.assertEqual(result['id'], 'sub-01')
            self.assertEqual(result['fluid_intelligence_score'], 0.85)

    def test_check_validation_and_halt_zero_subjects(self):
        """Test that check_validation_and_halt raises error and writes log when no subjects."""
        output_path = self.processed_dir / 'valid_subjects.json'
        
        with self.assertRaises(ValueError) as context:
            check_validation_and_halt([], output_path)
        
        self.assertIn("No valid Fluid Intelligence data found", str(context.exception))
        
        # Check that log file was written
        log_path = self.processed_dir / 'validation_errors.log'
        self.assertTrue(log_path.exists())
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("[VALIDATION_ERROR]", content)
            self.assertIn("No valid Fluid Intelligence data found", content)

    def test_check_validation_and_halt_with_subjects(self):
        """Test that check_validation_and_halt writes valid_subjects.json when subjects exist."""
        output_path = self.processed_dir / 'valid_subjects.json'
        valid_subjects = [{'id': 'sub-01', 'fluid_intelligence_score': 0.7}]
        
        check_validation_and_halt(valid_subjects, output_path)
        
        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data['count'], 1)
            self.assertEqual(data['subjects'][0]['id'], 'sub-01')

if __name__ == '__main__':
    unittest.main()