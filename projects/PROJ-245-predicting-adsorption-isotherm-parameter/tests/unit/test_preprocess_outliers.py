import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import detect_outliers, _compute_descriptor_hash

class TestDetectOutliers:
    def test_identical_descriptors_conflicting_targets(self, tmp_path):
        """
        Test that rows with identical descriptors but different targets are flagged.
        """
        # Create a mock dataframe
        data = {
            'material_id': ['M1', 'M2', 'M3'],
            'desc_1': [1.0, 1.0, 2.0],
            'desc_2': [2.0, 2.0, 3.0],
            'langmuir_capacity': [10.0, 20.0, 15.0] # M1 and M2 have same desc, diff target
        }
        df = pd.DataFrame(data)
        
        # Run detection
        result_df = detect_outliers(df, target_col='langmuir_capacity', variance_threshold=1.0)
        
        # Check output file exists
        assert os.path.exists('data/processed/outliers.csv')
        
        # Load outliers
        outliers = pd.read_csv('data/processed/outliers.csv')
        
        # M1 and M2 should be flagged
        assert len(outliers) == 2
        assert set(outliers['material_id']) == {'M1', 'M2'}
        
        # Clean up
        if os.path.exists('data/processed/outliers.csv'):
            os.remove('data/processed/outliers.csv')

    def test_no_outliers(self, tmp_path):
        """
        Test that rows with identical descriptors and same target are NOT flagged.
        """
        data = {
            'material_id': ['M1', 'M2'],
            'desc_1': [1.0, 1.0],
            'desc_2': [2.0, 2.0],
            'langmuir_capacity': [10.0, 10.0] # Same target
        }
        df = pd.DataFrame(data)
        
        result_df = detect_outliers(df, target_col='langmuir_capacity', variance_threshold=1.0)
        
        assert os.path.exists('data/processed/outliers.csv')
        outliers = pd.read_csv('data/processed/outliers.csv')
        assert len(outliers) == 0
        
        # Clean up
        if os.path.exists('data/processed/outliers.csv'):
            os.remove('data/processed/outliers.csv')

    def test_missing_target_column(self, tmp_path):
        """
        Test behavior when target column is missing.
        """
        data = {
            'material_id': ['M1'],
            'desc_1': [1.0],
        }
        df = pd.DataFrame(data)
        
        result_df = detect_outliers(df, target_col='missing_col', variance_threshold=1.0)
        
        assert os.path.exists('data/processed/outliers.csv')
        outliers = pd.read_csv('data/processed/outliers.csv')
        assert len(outliers) == 0
        
        # Clean up
        if os.path.exists('data/processed/outliers.csv'):
            os.remove('data/processed/outliers.csv')
