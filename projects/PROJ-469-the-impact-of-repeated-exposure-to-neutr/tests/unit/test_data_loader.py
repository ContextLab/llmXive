"""
Unit tests for data_loader.py functionality.

Tests:
- T010: Contract test for data loading - verifies ValueError on missing columns
"""

import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path

# Import the function under test
from data_loader import check_required_columns, load_csv

# Required columns as defined in the project schema (contracts/dataset.schema.yaml)
REQUIRED_COLUMNS = ['IAT_D_score', 'political_ideology', 'news_exposure_freq']

def test_load_raises_valueerror_on_missing_columns():
    """
    T010: Contract test for data loading.
    
    Verifies that load_csv raises a ValueError when required columns are missing
    from the dataset. This ensures data contract enforcement before processing.
    
    Scenario:
    1. Create a temporary CSV file with some but not all required columns
    2. Attempt to load it using load_csv with validation enabled
    3. Verify ValueError is raised with appropriate message
    """
    
    # Create a temporary directory and file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = Path(tmpdir) / "incomplete_data.csv"
        
        # Create a DataFrame with missing columns (only has IAT_D_score)
        incomplete_df = pd.DataFrame({
            'IAT_D_score': [0.1, 0.2, 0.3],
            'other_column': ['a', 'b', 'c']
            # Missing: political_ideology, news_exposure_freq
        })
        
        # Write to CSV
        incomplete_df.to_csv(tmpfile, index=False)
        
        # Test that check_required_columns raises ValueError
        with pytest.raises(ValueError) as excinfo:
            check_required_columns(incomplete_df, REQUIRED_COLUMNS)
        
        # Verify the error message contains helpful information
        error_message = str(excinfo.value)
        assert "missing required columns" in error_message.lower()
        assert "political_ideology" in error_message
        assert "news_exposure_freq" in error_message
        
        # Also test with load_csv when validation is enabled
        with pytest.raises(ValueError) as excinfo:
            load_csv(str(tmpfile), validate_columns=True)
        
        error_message = str(excinfo.value)
        assert "missing required columns" in error_message.lower()

def test_load_succeeds_with_all_columns():
    """
    Positive test: verify load_csv succeeds when all required columns are present.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = Path(tmpdir) / "complete_data.csv"
        
        # Create a DataFrame with all required columns
        complete_df = pd.DataFrame({
            'IAT_D_score': [0.1, 0.2, 0.3],
            'political_ideology': [-1.5, 0.0, 1.5],
            'news_exposure_freq': [2, 5, 8],
            'extra_column': ['x', 'y', 'z']  # Extra columns should be allowed
        })
        
        complete_df.to_csv(tmpfile, index=False)
        
        # This should not raise an exception
        result_df = load_csv(str(tmpfile), validate_columns=True)
        
        assert result_df is not None
        assert len(result_df) == 3
        assert all(col in result_df.columns for col in REQUIRED_COLUMNS)

def test_check_required_columns_empty_dataframe():
    """
    Edge case: verify behavior with empty DataFrame.
    """
    empty_df = pd.DataFrame()
    
    with pytest.raises(ValueError):
        check_required_columns(empty_df, REQUIRED_COLUMNS)

def test_check_required_columns_partial_missing():
    """
    Edge case: verify behavior when only one required column is missing.
    """
    partial_df = pd.DataFrame({
        'IAT_D_score': [0.1, 0.2],
        'political_ideology': [1.0, 2.0]
        # Missing: news_exposure_freq
    })
    
    with pytest.raises(ValueError) as excinfo:
        check_required_columns(partial_df, REQUIRED_COLUMNS)
    
    error_message = str(excinfo.value)
    assert "news_exposure_freq" in error_message
    assert "IAT_D_score" not in error_message  # Should not complain about present columns
    assert "political_ideology" not in error_message