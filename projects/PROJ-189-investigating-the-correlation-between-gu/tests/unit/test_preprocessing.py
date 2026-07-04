"""
Unit tests for preprocessing pipeline (T015).

Tests:
- Age filtering logic
- Covariate imputation strategies
- Validation checks
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code import preprocessing

class TestAgeFiltering:
    """Tests for age >= 60 filtering."""
    
    def test_filter_removes_young_participants(self):
        """Test that participants under 60 are removed."""
        data = {
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'age': [55, 60, 65, 59],
            'bmi': [22.0, 24.0, 26.0, 21.0]
        }
        df = pd.DataFrame(data)
        
        result = preprocessing.filter_by_age(df, min_age=60)
        
        assert len(result) == 2
        assert all(result['age'] >= 60)
        assert set(result['participant_id']) == {'P2', 'P3'}
    
    def test_filter_all_elderly(self):
        """Test when all participants are >= 60."""
        data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'age': [65, 70, 80],
            'bmi': [22.0, 24.0, 26.0]
        }
        df = pd.DataFrame(data)
        
        result = preprocessing.filter_by_age(df, min_age=60)
        
        assert len(result) == 3
        assert all(result['age'] >= 60)
    
    def test_filter_all_young(self):
        """Test when all participants are < 60."""
        data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'age': [20, 35, 55],
            'bmi': [22.0, 24.0, 26.0]
        }
        df = pd.DataFrame(data)
        
        result = preprocessing.filter_by_age(df, min_age=60)
        
        assert len(result) == 0
        assert result['age'].empty

class TestCovariateImputation:
    """Tests for covariate imputation logic."""
    
    def test_impute_bmi_median(self):
        """Test BMI imputation uses median."""
        data = {
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'age': [65, 70, 75, 80],
            'bmi': [22.0, np.nan, 26.0, 24.0]
        }
        df = pd.DataFrame(data)
        
        result = preprocessing.impute_covariates(df)
        
        # Median of [22.0, 26.0, 24.0] is 24.0
        assert result['bmi'].iloc[1] == 24.0
        assert not result['bmi'].isna().any()
    
    def test_impute_education_mean(self):
        """Test education imputation uses mean."""
        data = {
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'age': [65, 70, 75, 80],
            'education': [12.0, np.nan, 16.0, 14.0]
        }
        df = pd.DataFrame(data)
        
        result = preprocessing.impute_covariates(df)
        
        # Mean of [12.0, 16.0, 14.0] is 14.0
        assert result['education'].iloc[1] == 14.0
        assert not result['education'].isna().any()
    
    def test_no_imputation_needed(self):
        """Test when no missing values exist."""
        data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'age': [65, 70, 75],
            'bmi': [22.0, 24.0, 26.0],
            'education': [12.0, 16.0, 14.0]
        }
        df = pd.DataFrame(data)
        
        result = preprocessing.impute_covariates(df)
        
        # Should be unchanged
        pd.testing.assert_frame_equal(result, df)
    
    def test_multiple_missing_values(self):
        """Test imputation with multiple missing values."""
        data = {
            'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
            'age': [65, 70, 75, 80, 85],
            'bmi': [np.nan, np.nan, 26.0, 24.0, 28.0],
            'education': [12.0, 16.0, np.nan, np.nan, 14.0]
        }
        df = pd.DataFrame(data)
        
        result = preprocessing.impute_covariates(df)
        
        assert not result['bmi'].isna().any()
        assert not result['education'].isna().any()
        assert len(result) == 5

class TestValidation:
    """Tests for validation logic."""
    
    def test_validation_passes(self):
        """Test validation passes when no missing covariates."""
        data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'age': [65, 70, 75],
            'bmi': [22.0, 24.0, 26.0],
            'education': [12.0, 16.0, 14.0]
        }
        df = pd.DataFrame(data)
        
        assert preprocessing.validate_covariate_imputation(df) is True
    
    def test_validation_fails_with_missing(self):
        """Test validation fails when missing covariates exist."""
        data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'age': [65, 70, 75],
            'bmi': [22.0, np.nan, 26.0],
            'education': [12.0, 16.0, 14.0]
        }
        df = pd.DataFrame(data)
        
        assert preprocessing.validate_covariate_imputation(df) is False
    
    def test_validation_missing_covariate_column(self):
        """Test validation handles missing covariate columns gracefully."""
        data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'age': [65, 70, 75]
        }
        df = pd.DataFrame(data)
        
        # Should pass since required columns don't exist
        assert preprocessing.validate_covariate_imputation(df) is True

class TestPipelineIntegration:
    """Integration tests for the full pipeline."""
    
    def test_full_pipeline(self, tmp_path):
        """Test full pipeline with temporary files."""
        # Create test data
        data = {
            'participant_id': [f'P{i}' for i in range(100)],
            'age': np.random.randint(40, 90, 100),
            'bmi': np.random.choice([22.0, 24.0, np.nan, 26.0, np.nan], 100),
            'education': np.random.choice([12.0, 14.0, np.nan, 16.0], 100)
        }
        df = pd.DataFrame(data)
        
        # Save to temp file
        temp_input = tmp_path / 'merged_participant_data.csv'
        df.to_csv(temp_input, index=False)
        
        # Mock the load function
        original_load = preprocessing.load_merged_data
        def mock_load():
            return pd.read_csv(temp_input)
        
        preprocessing.load_merged_data = mock_load
        
        try:
            # Run pipeline
            result = preprocessing.run_preprocessing_pipeline()
            
            # Verify results
            assert all(result['age'] >= 60)
            assert not result['bmi'].isna().any()
            assert not result['education'].isna().any()
            assert len(result) > 0
        finally:
            # Restore original function
            preprocessing.load_merged_data = original_load

if __name__ == '__main__':
    pytest.main([__file__, '-v'])