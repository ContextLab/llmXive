import pytest
import pandas as pd
import numpy as np
from src.ingestion.validate_dataset import is_valid_entry, validate_and_filter_dataset

class TestIsValidEntry:
    """Unit tests for the is_valid_entry validation function."""

    def test_valid_entry(self):
        """Test that a valid entry passes validation."""
        entry = {
            'python_code': 'print("hello")',
            'javascript_code': 'console.log("hello");'
        }
        assert is_valid_entry(entry) is True

    def test_missing_python_code(self):
        """Test that entry missing python_code fails."""
        entry = {
            'javascript_code': 'console.log("hello");'
        }
        assert is_valid_entry(entry) is False

    def test_missing_js_code(self):
        """Test that entry missing javascript_code fails."""
        entry = {
            'python_code': 'print("hello")'
        }
        assert is_valid_entry(entry) is False

    def test_none_python_code(self):
        """Test that entry with None python_code fails."""
        entry = {
            'python_code': None,
            'javascript_code': 'console.log("hello");'
        }
        assert is_valid_entry(entry) is False

    def test_none_js_code(self):
        """Test that entry with None javascript_code fails."""
        entry = {
            'python_code': 'print("hello")',
            'javascript_code': None
        }
        assert is_valid_entry(entry) is False

    def test_nan_python_code(self):
        """Test that entry with NaN python_code fails."""
        entry = {
            'python_code': np.nan,
            'javascript_code': 'console.log("hello");'
        }
        assert is_valid_entry(entry) is False

    def test_non_string_python_code(self):
        """Test that entry with non-string python_code fails."""
        entry = {
            'python_code': 12345,
            'javascript_code': 'console.log("hello");'
        }
        assert is_valid_entry(entry) is False

    def test_non_string_js_code(self):
        """Test that entry with non-string javascript_code fails."""
        entry = {
            'python_code': 'print("hello")',
            'javascript_code': ['console.log("hello");']
        }
        assert is_valid_entry(entry) is False

    def test_empty_python_code(self):
        """Test that entry with empty python_code fails."""
        entry = {
            'python_code': '',
            'javascript_code': 'console.log("hello");'
        }
        assert is_valid_entry(entry) is False

    def test_whitespace_only_python_code(self):
        """Test that entry with whitespace-only python_code fails."""
        entry = {
            'python_code': '   \n\t  ',
            'javascript_code': 'console.log("hello");'
        }
        assert is_valid_entry(entry) is False

    def test_empty_js_code(self):
        """Test that entry with empty javascript_code fails."""
        entry = {
            'python_code': 'print("hello")',
            'javascript_code': ''
        }
        assert is_valid_entry(entry) is False

class TestValidateAndFilterDataset:
    """Unit tests for the validate_and_filter_dataset function."""

    def test_all_valid_entries(self):
        """Test filtering when all entries are valid."""
        df = pd.DataFrame([
            {'python_code': 'a = 1', 'javascript_code': 'let a = 1;'},
            {'python_code': 'b = 2', 'javascript_code': 'let b = 2;'}
        ])
        filtered_df, excluded = validate_and_filter_dataset(df)
        
        assert len(filtered_df) == 2
        assert len(excluded) == 0

    def test_mixed_validity(self):
        """Test filtering with mixed valid and invalid entries."""
        df = pd.DataFrame([
            {'python_code': 'a = 1', 'javascript_code': 'let a = 1;'},  # Valid
            {'javascript_code': 'let b = 2;'},  # Missing python
            {'python_code': 'c = 3', 'javascript_code': 'let c = 3;'},  # Valid
            {'python_code': None, 'javascript_code': 'let d = 4;'},  # None value
            {'python_code': 'e = 5', 'javascript_code': ''}  # Empty string
        ])
        filtered_df, excluded = validate_and_filter_dataset(df)
        
        assert len(filtered_df) == 2
        assert len(excluded) == 3

    def test_empty_dataframe(self):
        """Test filtering an empty DataFrame."""
        df = pd.DataFrame()
        filtered_df, excluded = validate_and_filter_dataset(df)
        
        assert len(filtered_df) == 0
        assert len(excluded) == 0

    def test_all_invalid_entries(self):
        """Test filtering when all entries are invalid."""
        df = pd.DataFrame([
            {'javascript_code': 'let a = 1;'},
            {'python_code': 'a = 1'},
            {'python_code': None, 'javascript_code': None}
        ])
        filtered_df, excluded = validate_and_filter_dataset(df)
        
        assert len(filtered_df) == 0
        assert len(excluded) == 3

    def test_reset_index(self):
        """Test that the filtered DataFrame has a reset index."""
        df = pd.DataFrame([
            {'python_code': 'a = 1', 'javascript_code': 'let a = 1;'},
            {'javascript_code': 'let b = 2;'},  # Invalid
            {'python_code': 'c = 3', 'javascript_code': 'let c = 3;'}
        ])
        filtered_df, excluded = validate_and_filter_dataset(df)
        
        assert list(filtered_df.index) == [0, 1]