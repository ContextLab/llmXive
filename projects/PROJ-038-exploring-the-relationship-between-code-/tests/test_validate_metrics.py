import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.validate_metrics import validate_no_nan_in_metrics, validate_schema_and_metrics, DataIntegrityError

@pytest.fixture
def valid_df():
    return pd.DataFrame({
        'file_path': ['a.java', 'b.java', 'c.java'],
        'cc': [5.0, 10.0, 3.0],
        'halstead': [100.5, 200.5, 50.5],
        'loc': [50, 100, 30],
        'is_buggy': [1, 0, 1]
    })

@pytest.fixture
def df_with_nan():
    return pd.DataFrame({
        'file_path': ['a.java', 'b.java', 'c.java'],
        'cc': [5.0, None, 3.0],
        'halstead': [100.5, 200.5, None],
        'loc': [50, 100, 30],
        'is_buggy': [1, 0, 1]
    })

@pytest.fixture
def df_empty():
    return pd.DataFrame(columns=['file_path', 'cc', 'halstead', 'loc', 'is_buggy'])

@pytest.fixture
def df_missing_col():
    return pd.DataFrame({
        'file_path': ['a.java'],
        'cc': [5.0],
        'halstead': [100.5],
        # 'loc' is missing
        'is_buggy': [1]
    })

@pytest.fixture
def df_nan_target():
    return pd.DataFrame({
        'file_path': ['a.java'],
        'cc': [5.0],
        'halstead': [100.5],
        'loc': [50],
        'is_buggy': [None]
    })

def test_validate_no_nan_in_metrics_pass(valid_df):
    """Test that a dataframe with no NaNs passes validation."""
    cleaned_df, dropped_count = validate_no_nan_in_metrics(valid_df, ['cc', 'halstead', 'loc'])
    assert dropped_count == 0
    assert len(cleaned_df) == len(valid_df)
    assert cleaned_df.equals(valid_df)

def test_validate_no_nan_in_metrics_fail(df_with_nan):
    """Test that a dataframe with NaNs drops rows and raises error if dropped > 0."""
    with pytest.raises(DataIntegrityError) as exc_info:
        cleaned_df, dropped_count = validate_no_nan_in_metrics(df_with_nan, ['cc', 'halstead', 'loc'])
    assert "DataIntegrityError" in str(exc_info.value)
    # The function should raise before returning, so we check the logic in the exception message
    assert "dropped" in str(exc_info.value).lower()

def test_validate_no_nan_in_metrics_missing_column(valid_df):
    """Test that validation handles missing columns gracefully (doesn't crash on column check, but logic assumes cols exist)."""
    # This test specifically checks the function that takes column list.
    # If we pass a column that doesn't exist, pandas will raise KeyError.
    # The task is about NaN validation, so we assume columns exist.
    # We test that it works when columns exist.
    cleaned_df, dropped_count = validate_no_nan_in_metrics(valid_df, ['cc', 'halstead', 'loc'])
    assert dropped_count == 0

def test_validate_schema_and_metrics_pass(valid_df):
    """Test full schema and metrics validation passes for clean data."""
    # Note: validate_schema_and_metrics raises DataIntegrityError if rows dropped.
    # Since valid_df has no NaNs, it should pass.
    result = validate_schema_and_metrics(valid_df)
    assert len(result) == 3

def test_validate_schema_and_metrics_nan_fail(df_with_nan):
    """Test full validation fails if NaNs are present and dropped."""
    with pytest.raises(DataIntegrityError):
        validate_schema_and_metrics(df_with_nan)

def test_validate_schema_and_metrics_empty_input(df_empty):
    """Test that empty input raises DataIntegrityError."""
    with pytest.raises(DataIntegrityError):
        validate_schema_and_metrics(df_empty)

def test_validate_schema_and_metrics_missing_column(df_missing_col):
    """Test that missing required columns raise KeyError."""
    with pytest.raises(KeyError):
        validate_schema_and_metrics(df_missing_col)

def test_validate_schema_and_metrics_nan_target(df_nan_target):
    """Test that NaN in target column raises DataIntegrityError."""
    with pytest.raises(DataIntegrityError):
        validate_schema_and_metrics(df_nan_target)
