import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from code.data.validate import exclude_subjects_by_missing_data, DataValidationError

class TestExcludeSubjectsByMissingData:
    """Tests for exclude_subjects_by_missing_data function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock participants DataFrame
        self.participants_df = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05'],
            'musical_genre': [5.0, 4.0, np.nan, 3.0, 2.0],  # sub-03 has missing
            'STOMP-R': [10.0, 9.0, 8.0, np.nan, 7.0],      # sub-04 has missing
            'age': [25, 30, 35, 40, 45],
            'sex': ['M', 'F', 'M', 'F', 'M']
        })
        
        # Mock preprocessed subjects (all 5)
        self.preprocessed_subjects = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05']
        
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_no_exclusion_when_data_complete(self):
        """Test that no subjects are excluded when data is complete."""
        # Create a DataFrame with no missing values
        complete_df = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02', 'sub-03'],
            'musical_genre': [5.0, 4.0, 3.0],
            'STOMP-R': [10.0, 9.0, 8.0],
            'age': [25, 30, 35]
        })
        
        result = exclude_subjects_by_missing_data(
            complete_df, 
            ['sub-01', 'sub-02', 'sub-03'],
            missing_threshold=0.10
        )
        
        assert len(result) == 3
        assert list(result['subject_id']) == ['sub-01', 'sub-02', 'sub-03']
    
    def test_excludes_subjects_with_high_missing_behavioral(self):
        """Test exclusion of subjects with >10% missing behavioral data."""
        # sub-03 has 1/2 = 50% missing in behavioral columns
        result = exclude_subjects_by_missing_data(
            self.participants_df,
            self.preprocessed_subjects,
            missing_threshold=0.10
        )
        
        # sub-03 should be excluded
        assert 'sub-03' not in result['subject_id'].values
        # sub-04 should be excluded (1/2 = 50% missing)
        assert 'sub-04' not in result['subject_id'].values
        
        # Others should remain
        assert len(result) == 3
        assert 'sub-01' in result['subject_id'].values
        assert 'sub-02' in result['subject_id'].values
        assert 'sub-05' in result['subject_id'].values
    
    def test_threshold_parameter_respected(self):
        """Test that the threshold parameter is respected."""
        # With threshold=0.50, sub-03 and sub-04 (50% missing) should remain
        result = exclude_subjects_by_missing_data(
            self.participants_df,
            self.preprocessed_subjects,
            missing_threshold=0.50
        )
        
        # All should remain since 50% is not > 50%
        assert len(result) == 5
        assert 'sub-03' in result['subject_id'].values
        assert 'sub-04' in result['subject_id'].values
    
    def test_excludes_subjects_not_in_preprocessed(self):
        """Test that subjects not in preprocessed list are excluded."""
        # Create a DataFrame with a subject not in preprocessed list
        df = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02', 'sub-99'],
            'musical_genre': [5.0, 4.0, 3.0],
            'STOMP-R': [10.0, 9.0, 8.0]
        })
        
        result = exclude_subjects_by_missing_data(
            df,
            ['sub-01', 'sub-02'],  # sub-99 not here
            missing_threshold=0.10
        )
        
        assert len(result) == 2
        assert 'sub-99' not in result['subject_id'].values
        assert 'sub-01' in result['subject_id'].values
        assert 'sub-02' in result['subject_id'].values
    
    def test_empty_dataframe_returns_empty(self):
        """Test that empty DataFrame is handled correctly."""
        empty_df = pd.DataFrame(columns=['subject_id', 'musical_genre', 'STOMP-R'])
        
        result = exclude_subjects_by_missing_data(
            empty_df,
            [],
            missing_threshold=0.10
        )
        
        assert len(result) == 0
        assert list(result.columns) == list(empty_df.columns)
    
    def test_all_subjects_excluded_returns_empty(self):
        """Test when all subjects have too much missing data."""
        # All subjects have 50% missing
        df = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02'],
            'musical_genre': [np.nan, np.nan],
            'STOMP-R': [np.nan, np.nan]
        })
        
        result = exclude_subjects_by_missing_data(
            df,
            ['sub-01', 'sub-02'],
            missing_threshold=0.10
        )
        
        assert len(result) == 0