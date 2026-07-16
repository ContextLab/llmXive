"""
Unit tests for input validation logic (T005a).

Tests the validate_input_columns function to ensure it correctly:
1. Passes when all required columns are present
2. Raises ValueError with clear message when columns are missing
3. Handles edge cases (empty required list, wrong input type)
"""
import pytest
import pandas as pd
import numpy as np
from src.utils.validation import validate_input_columns


class TestValidateInputColumns:
    """Test suite for validate_input_columns function."""
    
    def test_all_columns_present(self):
        """Test that validation passes when all required columns exist."""
        df = pd.DataFrame({
            'text_content': ['hello world', 'test text'],
            'authenticity_score': [4, 3],
            'conversation_id': [1, 2]
        })
        
        # Should not raise any exception
        validate_input_columns(df, ['text_content', 'authenticity_score'])
        
    def test_missing_single_column(self):
        """Test that ValueError is raised when one required column is missing."""
        df = pd.DataFrame({
            'text_content': ['hello world'],
            'conversation_id': [1]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(df, ['text_content', 'authenticity_score'])
        
        error_message = str(exc_info.value)
        assert 'authenticity_score' in error_message
        assert 'Missing required columns' in error_message
        
    def test_missing_multiple_columns(self):
        """Test that ValueError lists all missing columns."""
        df = pd.DataFrame({
            'conversation_id': [1, 2, 3]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(df, ['text_content', 'authenticity_score', 'turn_count'])
        
        error_message = str(exc_info.value)
        assert 'text_content' in error_message
        assert 'authenticity_score' in error_message
        assert 'turn_count' in error_message
        
    def test_empty_required_list(self):
        """Test that empty required_cols list passes validation."""
        df = pd.DataFrame({'anything': [1, 2, 3]})
        
        # Should not raise any exception
        validate_input_columns(df, [])
        
    def test_non_dataframe_input(self):
        """Test that TypeError is raised for non-DataFrame inputs."""
        with pytest.raises(TypeError):
            validate_input_columns([1, 2, 3], ['col1'])
            
        with pytest.raises(TypeError):
            validate_input_columns({'col1': [1, 2]}, ['col1'])
            
    def test_case_sensitive_columns(self):
        """Test that column names are case-sensitive."""
        df = pd.DataFrame({
            'Text_Content': ['hello'],  # Wrong case
            'Authenticity_Score': [4]   # Wrong case
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(df, ['text_content', 'authenticity_score'])
        
        error_message = str(exc_info.value)
        assert 'text_content' in error_message
        assert 'authenticity_score' in error_message
        
    def test_extra_columns_allowed(self):
        """Test that extra columns beyond required are allowed."""
        df = pd.DataFrame({
            'text_content': ['hello'],
            'authenticity_score': [4],
            'extra_col1': [1],
            'extra_col2': ['test'],
            'another_extra': [3.14]
        })
        
        # Should pass validation despite extra columns
        validate_input_columns(df, ['text_content', 'authenticity_score'])
        
    def test_specific_fr006_scenario(self):
        """
        Test the specific scenario from FR-006: 
        validating 'text_content' and 'authenticity_score' columns.
        """
        # Valid case - both columns present
        valid_df = pd.DataFrame({
            'text_content': ['Sample conversation text'],
            'authenticity_score': [4.0],
            'metadata': ['extra info']
        })
        validate_input_columns(valid_df, ['text_content', 'authenticity_score'])
        
        # Invalid case - missing 'authenticity_score'
        invalid_df = pd.DataFrame({
            'text_content': ['Sample conversation text'],
            'metadata': ['extra info']
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(invalid_df, ['text_content', 'authenticity_score'])
        
        assert 'authenticity_score' in str(exc_info.value)
        
    def test_dataframe_with_nan_values(self):
        """Test that validation passes even if DataFrame contains NaN values."""
        df = pd.DataFrame({
            'text_content': ['hello', None, 'world'],
            'authenticity_score': [4.0, np.nan, 3.0]
        })
        
        # Validation should pass (column existence, not value validation)
        validate_input_columns(df, ['text_content', 'authenticity_score'])