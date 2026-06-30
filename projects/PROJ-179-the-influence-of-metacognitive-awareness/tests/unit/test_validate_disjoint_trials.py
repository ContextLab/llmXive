"""
Unit tests for T017: validate_disjoint_trials.py
"""
import os
import sys
import json
import tempfile
import unittest
import pandas as pd
from pathlib import Path

# Add the code directory to the path to allow imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.validate_disjoint_trials import validate_disjoint, load_summary_file, get_unique_trials

class TestValidateDisjointTrials(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create mock data for confidence summary
        self.confidence_data = pd.DataFrame({
            'trial_id': [1, 2, 3, 4, 5],
            'mean_confidence': [0.8, 0.7, 0.9, 0.6, 0.85]
        })
        
        # Create mock data for accuracy summary (disjoint trials)
        self.accuracy_data_disjoint = pd.DataFrame({
            'trial_id': [6, 7, 8, 9, 10],
            'accuracy': [1, 0, 1, 1, 0]
        })
        
        # Create mock data for accuracy summary (overlapping trials)
        self.accuracy_data_overlap = pd.DataFrame({
            'trial_id': [3, 4, 8, 9, 10],  # 3 and 4 overlap
            'accuracy': [1, 0, 1, 1, 0]
        })

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_load_summary_file_success(self):
        """Test loading a valid summary file."""
        file_path = self.temp_path / "test.csv"
        self.confidence_data.to_csv(file_path, index=False)
        
        df, col = load_summary_file(file_path)
        self.assertEqual(col, 'trial_id')
        self.assertEqual(len(df), 5)

    def test_load_summary_file_missing_file(self):
        """Test loading a non-existent file raises error."""
        file_path = self.temp_path / "nonexistent.csv"
        with self.assertRaises(FileNotFoundError):
            load_summary_file(file_path)

    def test_get_unique_trials(self):
        """Test extracting unique trials."""
        file_path = self.temp_path / "test.csv"
        self.confidence_data.to_csv(file_path, index=False)
        
        df, col = load_summary_file(file_path)
        trials = get_unique_trials(df, col)
        
        self.assertEqual(trials, {1, 2, 3, 4, 5})

    def test_validate_disjoint_pass(self):
        """Test validation passes when trials are disjoint."""
        conf_path = self.temp_path / "confidence_summary.csv"
        acc_path = self.temp_path / "accuracy_summary.csv"
        output_path = self.temp_path / "report.json"
        
        self.confidence_data.to_csv(conf_path, index=False)
        self.accuracy_data_disjoint.to_csv(acc_path, index=False)
        
        success = validate_disjoint(conf_path, acc_path, output_path)
        
        self.assertTrue(success)
        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['intersection_count'], 0)

    def test_validate_disjoint_fail(self):
        """Test validation fails when trials overlap."""
        conf_path = self.temp_path / "confidence_summary.csv"
        acc_path = self.temp_path / "accuracy_summary.csv"
        output_path = self.temp_path / "report.json"
        
        self.confidence_data.to_csv(conf_path, index=False)
        self.accuracy_data_overlap.to_csv(acc_path, index=False)
        
        success = validate_disjoint(conf_path, acc_path, output_path)
        
        self.assertFalse(success)
        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['intersection_count'], 2)
        self.assertIn(3, report['intersection_trials'])
        self.assertIn(4, report['intersection_trials'])

    def test_validate_disjoint_missing_column(self):
        """Test validation handles missing trial ID column gracefully."""
        conf_path = self.temp_path / "confidence_summary.csv"
        acc_path = self.temp_path / "accuracy_summary.csv"
        output_path = self.temp_path / "report.json"
        
        # Create data without 'trial_id' column
        bad_conf_data = pd.DataFrame({
            'wrong_id': [1, 2, 3],
            'value': [0.8, 0.7, 0.9]
        })
        bad_conf_data.to_csv(conf_path, index=False)
        
        self.accuracy_data_disjoint.to_csv(acc_path, index=False)
        
        with self.assertRaises(ValueError):
            validate_disjoint(conf_path, acc_path, output_path)

if __name__ == '__main__':
    unittest.main()