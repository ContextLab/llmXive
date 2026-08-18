"""
Unit tests for the validation module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.validation import (
    calculate_match_proportion,
    filter_valid_rows,
    validate_soil_data_coverage,
    SOIL_PREDICTORS
)
from utils.exceptions import DataQualityError

@pytest.fixture
def valid_data():
    """Create a DataFrame with all valid soil data."""
    return pd.DataFrame({
        'species_name': ['A', 'B', 'C'],
        'soil_n': [10.0, 20.0, 30.0],
        'soil_p': [5.0, 10.0, 15.0],
        'soil_k': [100.0, 200.0, 300.0],
        'soil_ph': [6.5, 7.0, 7.5],
        'root_depth': [100.0, 150.0, 200.0]
    })

@pytest.fixture
def mixed_data():
    """Create a DataFrame with some missing soil data."""
    return pd.DataFrame({
        'species_name': ['A', 'B', 'C', 'D'],
        'soil_n': [10.0, np.nan, 30.0, 40.0],
        'soil_p': [5.0, 10.0, np.nan, 20.0],
        'soil_k': [100.0, 200.0, 300.0, np.nan],
        'soil_ph': [6.5, 7.0, 7.5, 8.0],
        'root_depth': [100.0, 150.0, 200.0, 250.0]
    })

@pytest.fixture
def low_quality_data():
    """Create a DataFrame with very low data quality (below 90%)."""
    # 4 rows, only 1 valid -> 25%
    return pd.DataFrame({
        'species_name': ['A', 'B', 'C', 'D'],
        'soil_n': [10.0, np.nan, np.nan, np.nan],
        'soil_p': [5.0, np.nan, np.nan, np.nan],
        'soil_k': [100.0, np.nan, np.nan, np.nan],
        'soil_ph': [6.5, np.nan, np.nan, np.nan],
        'root_depth': [100.0, 150.0, 200.0, 250.0]
    })

def test_calculate_match_proportion_all_valid(valid_data):
    """Test proportion calculation when all data is valid."""
    prop = calculate_match_proportion(valid_data)
    assert prop == 1.0

def test_calculate_match_proportion_mixed(mixed_data):
    """Test proportion calculation with missing values."""
    # 4 rows, only 1 row has all 4 soil predictors non-null (Row A)
    # Row B: soil_n is NaN
    # Row C: soil_p is NaN
    # Row D: soil_k is NaN
    # So only 1 valid row out of 4 = 0.25
    prop = calculate_match_proportion(mixed_data)
    assert prop == 0.25

def test_filter_valid_rows_all_valid(valid_data):
    """Test filtering when all data is valid."""
    valid_df, excluded_df = filter_valid_rows(valid_data)
    assert len(valid_df) == 3
    assert len(excluded_df) == 0

def test_filter_valid_rows_mixed(mixed_data):
    """Test filtering with mixed data quality."""
    valid_df, excluded_df = filter_valid_rows(mixed_data)
    assert len(valid_df) == 1
    assert len(excluded_df) == 3
    # Check that the valid row is 'A'
    assert valid_df.iloc[0]['species_name'] == 'A'

def test_validate_soil_data_coverage_pass(valid_data):
    """Test that validation passes when quality is high."""
    result = validate_soil_data_coverage(valid_data, threshold=0.90)
    assert len(result) == 3

def test_validate_soil_data_coverage_fail(low_quality_data):
    """Test that validation fails when quality is too low."""
    with pytest.raises(DataQualityError) as exc_info:
        validate_soil_data_coverage(low_quality_data, threshold=0.90)
    
    assert "below the required threshold" in str(exc_info.value)

def test_validate_soil_data_coverage_exact_threshold(mixed_data):
    """Test behavior at exact threshold boundary."""
    # mixed_data has 0.25 proportion. If threshold is 0.25, it should pass.
    # If threshold is 0.26, it should fail.
    result = validate_soil_data_coverage(mixed_data, threshold=0.25)
    assert len(result) == 1
    
    with pytest.raises(DataQualityError):
        validate_soil_data_coverage(mixed_data, threshold=0.26)

def test_empty_dataframe():
    """Test handling of empty DataFrames."""
    empty_df = pd.DataFrame(columns=['species_name', 'soil_n', 'soil_p', 'soil_k', 'soil_ph'])
    
    with pytest.raises(DataQualityError):
        validate_soil_data_coverage(empty_df)

def test_missing_columns():
    """Test handling of DataFrames missing required columns."""
    df = pd.DataFrame({'species_name': ['A'], 'other_col': [1]})
    
    with pytest.raises(DataQualityError):
        validate_soil_data_coverage(df)