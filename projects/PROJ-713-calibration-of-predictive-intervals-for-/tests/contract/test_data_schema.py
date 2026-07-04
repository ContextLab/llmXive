"""
Contract test for data_loader output schema.

Verifies that the data loading and splitting functions return dataframes
with the expected columns, dtypes, and structural properties as defined
in the project specification.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_loader import split_series, standardize
from utils.exceptions import DataValidationError


class TestDataSchema:
    """Contract tests for data loader output schema."""

    @pytest.fixture
    def mock_timeseries_data(self):
        """Generate a mock time series dataset for testing."""
        n_points = 1000
        dates = pd.date_range(start="2020-01-01", periods=n_points, freq="H")
        values = np.sin(np.arange(n_points) * 0.01) + np.random.normal(0, 0.1, n_points)
        
        df = pd.DataFrame({
            "timestamp": dates,
            "value": values,
            "series_id": "test_series_001"
        })
        return df

    def test_split_series_returns_dict(self, mock_timeseries_data):
        """Test that split_series returns a dictionary."""
        result = split_series(mock_timeseries_data, train_ratio=0.8)
        assert isinstance(result, dict), "split_series must return a dictionary"

    def test_split_series_contains_expected_keys(self, mock_timeseries_data):
        """Test that split_series returns train and test sets."""
        result = split_series(mock_timeseries_data, train_ratio=0.8)
        assert "train" in result, "Result must contain 'train' key"
        assert "test" in result, "Result must contain 'test' key"

    def test_split_series_80_20_ratio(self, mock_timeseries_data):
        """Test that split_series respects the 80/20 split ratio."""
        result = split_series(mock_timeseries_data, train_ratio=0.8)
        train_len = len(result["train"])
        test_len = len(result["test"])
        total_len = len(mock_timeseries_data)
        
        assert train_len == int(total_len * 0.8), "Training set must be 80% of data"
        assert test_len == int(total_len * 0.2), "Test set must be 20% of data"
        assert train_len + test_len == total_len, "Split must preserve total length"

    def test_split_series_dtypes_preserved(self, mock_timeseries_data):
        """Test that split_series preserves column dtypes."""
        result = split_series(mock_timeseries_data, train_ratio=0.8)
        
        # Check timestamp column
        assert result["train"]["timestamp"].dtype == mock_timeseries_data["timestamp"].dtype
        assert result["test"]["timestamp"].dtype == mock_timeseries_data["timestamp"].dtype
        
        # Check value column
        assert pd.api.types.is_numeric_dtype(result["train"]["value"])
        assert pd.api.types.is_numeric_dtype(result["test"]["value"])

    def test_split_series_no_nulls_in_test(self, mock_timeseries_data):
        """Test that test set does not contain null values."""
        result = split_series(mock_timeseries_data, train_ratio=0.8)
        assert not result["test"]["value"].isnull().any(), "Test set must not contain null values"

    def test_standardize_returns_dataframe(self, mock_timeseries_data):
        """Test that standardize returns a DataFrame."""
        result = standardize(mock_timeseries_data, "value")
        assert isinstance(result, pd.DataFrame), "standardize must return a DataFrame"

    def test_standardize_preserves_columns(self, mock_timeseries_data):
        """Test that standardize preserves all columns."""
        result = standardize(mock_timeseries_data, "value")
        assert set(result.columns) == set(mock_timeseries_data.columns), \
            "standardize must preserve all original columns"

    def test_standardize_output_has_zero_mean(self, mock_timeseries_data):
        """Test that standardized values have mean close to zero."""
        result = standardize(mock_timeseries_data, "value")
        mean_val = result["value"].mean()
        assert abs(mean_val) < 1e-6, f"Standardized mean should be ~0, got {mean_val}"

    def test_standardize_output_has_unit_variance(self, mock_timeseries_data):
        """Test that standardized values have variance close to one."""
        result = standardize(mock_timeseries_data, "value")
        var_val = result["value"].var()
        assert abs(var_val - 1.0) < 1e-4, f"Standardized variance should be ~1, got {var_val}"

    def test_standardize_handles_constant_series(self, mock_timeseries_data):
        """Test that standardize handles constant series without crashing."""
        constant_data = mock_timeseries_data.copy()
        constant_data["value"] = 5.0
        
        # Should not raise an exception, but may produce NaNs or zeros
        try:
            result = standardize(constant_data, "value")
            # If it runs, check that it returns a DataFrame
            assert isinstance(result, pd.DataFrame)
        except Exception as e:
            # If it raises, it should be a specific error
            assert isinstance(e, (ValueError, DataValidationError)), \
                f"Unexpected error type: {type(e)}"

    def test_split_series_timestamp_order(self, mock_timeseries_data):
        """Test that split_series preserves chronological order."""
        result = split_series(mock_timeseries_data, train_ratio=0.8)
        
        # Check that timestamps are sorted
        assert result["train"]["timestamp"].is_monotonic_increasing
        assert result["test"]["timestamp"].is_monotonic_increasing
        
        # Check that test set starts after train set ends
        train_end = result["train"]["timestamp"].max()
        test_start = result["test"]["timestamp"].min()
        assert test_start > train_end, "Test set must start after train set ends"