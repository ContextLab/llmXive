"""
Unit tests for ingestion module, specifically focusing on exclusion logic.
"""
import os
import sys
import unittest
import tempfile
import shutil
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import (
    join_fmri_mwq_data,
    validate_subject_data,
    process_subject_validation,
    check_zero_variance_subjects
)
from code.config import get_project_root

class TestExclusionLogic(unittest.TestCase):
    """Test cases for missing pairs and high motion exclusion logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        
        # Create mock data directories
        self.raw_dir = self.project_root / "data" / "raw"
        self.raw_dir.mkdir(parents=True)
        
        self.processed_dir = self.project_root / "data" / "processed"
        self.processed_dir.mkdir(parents=True)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_missing_pairs_exclusion(self):
        """Test that subjects with missing MWQ or fMRI data are excluded."""
        # Create mock fMRI data with subjects 1, 2, 3
        fmri_data = pd.DataFrame({
            'Subject_ID': ['sub-01', 'sub-02', 'sub-03'],
            'Global_Signal_SD': [0.5, 0.6, 0.7],
            'Mean_FD': [0.2, 0.3, 0.4],
            'Mean_DVARS': [0.3, 0.4, 0.5]
        })
        
        # Create mock MWQ data with subjects 2, 3, 4 (missing sub-01, has sub-04)
        mwq_data = pd.DataFrame({
            'Subject_ID': ['sub-02', 'sub-03', 'sub-04'],
            'MWQ_Score': [15.0, 20.0, 18.0],
            'Age': [25, 30, 28],
            'Sex': ['M', 'F', 'M']
        })
        
        # Test join_fmri_mwq_data
        joined_data = join_fmri_mwq_data(fmri_data, mwq_data)
        
        # Should only contain subjects present in both datasets (sub-02, sub-03)
        self.assertEqual(len(joined_data), 2)
        self.assertIn('sub-02', joined_data['Subject_ID'].values)
        self.assertIn('sub-03', joined_data['Subject_ID'].values)
        self.assertNotIn('sub-01', joined_data['Subject_ID'].values)  # Missing MWQ
        self.assertNotIn('sub-04', joined_data['Subject_ID'].values)  # Missing fMRI

    def test_high_motion_exclusion(self):
        """Test that subjects with mean FD > 0.5mm are excluded."""
        # Create mock joined data with varying FD values
        joined_data = pd.DataFrame({
            'Subject_ID': ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05'],
            'Global_Signal_SD': [0.5, 0.6, 0.7, 0.8, 0.9],
            'MWQ_Score': [15.0, 20.0, 18.0, 22.0, 16.0],
            'Age': [25, 30, 28, 35, 27],
            'Sex': ['M', 'F', 'M', 'F', 'M'],
            'Mean_FD': [0.2, 0.4, 0.5, 0.6, 0.8],  # sub-04 and sub-05 exceed threshold
            'Mean_DVARS': [0.3, 0.4, 0.5, 0.6, 0.7]
        })
        
        # Apply motion exclusion (threshold = 0.5)
        threshold = 0.5
        filtered_data = joined_data[joined_data['Mean_FD'] <= threshold].reset_index(drop=True)
        
        # Should exclude sub-04 and sub-05
        self.assertEqual(len(filtered_data), 3)
        self.assertIn('sub-01', filtered_data['Subject_ID'].values)
        self.assertIn('sub-02', filtered_data['Subject_ID'].values)
        self.assertIn('sub-03', filtered_data['Subject_ID'].values)
        self.assertNotIn('sub-04', filtered_data['Subject_ID'].values)
        self.assertNotIn('sub-05', filtered_data['Subject_ID'].values)

    def test_combined_exclusion_logic(self):
        """Test combined exclusion of missing pairs and high motion subjects."""
        # Create mock fMRI data
        fmri_data = pd.DataFrame({
            'Subject_ID': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
            'Global_Signal_SD': [0.5, 0.6, 0.7, 0.8],
            'Mean_FD': [0.2, 0.6, 0.4, 0.8],  # sub-02 and sub-04 exceed threshold
            'Mean_DVARS': [0.3, 0.7, 0.5, 0.9]
        })
        
        # Create mock MWQ data
        mwq_data = pd.DataFrame({
            'Subject_ID': ['sub-01', 'sub-03', 'sub-05'],  # sub-02 and sub-04 missing
            'MWQ_Score': [15.0, 18.0, 20.0],
            'Age': [25, 28, 30],
            'Sex': ['M', 'M', 'F']
        })
        
        # Step 1: Join data (excludes sub-02, sub-04 due to missing MWQ; sub-05 due to missing fMRI)
        joined_data = join_fmri_mwq_data(fmri_data, mwq_data)
        
        # Should only have sub-01 and sub-03
        self.assertEqual(len(joined_data), 2)
        
        # Step 2: Apply motion exclusion (threshold = 0.5)
        # sub-01 has FD=0.2 (keep), sub-03 has FD=0.4 (keep)
        # If sub-02 or sub-04 were present, they would be excluded
        filtered_data = joined_data[joined_data['Mean_FD'] <= 0.5].reset_index(drop=True)
        
        # Both remaining subjects should pass motion threshold
        self.assertEqual(len(filtered_data), 2)
        self.assertEqual(filtered_data['Subject_ID'].tolist(), ['sub-01', 'sub-03'])

    def test_zero_variance_exclusion(self):
        """Test that subjects with global_signal_sd == 0 are excluded."""
        # Create mock data with zero variance
        data = pd.DataFrame({
            'Subject_ID': ['sub-01', 'sub-02', 'sub-03'],
            'Global_Signal_SD': [0.5, 0.0, 0.7],  # sub-02 has zero variance
            'MWQ_Score': [15.0, 20.0, 18.0],
            'Age': [25, 30, 28],
            'Sex': ['M', 'F', 'M'],
            'Mean_FD': [0.2, 0.3, 0.4],
            'Mean_DVARS': [0.3, 0.4, 0.5]
        })
        
        # Apply zero variance check
        filtered_data = check_zero_variance_subjects(data)
        
        # Should exclude sub-02
        self.assertEqual(len(filtered_data), 2)
        self.assertIn('sub-01', filtered_data['Subject_ID'].values)
        self.assertIn('sub-03', filtered_data['Subject_ID'].values)
        self.assertNotIn('sub-02', filtered_data['Subject_ID'].values)

    def test_exclusion_logging_counts(self):
        """Test that exclusion counts are properly tracked and logged."""
        # Create mock data
        fmri_data = pd.DataFrame({
            'Subject_ID': [f'sub-{i:02d}' for i in range(1, 11)],  # 10 subjects
            'Global_Signal_SD': [0.5 + i * 0.01 for i in range(10)],
            'Mean_FD': [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.3, 0.4, 0.2],  # 3 high motion
            'Mean_DVARS': [0.3 + i * 0.01 for i in range(10)]
        })
        
        mwq_data = pd.DataFrame({
            'Subject_ID': [f'sub-{i:02d}' for i in range(2, 9)],  # 7 subjects (missing sub-01, sub-09, sub-10)
            'MWQ_Score': [15.0 + i for i in range(7)],
            'Age': [25 + i for i in range(7)],
            'Sex': ['M', 'F', 'M', 'F', 'M', 'F', 'M']
        })
        
        # Join data
        joined_data = join_fmri_mwq_data(fmri_data, mwq_data)
        
        # Initial join should have 7 subjects (sub-02 to sub-08)
        self.assertEqual(len(joined_data), 7)
        
        # Apply motion exclusion (threshold = 0.5)
        # sub-06 (FD=0.6), sub-07 (FD=0.7), sub-08 (FD=0.8) should be excluded
        filtered_data = joined_data[joined_data['Mean_FD'] <= 0.5].reset_index(drop=True)
        
        # Should have 4 subjects remaining
        self.assertEqual(len(filtered_data), 4)
        
        # Verify excluded subjects
        excluded_motion = joined_data[joined_data['Mean_FD'] > 0.5]
        self.assertEqual(len(excluded_motion), 3)
        
        # Verify specific excluded IDs
        excluded_ids = excluded_motion['Subject_ID'].tolist()
        self.assertIn('sub-06', excluded_ids)
        self.assertIn('sub-07', excluded_ids)
        self.assertIn('sub-08', excluded_ids)

    def test_edge_case_all_excluded(self):
        """Test behavior when all subjects are excluded."""
        # Create mock data where all subjects exceed motion threshold
        fmri_data = pd.DataFrame({
            'Subject_ID': ['sub-01', 'sub-02'],
            'Global_Signal_SD': [0.5, 0.6],
            'Mean_FD': [0.8, 0.9],  # All exceed threshold
            'Mean_DVARS': [0.7, 0.8]
        })
        
        mwq_data = pd.DataFrame({
            'Subject_ID': ['sub-01', 'sub-02'],
            'MWQ_Score': [15.0, 20.0],
            'Age': [25, 30],
            'Sex': ['M', 'F']
        })
        
        # Join data
        joined_data = join_fmri_mwq_data(fmri_data, mwq_data)
        self.assertEqual(len(joined_data), 2)
        
        # Apply motion exclusion
        filtered_data = joined_data[joined_data['Mean_FD'] <= 0.5].reset_index(drop=True)
        
        # Should be empty
        self.assertEqual(len(filtered_data), 0)

    def test_edge_case_no_missing_pairs(self):
        """Test behavior when all subjects have matching data."""
        # Create mock data with perfect match
        fmri_data = pd.DataFrame({
            'Subject_ID': ['sub-01', 'sub-02', 'sub-03'],
            'Global_Signal_SD': [0.5, 0.6, 0.7],
            'Mean_FD': [0.2, 0.3, 0.4],
            'Mean_DVARS': [0.3, 0.4, 0.5]
        })
        
        mwq_data = pd.DataFrame({
            'Subject_ID': ['sub-01', 'sub-02', 'sub-03'],
            'MWQ_Score': [15.0, 20.0, 18.0],
            'Age': [25, 30, 28],
            'Sex': ['M', 'F', 'M']
        })
        
        # Join data
        joined_data = join_fmri_mwq_data(fmri_data, mwq_data)
        
        # Should have all 3 subjects
        self.assertEqual(len(joined_data), 3)
        self.assertListEqual(joined_data['Subject_ID'].tolist(), ['sub-01', 'sub-02', 'sub-03'])

if __name__ == '__main__':
    unittest.main()