"""
Unit tests for the input validation logic (T005a).

Tests FR-006: Input Validation Logic.
Verifies that validate_input_columns correctly raises ValueError for missing
columns and handles edge cases appropriately.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure code directory is in path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from src.utils.validation import validate_input_columns


class TestValidateInputColumns:
    """Test suite for validate_input_columns function."""
    
    def test_valid_dataframe_with_required_columns(self):
        """Test that a valid DataFrame with all required columns passes validation."""
        df = pd.DataFrame({
            'text_content': ['This is a test', 'Another example'],
            'authenticity_score': [4.5, 3.2],
            'conversation_id': ['conv1', 'conv2']
        })
        
        # Should not raise any exception
        validate_input_columns(df, ['text_content', 'authenticity_score'])
    
    def test_missing_text_content_column(self):
        """Test that ValueError is raised when text_content is missing."""
        df = pd.DataFrame({
            'message': ['This is a test'],
            'authenticity_score': [4.5]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(df, ['text_content', 'authenticity_score'])
        
        assert "missing required columns" in str(exc_info.value).lower()
        assert "text_content" in str(exc_info.value)
    
    def test_missing_authenticity_score_column(self):
        """Test that ValueError is raised when authenticity_score is missing."""
        df = pd.DataFrame({
            'text_content': ['This is a test'],
            'message': ['Another field']
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(df, ['text_content', 'authenticity_score'])
        
        assert "missing required columns" in str(exc_info.value).lower()
        assert "authenticity_score" in str(exc_info.value)
    
    def test_multiple_missing_columns(self):
        """Test that ValueError lists all missing columns."""
        df = pd.DataFrame({
            'random_col': ['value']
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(df, ['text_content', 'authenticity_score', 'id'])
        
        error_msg = str(exc_info.value)
        assert "text_content" in error_msg
        assert "authenticity_score" in error_msg
        assert "id" in error_msg
    
    def test_empty_dataframe(self):
        """Test that ValueError is raised for empty DataFrames."""
        df = pd.DataFrame(columns=['text_content', 'authenticity_score'])
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(df, ['text_content', 'authenticity_score'])
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_none_dataframe(self):
        """Test that ValueError is raised for None input."""
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(None, ['text_content', 'authenticity_score'])
        
        assert "none" in str(exc_info.value).lower()
    
    def test_wrong_type_for_required_cols(self):
        """Test that TypeError is raised if required_cols is not a list/set/tuple."""
        df = pd.DataFrame({
            'text_content': ['test'],
            'authenticity_score': [4.0]
        })
        
        with pytest.raises(TypeError):
            validate_input_columns(df, "text_content")  # String instead of list
    
    def test_text_content_type_validation(self):
        """Test that ValueError is raised if text_content is not object type."""
        df = pd.DataFrame({
            'text_content': [1, 2, 3],  # Numeric instead of string
            'authenticity_score': [4.0, 3.5, 2.0]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(df, ['text_content', 'authenticity_score'])
        
        assert "object (string)" in str(exc_info.value)
    
    def test_authenticity_score_type_validation(self):
        """Test that ValueError is raised if authenticity_score is not numeric."""
        df = pd.DataFrame({
            'text_content': ['test1', 'test2'],
            'authenticity_score': ['high', 'low']  # String instead of numeric
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(df, ['text_content', 'authenticity_score'])
        
        assert "numeric" in str(exc_info.value).lower()
    
    def test_extra_columns_ignored(self):
        """Test that extra columns do not cause validation failure."""
        df = pd.DataFrame({
            'text_content': ['test'],
            'authenticity_score': [4.0],
            'extra_col1': ['a'],
            'extra_col2': [123],
            'metadata': [{'key': 'value'}]
        })
        
        # Should pass validation even with extra columns
        validate_input_columns(df, ['text_content', 'authenticity_score'])
    
    def test_case_sensitive_column_names(self):
        """Test that column name matching is case-sensitive."""
        df = pd.DataFrame({
            'Text_Content': ['test'],  # Wrong case
            'Authenticity_Score': [4.0]  # Wrong case
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_input_columns(df, ['text_content', 'authenticity_score'])
        
        assert "text_content" in str(exc_info.value)
        assert "authenticity_score" in str(exc_info.value)
