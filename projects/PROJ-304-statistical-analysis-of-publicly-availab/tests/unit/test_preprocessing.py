"""
Unit tests for preprocessing functions, specifically the IQR outlier filter.

This test verifies that the IQR filter correctly identifies and removes
decibel outliers while preserving valid data points.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from preprocessing import apply_iqr_filter, clean_traffic_data
from logger import get_logger

logger = get_logger(__name__)


class TestIQRFilter:
    """Tests for the IQR outlier filtering logic."""

    def test_iqr_filter_removes_extreme_outliers(self):
        """Test that extreme outliers are removed by the IQR filter."""
        # Create a dataset with known outliers
        # Normal range: 40-70 dB
        # Outliers: < 20 dB and > 100 dB (assuming 1.5x IQR threshold)
        data = {
            'grid_id': ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7'],
            'date': pd.to_datetime(['2023-01-01'] * 7),
            'noise_db': [50.0, 55.0, 60.0, 65.0, 10.0, 110.0, 58.0]
        }
        df = pd.DataFrame(data)

        # Apply IQR filter
        filtered_df = apply_iqr_filter(df, 'noise_db')

        # The outliers (10.0 and 110.0) should be removed
        assert len(filtered_df) == 5, f"Expected 5 rows, got {len(filtered_df)}"
        assert 10.0 not in filtered_df['noise_db'].values
        assert 110.0 not in filtered_df['noise_db'].values

        # The valid values should remain
        expected_values = {50.0, 55.0, 60.0, 65.0, 58.0}
        actual_values = set(filtered_df['noise_db'].values)
        assert expected_values == actual_values, f"Expected {expected_values}, got {actual_values}"

    def test_iqr_filter_preserves_all_data_when_no_outliers(self):
        """Test that data is preserved when there are no outliers."""
        # Create a dataset with no outliers (all within 1.5*IQR)
        data = {
            'grid_id': ['G1', 'G2', 'G3', 'G4', 'G5'],
            'date': pd.to_datetime(['2023-01-01'] * 5),
            'noise_db': [45.0, 50.0, 55.0, 60.0, 65.0]
        }
        df = pd.DataFrame(data)

        # Apply IQR filter
        filtered_df = apply_iqr_filter(df, 'noise_db')

        # All rows should be preserved
        assert len(filtered_df) == 5, f"Expected 5 rows, got {len(filtered_df)}"
        assert list(filtered_df['noise_db']) == [45.0, 50.0, 55.0, 60.0, 65.0]

    def test_iqr_filter_handles_single_value(self):
        """Test behavior when only one value is present (IQR=0)."""
        data = {
            'grid_id': ['G1'],
            'date': pd.to_datetime(['2023-01-01']),
            'noise_db': [50.0]
        }
        df = pd.DataFrame(data)

        # With a single value, IQR is 0. The filter should keep the value
        # (as it is both Q1 and Q3, so it's within bounds)
        filtered_df = apply_iqr_filter(df, 'noise_db')
        assert len(filtered_df) == 1

    def test_iqr_filter_handles_empty_dataframe(self):
        """Test that an empty DataFrame is handled gracefully."""
        df = pd.DataFrame(columns=['grid_id', 'date', 'noise_db'])

        filtered_df = apply_iqr_filter(df, 'noise_db')
        assert len(filtered_df) == 0

    def test_iqr_filter_correct_bounds_calculation(self):
        """
        Verify the specific bounds calculation for a known distribution.
        
        Data: [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        Q1 = 27.5 (25th percentile)
        Q3 = 82.5 (75th percentile)
        IQR = 55.0
        Lower Bound = 27.5 - 1.5*55 = -55.0
        Upper Bound = 82.5 + 1.5*55 = 165.0
        All values in this range should be kept.
        """
        data = {
            'grid_id': [f'G{i}' for i in range(10)],
            'date': pd.to_datetime(['2023-01-01'] * 10),
            'noise_db': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        }
        df = pd.DataFrame(data)

        filtered_df = apply_iqr_filter(df, 'noise_db')
        
        # All values should be kept as none are outliers
        assert len(filtered_df) == 10

    def test_iqr_filter_removes_values_beyond_calculated_bounds(self):
        """
        Test removal of values explicitly outside calculated bounds.
        
        Data: [40, 45, 50, 55, 60, 65, 70]
        Q1 = 45, Q3 = 65, IQR = 20
        Lower = 45 - 30 = 15
        Upper = 65 + 30 = 95
        If we add 10 (below 15) and 100 (above 95), they should be removed.
        """
        data = {
            'grid_id': [f'G{i}' for i in range(9)],
            'date': pd.to_datetime(['2023-01-01'] * 9),
            'noise_db': [40, 45, 50, 55, 60, 65, 70, 10, 100]
        }
        df = pd.DataFrame(data)

        filtered_df = apply_iqr_filter(df, 'noise_db')

        # Should have 7 rows (10 and 100 removed)
        assert len(filtered_df) == 7
        assert 10 not in filtered_df['noise_db'].values
        assert 100 not in filtered_df['noise_db'].values
        assert set(filtered_df['noise_db'].values) == {40, 45, 50, 55, 60, 65, 70}

    def test_iqr_filter_with_nan_values(self):
        """Test that NaN values are handled (removed or ignored depending on implementation)."""
        data = {
            'grid_id': ['G1', 'G2', 'G3', 'G4'],
            'date': pd.to_datetime(['2023-01-01'] * 4),
            'noise_db': [50.0, np.nan, 60.0, 100.0] # 100 is an outlier
        }
        df = pd.DataFrame(data)

        # The filter should handle NaNs gracefully.
        # Typically, IQR calculation ignores NaNs, but filtering might drop them.
        # We expect the outlier (100) to be removed.
        filtered_df = apply_iqr_filter(df, 'noise_db')

        # Check that 100 is removed
        assert 100.0 not in filtered_df['noise_db'].values
        # The NaN might be removed or kept depending on specific logic, 
        # but the outlier must be gone.
        # If the implementation drops NaNs during filtering, length will be 2 (50, 60)
        # If it keeps NaNs, length will be 3.
        assert len(filtered_df) in [2, 3], f"Unexpected row count: {len(filtered_df)}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
