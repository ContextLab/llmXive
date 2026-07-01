"""
Unit tests for the preprocessing module (T015).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import filter_by_training_years, remove_missing_data, preprocess_subjects
from utils.memory_monitor import MemoryLimitExceeded

class TestFilterByTrainingYears:
    def test_filter_by_training_years_includes_valid(self):
        """Test that subjects with >= 1 year are included."""
        data = {
            'subject_id': ['S1', 'S2', 'S3'],
            'years_of_training': [0.5, 1.0, 2.0]
        }
        df = pd.DataFrame(data)
        
        result = filter_by_training_years(df, min_years=1.0)
        
        assert len(result) == 2
        assert 'S1' not in result['subject_id'].values
        assert 'S2' in result['subject_id'].values
        assert 'S3' in result['subject_id'].values

    def test_filter_by_training_years_excludes_invalid(self):
        """Test that subjects with < 1 year are excluded."""
        data = {
            'subject_id': ['S1', 'S2', 'S3'],
            'years_of_training': [0.0, 0.9, 1.0]
        }
        df = pd.DataFrame(data)
        
        result = filter_by_training_years(df, min_years=1.0)
        
        assert len(result) == 1
        assert result.iloc[0]['subject_id'] == 'S3'

    def test_filter_by_training_years_handles_nan(self):
        """Test that NaN values in years_of_training are excluded."""
        data = {
            'subject_id': ['S1', 'S2', 'S3'],
            'years_of_training': [1.0, np.nan, 2.0]
        }
        df = pd.DataFrame(data)
        
        result = filter_by_training_years(df, min_years=1.0)
        
        assert len(result) == 2
        assert 'S2' not in result['subject_id'].values

    def test_filter_missing_column_raises_error(self):
        """Test that missing column raises KeyError."""
        data = {
            'subject_id': ['S1', 'S2'],
            'age': [15, 16]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(KeyError, match="DataFrame must contain 'years_of_training' column"):
            filter_by_training_years(df, min_years=1.0)

class TestRemoveMissingData:
    def test_remove_missing_data_all_columns(self):
        """Test dropping rows with any missing values."""
        data = {
            'A': [1, 2, np.nan, 4],
            'B': [5, np.nan, 7, 8]
        }
        df = pd.DataFrame(data)
        
        result = remove_missing_data(df)
        
        assert len(result) == 2
        assert list(result['A']) == [2, 4]

    def test_remove_missing_data_specific_columns(self):
        """Test dropping rows with missing values in specific columns."""
        data = {
            'A': [1, 2, np.nan, 4],
            'B': [5, np.nan, 7, 8],
            'C': [9, 10, 11, 12]
        }
        df = pd.DataFrame(data)
        
        result = remove_missing_data(df, columns=['A'])
        
        # Only row with NaN in A (index 2) should be dropped
        assert len(result) == 3
        assert 2 not in result.index

    def test_remove_missing_data_missing_columns_raises_error(self):
        """Test that specifying non-existent columns raises KeyError."""
        data = {'A': [1, 2]}
        df = pd.DataFrame(data)
        
        with pytest.raises(KeyError, match="Columns not found in DataFrame"):
            remove_missing_data(df, columns=['Z'])

class TestPreprocessSubjects:
    def setup_method(self):
        """Setup test data."""
        self.data = {
            'subject_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'group': ['musician', 'musician', 'non_musician', 'musician', 'non_musician'],
            'years_of_training': [2.0, 0.5, 0.0, 1.5, np.nan],
            'age': [15, 16, 14, 15, 16],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'motion_score': [0.1, 0.2, 0.1, 0.3, 0.2],
            'ses_score': [50, 60, 55, 45, 50]
        }
        self.df = pd.DataFrame(self.data)

    def test_preprocess_subjects_filters_and_cleans(self):
        """Test full pipeline filters by years and removes missing."""
        result = preprocess_subjects(self.df, min_years=1.0)
        
        # Expected: S1 (2.0), S4 (1.5). S2 (0.5), S3 (0.0), S5 (NaN) excluded.
        assert len(result) == 2
        assert 'S1' in result['subject_id'].values
        assert 'S4' in result['subject_id'].values
        assert 'S2' not in result['subject_id'].values
        assert 'S3' not in result['subject_id'].values
        assert 'S5' not in result['subject_id'].values

    def test_preprocess_subjects_empty_result(self):
        """Test pipeline returns empty df if no subjects pass filter."""
        data_nan = self.df.copy()
        data_nan['years_of_training'] = 0.5
        result = preprocess_subjects(data_nan, min_years=1.0)
        assert len(result) == 0

    def test_preprocess_subjects_preserves_columns(self):
        """Test that output contains required columns."""
        result = preprocess_subjects(self.df, min_years=1.0)
        required_cols = ['subject_id', 'group', 'years_of_training', 'age', 'sex']
        for col in required_cols:
            assert col in result.columns