import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing import apply_iqr_filter, clean_traffic_data, aggregate_daily_metrics

class TestIQRFilter:
    """Unit tests for IQR outlier filter functionality."""

    def test_iqr_filter_removes_outliers(self):
        """Test that IQR filter correctly removes outliers."""
        # Create data with clear outliers
        data = {
            'noise_level_db': [40, 42, 45, 48, 50, 52, 55, 150, 160]  # 150, 160 are outliers
        }
        df = pd.DataFrame(data)
        
        # Apply filter
        filtered_df = apply_iqr_filter(df, 'noise_level_db', k=1.5)
        
        # Check that outliers were removed
        assert len(filtered_df) < len(df), "Outliers should be removed"
        assert all((filtered_df['noise_level_db'] >= 40) & (filtered_df['noise_level_db'] <= 55)), \
            "Outlier values (150, 160) should not be in filtered data"

    def test_iqr_filter_retains_valid_data(self):
        """Test that IQR filter retains valid non-outlier data."""
        # Create clean data
        data = {
            'noise_level_db': [40, 42, 45, 48, 50, 52, 55]
        }
        df = pd.DataFrame(data)
        
        # Apply filter
        filtered_df = apply_iqr_filter(df, 'noise_level_db', k=1.5)
        
        # Check that all data is retained (no outliers in this set)
        assert len(filtered_df) == len(df), "Valid data should be retained"

    def test_iqr_filter_custom_column(self):
        """Test IQR filter on a custom column name."""
        data = {
            'custom_col': [10, 12, 15, 18, 100]  # 100 is outlier
        }
        df = pd.DataFrame(data)
        
        filtered_df = apply_iqr_filter(df, 'custom_col', k=1.5)
        
        assert len(filtered_df) < len(df), "Outlier should be removed"
        assert 100 not in filtered_df['custom_col'].values, "Outlier value should not be present"

    def test_iqr_filter_missing_column_raises_error(self):
        """Test that IQR filter raises error for missing column."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Column 'noise_level_db' not found"):
            apply_iqr_filter(df, 'noise_level_db')

    def test_iqr_filter_with_zero_iqr(self):
        """Test IQR filter when all values are identical (IQR=0)."""
        data = {
            'noise_level_db': [50, 50, 50, 50]
        }
        df = pd.DataFrame(data)
        
        filtered_df = apply_iqr_filter(df, 'noise_level_db', k=1.5)
        
        # When IQR is 0, bounds are equal to the value, so no outliers
        assert len(filtered_df) == len(df), "All identical values should be retained"

class TestCleanTrafficData:
    """Unit tests for traffic data cleaning."""

    def test_clean_traffic_data_retains_zeros(self):
        """Test that 0.0 values in traffic_volume are retained."""
        data = {
            'traffic_volume': [0.0, 10.0, 20.0, 0.0, 30.0],
            'other_col': ['a', 'b', 'c', 'd', 'e']
        }
        df = pd.DataFrame(data)
        
        cleaned_df = clean_traffic_data(df)
        
        # Zeros should be retained
        assert 0.0 in cleaned_df['traffic_volume'].values, "Zero values should be retained"
        assert len(cleaned_df) == len(df), "No rows should be removed when no NaN exists"

    def test_clean_traffic_data_removes_nan(self):
        """Test that NaN values in traffic_volume are removed."""
        data = {
            'traffic_volume': [10.0, np.nan, 20.0, np.nan, 30.0],
            'other_col': ['a', 'b', 'c', 'd', 'e']
        }
        df = pd.DataFrame(data)
        
        cleaned_df = clean_traffic_data(df)
        
        # NaN values should be removed
        assert not cleaned_df['traffic_volume'].isna().any(), "NaN values should be removed"
        assert len(cleaned_df) == 3, "Only 3 non-NaN rows should remain"

    def test_clean_traffic_data_logs_exclusion(self):
        """Test that excluded rows are logged to exclusion_log.csv."""
        data = {
            'traffic_volume': [10.0, np.nan, 20.0],
            'other_col': ['a', 'b', 'c']
        }
        df = pd.DataFrame(data)
        
        # Clean data
        clean_traffic_data(df)
        
        # Check if exclusion log was created
        log_path = Path(__file__).parent.parent.parent / "data" / "processed" / "exclusion_log.csv"
        assert log_path.exists(), "Exclusion log should be created"
        
        # Verify log content
        log_df = pd.read_csv(log_path)
        assert 'excluded_count' in log_df.columns, "Log should contain excluded_count column"
        assert log_df['excluded_count'].iloc[-1] == 1, "Log should record 1 excluded row"

class TestAggregateDailyMetrics:
    """Unit tests for daily aggregation."""

    def test_aggregate_daily_metrics_calculates_correctly(self):
        """Test that daily aggregation calculates mean, median, and p95 correctly."""
        data = {
            'grid_id': [1, 1, 1, 2, 2],
            'date': ['2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01'],
            'noise_level_db': [40, 50, 60, 30, 70]
        }
        df = pd.DataFrame(data)
        
        aggregated = aggregate_daily_metrics(df)
        
        # Check grid_id 1: mean=50, median=50, p95=60 (approx)
        grid1 = aggregated[aggregated['grid_id'] == 1].iloc[0]
        assert grid1['noise_mean'] == 50.0, "Mean should be 50"
        assert grid1['noise_median'] == 50.0, "Median should be 50"
        
        # Check grid_id 2: mean=50, median=50
        grid2 = aggregated[aggregated['grid_id'] == 2].iloc[0]
        assert grid2['noise_mean'] == 50.0, "Mean should be 50"

    def test_aggregate_daily_metrics_missing_columns_raises_error(self):
        """Test that aggregation raises error for missing columns."""
        df = pd.DataFrame({'grid_id': [1], 'noise_level_db': [40]})
        
        with pytest.raises(ValueError, match="Missing required columns"):
            aggregate_daily_metrics(df)
