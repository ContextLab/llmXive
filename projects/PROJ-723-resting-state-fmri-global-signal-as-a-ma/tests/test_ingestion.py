"""
Unit tests for ingestion module functions.

These tests verify the core logic of data loading, joining, and validation
before the full pipeline is executed on real data.
"""
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import validate_subject_data, join_fmri_mwq_data
from utils import read_csv, write_csv


class TestIngestionValidation(unittest.TestCase):
    """Tests for subject data validation logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_fmri = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02', 'sub-03'],
            'global_signal_sd': [0.5, 0.6, 0.7],
            'mean_fd': [0.1, 0.2, 0.8]
        })
        self.valid_mwq = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02', 'sub-03'],
            'mwq_score': [10, 20, 30],
            'age': [25, 30, 35],
            'sex': ['M', 'F', 'M']
        })

    def test_validate_subject_data_no_missing(self):
        """Test validation passes when no required keys are missing."""
        required_cols_fmri = ['subject_id', 'global_signal_sd']
        required_cols_mwq = ['subject_id', 'mwq_score']
        
        result = validate_subject_data(self.valid_fmri, self.valid_mwq, 
                                       required_cols_fmri, required_cols_mwq)
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['missing_fmri']), 0)
        self.assertEqual(len(result['missing_mwq']), 0)

    def test_validate_subject_data_missing_cols(self):
        """Test validation fails when required columns are missing."""
        incomplete_fmri = self.valid_fmri.drop(columns=['global_signal_sd'])
        
        required_cols_fmri = ['subject_id', 'global_signal_sd']
        required_cols_mwq = ['subject_id', 'mwq_score']
        
        result = validate_subject_data(incomplete_fmri, self.valid_mwq,
                                       required_cols_fmri, required_cols_mwq)
        
        self.assertFalse(result['valid'])
        self.assertIn('global_signal_sd', result['missing_fmri'])

    def test_join_fmri_mwq_data_success(self):
        """Test successful join of matching datasets."""
        joined = join_fmri_mwq_data(self.valid_fmri, self.valid_mwq, on='subject_id')
        
        self.assertEqual(len(joined), 3)
        self.assertIn('global_signal_sd', joined.columns)
        self.assertIn('mwq_score', joined.columns)
        self.assertIn('age', joined.columns)

    def test_join_fmri_mwq_data_partial_match(self):
        """Test join handles partial matches correctly."""
        extra_mwq = self.valid_mwq.copy()
        extra_mwq = pd.concat([extra_mwq, pd.DataFrame({'subject_id': ['sub-04'], 'mwq_score': [40]})])
        
        joined = join_fmri_mwq_data(self.valid_fmri, extra_mwq, on='subject_id')
        
        # Should only have 3 rows (inner join default)
        self.assertEqual(len(joined), 3)
        self.assertNotIn('sub-04', joined['subject_id'].values)


class TestIngestionIntegration(unittest.TestCase):
    """Integration-style tests using temporary CSV files."""

    def setUp(self):
        """Set up temporary directory and test files."""
        self.test_dir = Path(__file__).parent.parent / "data" / "test_temp"
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_round_trip_csv(self):
        """Test reading and writing CSVs preserves data."""
        test_df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': ['x', 'y', 'z']
        })
        path = self.test_dir / "test_round_trip.csv"
        
        write_csv(test_df, path)
        loaded_df = read_csv(path)
        
        self.assertTrue(test_df.equals(loaded_df))


if __name__ == '__main__':
    unittest.main()
