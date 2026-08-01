"""
Unit tests for input validation logic (T005a).

These tests verify that FR-006 is correctly implemented:
- Missing columns raise ValueError
- Valid columns pass validation
- Empty dataframes are rejected
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Ensure we can import from the project's src directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.utils.validation import (
    validate_input_columns,
    validate_authenticity_dataframe,
    validate_feature_dataframe,
    REQUIRED_FOR_AUTHENTICITY_ANALYSIS
)


class TestValidateInputColumns:
    """Tests for the validate_input_columns function."""

    def test_all_columns_present(self):
        """Test that validation passes when all required columns exist."""
        df = pd.DataFrame({
            'text_content': ['hello', 'world'],
            'authenticity_score': [4.0, 3.5],
            'extra_column': [1, 2]
        })
        required = ['text_content', 'authenticity_score']
        # Should not raise
        validate_input_columns(df, required)

    def test_missing_one_column(self):
        """Test that ValueError is raised when one required column is missing."""
        df = pd.DataFrame({
            'text_content': ['hello', 'world'],
            # authenticity_score is missing
        })
        required = ['text_content', 'authenticity_score']

        with pytest.raises(ValueError) as excinfo:
            validate_input_columns(df, required)

        assert 'authenticity_score' in str(excinfo.value)
        assert 'Missing required columns' in str(excinfo.value)

    def test_missing_multiple_columns(self):
        """Test that ValueError is raised with multiple missing columns."""
        df = pd.DataFrame({
            'text_content': ['hello', 'world'],
        })
        required = ['text_content', 'authenticity_score', 'conversation_id']

        with pytest.raises(ValueError) as excinfo:
            validate_input_columns(df, required)

        missing = ['authenticity_score', 'conversation_id']
        for col in missing:
            assert col in str(excinfo.value)

    def test_empty_dataframe(self):
        """Test that empty DataFrames are rejected."""
        df = pd.DataFrame(columns=['text_content', 'authenticity_score'])
        required = ['text_content', 'authenticity_score']

        with pytest.raises(ValueError) as excinfo:
            validate_input_columns(df, required)

        assert 'empty' in str(excinfo.value).lower()

    def test_case_sensitive_columns(self):
        """Test that column names are case-sensitive."""
        df = pd.DataFrame({
            'Text_Content': ['hello'],  # Wrong case
            'Authenticity_Score': [4.0]  # Wrong case
        })
        required = ['text_content', 'authenticity_score']

        with pytest.raises(ValueError) as excinfo:
            validate_input_columns(df, required)

        assert 'text_content' in str(excinfo.value)
        assert 'authenticity_score' in str(excinfo.value)

    def test_whitespace_in_column_names(self):
        """Test that whitespace in column names causes failure."""
        df = pd.DataFrame({
            ' text_content ': ['hello'],  # Whitespace around name
            'authenticity_score': [4.0]
        })
        required = ['text_content', 'authenticity_score']

        with pytest.raises(ValueError) as excinfo:
            validate_input_columns(df, required)

        assert 'text_content' in str(excinfo.value)


class TestValidateAuthenticityDataFrame:
    """Tests for the validate_authenticity_dataframe helper."""

    def test_valid_authenticity_data(self):
        """Test validation passes for correctly formatted authenticity data."""
        df = pd.DataFrame({
            'text_content': ['Sample text'],
            'authenticity_score': [4.5]
        })
        # Should not raise
        validate_authenticity_dataframe(df)

    def test_missing_text_content(self):
        """Test failure when text_content is missing."""
        df = pd.DataFrame({
            'authenticity_score': [4.5]
        })
        with pytest.raises(ValueError):
            validate_authenticity_dataframe(df)

    def test_missing_authenticity_score(self):
        """Test failure when authenticity_score is missing."""
        df = pd.DataFrame({
            'text_content': ['Sample text']
        })
        with pytest.raises(ValueError):
            validate_authenticity_dataframe(df)


class TestValidateFeatureDataFrame:
    """Tests for the validate_feature_dataframe helper."""

    def test_valid_feature_data(self):
        """Test validation passes for correctly formatted feature data."""
        df = pd.DataFrame({
            'conversation_id': ['conv_001'],
            'text_content': ['Sample text']
        })
        # Should not raise
        validate_feature_dataframe(df)

    def test_missing_conversation_id(self):
        """Test failure when conversation_id is missing."""
        df = pd.DataFrame({
            'text_content': ['Sample text']
        })
        with pytest.raises(ValueError):
            validate_feature_dataframe(df)

    def test_missing_text_content(self):
        """Test failure when text_content is missing."""
        df = pd.DataFrame({
            'conversation_id': ['conv_001']
        })
        with pytest.raises(ValueError):
            validate_feature_dataframe(df)