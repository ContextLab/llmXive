"""
Unit tests for data validation in stats_engine.py (Task T122).

This module verifies that the ANOVA input validation correctly raises
DataValidationError when required columns are missing.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.stats_engine import (
    validate_anova_input,
    DataValidationError,
    run_anova_rm
)

class TestDataValidation:
    """Test cases for input data validation."""
    
    @pytest.fixture
    def valid_df(self):
        """Create a valid DataFrame with all required columns."""
        data = {
            'participant_id': ['P001', 'P001', 'P002', 'P002'],
            'interface_type': ['Traditional', 'Explainable', 'Traditional', 'Explainable'],
            'completion_time': [120.5, 110.2, 130.0, 115.5],
            'error_count': [2, 1, 3, 1],
            'sus_score': [75.0, 85.0, 70.0, 90.0]
        }
        return pd.DataFrame(data)
    
    def test_validate_anova_input_success(self, valid_df):
        """Test that validation passes when all columns are present."""
        required_columns = ['completion_time', 'error_count', 'sus_score', 'interface_type', 'participant_id']
        # Should not raise any exception
        validate_anova_input(valid_df, required_columns)
    
    def test_validate_anova_input_missing_column(self, valid_df):
        """Test that validation fails when a required column is missing."""
        # Remove one required column
        df_missing = valid_df.drop(columns=['sus_score'])
        required_columns = ['completion_time', 'error_count', 'sus_score', 'interface_type', 'participant_id']
        
        with pytest.raises(DataValidationError) as exc_info:
            validate_anova_input(df_missing, required_columns)
        
        assert 'sus_score' in str(exc_info.value)
        assert 'Missing required columns' in str(exc_info.value)
    
    def test_validate_anova_input_multiple_missing(self, valid_df):
        """Test that validation fails with multiple missing columns."""
        # Remove multiple required columns
        df_missing = valid_df.drop(columns=['sus_score', 'error_count'])
        required_columns = ['completion_time', 'error_count', 'sus_score', 'interface_type', 'participant_id']
        
        with pytest.raises(DataValidationError) as exc_info:
            validate_anova_input(df_missing, required_columns)
        
        assert 'sus_score' in str(exc_info.value)
        assert 'error_count' in str(exc_info.value)
    
    def test_run_anova_rm_missing_columns(self, valid_df):
        """Test that run_anova_rm raises DataValidationError for missing columns."""
        # Remove a required column
        df_missing = valid_df.drop(columns=['completion_time'])
        
        with pytest.raises(DataValidationError) as exc_info:
            run_anova_rm(df_missing, 'error_count')
        
        assert 'completion_time' in str(exc_info.value)
    
    def test_run_anova_rm_with_valid_data(self, valid_df):
        """Test that run_anova_rm succeeds with valid data."""
        result = run_anova_rm(valid_df, 'completion_time')
        
        assert 'f_stat' in result
        assert 'p_val' in result
        assert 'corrected_p' in result
        assert 'metric' in result
        assert result['metric'] == 'completion_time'
        assert isinstance(result['f_stat'], float)
        assert isinstance(result['p_val'], float)
    
    def test_validate_anova_input_empty_dataframe(self):
        """Test validation with an empty DataFrame."""
        df_empty = pd.DataFrame()
        required_columns = ['completion_time', 'error_count', 'sus_score', 'interface_type', 'participant_id']
        
        with pytest.raises(DataValidationError) as exc_info:
            validate_anova_input(df_empty, required_columns)
        
        assert 'Missing required columns' in str(exc_info.value)
    
    def test_validate_anova_input_partial_columns(self):
        """Test validation with only some required columns."""
        df_partial = pd.DataFrame({
            'participant_id': ['P001'],
            'interface_type': ['Traditional']
        })
        required_columns = ['completion_time', 'error_count', 'sus_score', 'interface_type', 'participant_id']
        
        with pytest.raises(DataValidationError) as exc_info:
            validate_anova_input(df_partial, required_columns)
        
        assert 'completion_time' in str(exc_info.value)
        assert 'error_count' in str(exc_info.value)
        assert 'sus_score' in str(exc_info.value)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
