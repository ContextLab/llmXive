"""
Unit tests for error reduction calculation in code/analysis/comparison.py.

This module validates the logic for computing RMSE and percentage error reduction
between a new reconstruction and a baseline model over the satellite-era overlap.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.comparison import calculate_error_reduction, compute_rmse


class TestComputeRMSE:
    """Tests for the compute_rmse helper function."""

    def test_rmse_identical_arrays(self):
        """RMSE should be 0.0 if arrays are identical."""
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([10.0, 20.0, 30.0])
        rmse = compute_rmse(y_true, y_pred)
        assert rmse == 0.0

    def test_rmse_constant_offset(self):
        """RMSE should equal the absolute value of a constant offset."""
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([12.0, 22.0, 32.0])  # Offset by +2
        rmse = compute_rmse(y_true, y_pred)
        assert np.isclose(rmse, 2.0)

    def test_rmse_single_value(self):
        """RMSE for a single value."""
        y_true = np.array([100.0])
        y_pred = np.array([110.0])
        rmse = compute_rmse(y_true, y_pred)
        assert np.isclose(rmse, 10.0)

    def test_rmse_with_nan_handling(self):
        """RMSE should raise error if NaNs are present (no masking in simple impl)."""
        y_true = np.array([10.0, np.nan, 30.0])
        y_pred = np.array([10.0, 20.0, 30.0])
        with pytest.raises(ValueError):
            compute_rmse(y_true, y_pred)


class TestCalculateErrorReduction:
    """Tests for the calculate_error_reduction main function."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create synthetic data for the satellite era overlap (2016-present)
        # Using realistic TSI values around 1361 W/m^2
        self.satellite_years = np.arange(2016, 2024)
        self.new_tsi = 1361.0 + np.array([0.1, -0.2, 0.3, -0.1, 0.2, -0.3, 0.1, 0.0])
        self.baseline_tsi = 1361.0 + np.array([0.5, -0.6, 0.8, -0.5, 0.7, -0.9, 0.4, 0.3])
        
        # Create DataFrames
        self.new_df = pd.DataFrame({
            'year': self.satellite_years,
            'tsi': self.new_tsi
        })
        self.baseline_df = pd.DataFrame({
            'year': self.satellite_years,
            'tsi': self.baseline_tsi
        })

    def test_error_reduction_positive(self):
        """
        Test that error reduction is positive when new model is better.
        New model errors: ~0.2 RMS
        Baseline errors: ~0.7 RMS
        """
        result = calculate_error_reduction(
            new_reconstruction=self.new_df,
            baseline_reconstruction=self.baseline_df,
            year_col='year',
            value_col='tsi',
            start_year=2016,
            end_year=2024
        )

        assert 'rmse_new' in result
        assert 'rmse_baseline' in result
        assert 'percentage_reduction' in result

        # New model should have lower RMSE
        assert result['rmse_new'] < result['rmse_baseline']
        
        # Percentage reduction should be positive
        assert result['percentage_reduction'] > 0.0

        # Check calculation logic manually
        expected_rmse_new = np.sqrt(np.mean((self.new_tsi - 1361.0)**2))
        expected_rmse_baseline = np.sqrt(np.mean((self.baseline_tsi - 1361.0)**2))
        
        assert np.isclose(result['rmse_new'], expected_rmse_new)
        assert np.isclose(result['rmse_baseline'], expected_rmse_baseline)

    def test_error_reduction_negative(self):
        """Test that error reduction is negative when new model is worse."""
        # Swap the dataframes so baseline is better
        result = calculate_error_reduction(
            new_reconstruction=self.baseline_df,
            baseline_reconstruction=self.new_df,
            year_col='year',
            value_col='tsi',
            start_year=2016,
            end_year=2024
        )

        assert result['percentage_reduction'] < 0.0

    def test_error_reduction_zero(self):
        """Test that error reduction is zero when models are identical."""
        result = calculate_error_reduction(
            new_reconstruction=self.new_df,
            baseline_reconstruction=self.new_df,
            year_col='year',
            value_col='tsi',
            start_year=2016,
            end_year=2024
        )

        assert result['percentage_reduction'] == 0.0

    def test_filtering_by_year_range(self):
        """Test that only data within the specified year range is used."""
        # Add data outside the range
        extended_new = pd.concat([
            pd.DataFrame({'year': [2010, 2012], 'tsi': [1360.0, 1360.0]}),
            self.new_df,
            pd.DataFrame({'year': [2030], 'tsi': [1360.0]})
        ]).reset_index(drop=True)
        
        extended_baseline = pd.concat([
            pd.DataFrame({'year': [2010, 2012], 'tsi': [1360.5, 1360.5]}),
            self.baseline_df,
            pd.DataFrame({'year': [2030], 'tsi': [1360.5]})
        ]).reset_index(drop=True)

        result = calculate_error_reduction(
            new_reconstruction=extended_new,
            baseline_reconstruction=extended_baseline,
            year_col='year',
            value_col='tsi',
            start_year=2016,
            end_year=2024
        )

        # Should match the result from the filtered setup_method data
        expected_result = calculate_error_reduction(
            new_reconstruction=self.new_df,
            baseline_reconstruction=self.baseline_df,
            year_col='year',
            value_col='tsi',
            start_year=2016,
            end_year=2024
        )

        assert result['rmse_new'] == expected_result['rmse_new']
        assert result['rmse_baseline'] == expected_result['rmse_baseline']

    def test_empty_overlap_raises_error(self):
        """Test that an error is raised if no data overlaps the year range."""
        new_future = pd.DataFrame({
            'year': [2050, 2051],
            'tsi': [1361.0, 1361.0]
        })
        baseline_future = pd.DataFrame({
            'year': [2050, 2051],
            'tsi': [1361.0, 1361.0]
        })

        with pytest.raises(ValueError, match="No data found in the specified year range"):
            calculate_error_reduction(
                new_reconstruction=new_future,
                baseline_reconstruction=baseline_future,
                year_col='year',
                value_col='tsi',
                start_year=2016,
                end_year=2024
            )

    def test_mismatched_columns_raises_error(self):
        """Test that an error is raised if required columns are missing."""
        bad_df = pd.DataFrame({
            'year': [2016, 2017],
            'value': [1361.0, 1361.0]  # Wrong column name
        })

        with pytest.raises(KeyError):
            calculate_error_reduction(
                new_reconstruction=bad_df,
                baseline_reconstruction=self.baseline_df,
                year_col='year',
                value_col='tsi',
                start_year=2016,
                end_year=2024
            )