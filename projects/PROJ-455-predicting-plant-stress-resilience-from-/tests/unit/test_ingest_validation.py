import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from data.ingest import validate_and_handle_rejection, filter_by_recovery_time
from utils.logging import DataRejectionError
from utils.logging import get_logger
import logging
import io
import sys


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4'],
        'recovery_days': [10.0, 15.0, 5.0, 20.0],
        'biomass_change': [0.1, 0.2, -0.1, 0.3],
        'metabolite_1': [100.0, 120.0, 130.0, 110.0],
        'metabolite_2': [50.0, 60.0, 70.0, 55.0]
    })


@pytest.fixture
def df_with_missing():
    """Create a DataFrame with missing values."""
    df = pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4'],
        'recovery_days': [10.0, 15.0, 5.0, 20.0],
        'metabolite_1': [100.0, np.nan, 130.0, 110.0],
        'metabolite_2': [np.nan, 60.0, np.nan, 55.0]
    })
    return df


def test_validate_and_handle_rejection_success(sample_df):
    """Test that successful validation passes through the DataFrame."""
    
    def mock_validation(df):
        if 'recovery_days' not in df.columns:
            raise DataRejectionError("Missing column")
        return df
    
    result = validate_and_handle_rejection(sample_df, mock_validation, "test_validation")
    assert result is not None
    assert len(result) == 4


def test_validate_and_handle_rejection_data_rejection(sample_df, caplog):
    """Test that DataRejectionError is caught and logged correctly."""
    
    def failing_validation(df):
        raise DataRejectionError("Missing >10%")
    
    with pytest.raises(DataRejectionError) as exc_info:
        validate_and_handle_rejection(sample_df, failing_validation, "missing_threshold")
    
    assert "Missing >10%" in str(exc_info.value)
    # Verify log capture (caplog works with pytest logging)
    assert "Dataset rejected" in caplog.text
    assert "missing_threshold" in caplog.text


def test_validate_and_handle_rejection_unexpected_error(sample_df, caplog):
    """Test that unexpected errors are caught and logged."""
    
    def unexpected_error_validation(df):
        raise ValueError("Unexpected error")
    
    with pytest.raises(ValueError):
        validate_and_handle_rejection(sample_df, unexpected_error_validation, "test_validation")
    
    assert "Unexpected error" in caplog.text


def test_filter_by_recovery_time_with_rejection(sample_df):
    """Test that filter_by_recovery_time raises DataRejectionError when column is missing."""
    df_no_col = sample_df.drop(columns=['recovery_days'])
    
    with pytest.raises(DataRejectionError):
        filter_by_recovery_time(df_no_col)


def test_filter_by_recovery_time_valid(sample_df):
    """Test that filter_by_recovery_time works correctly with valid data."""
    result = filter_by_recovery_time(sample_df, min_days=7.0)
    assert len(result) == 3  # S1, S2, S4 should remain
    assert 'S3' not in result['sample_id'].values