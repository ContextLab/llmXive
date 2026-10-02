"""
Unit tests for the uncertainty_calculator module.
"""

import math
import pytest
import pandas as pd
import numpy as np

from code.utils.uncertainty_calculator import (
    calculate_total_uncertainty,
    compute_uncertainties_for_dataframe,
    DEFAULT_PRECISION,
    DEFAULT_EXPERIMENTAL_ERROR
)


class TestCalculateTotalUncertainty:
    """Tests for the calculate_total_uncertainty function."""

    def test_both_values_provided(self):
        """Test calculation with both precision and error provided."""
        precision = 5.0
        error = 12.0
        expected = math.sqrt(5.0**2 + 12.0**2)
        result = calculate_total_uncertainty(precision, error)
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_missing_precision_uses_default(self):
        """Test that missing precision defaults to 10.0."""
        error = 0.0
        expected = math.sqrt(DEFAULT_PRECISION**2 + error**2)
        result = calculate_total_uncertainty(None, error)
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_missing_error_uses_default(self):
        """Test that missing error defaults to 0.0."""
        precision = 10.0
        expected = math.sqrt(precision**2 + DEFAULT_EXPERIMENTAL_ERROR**2)
        result = calculate_total_uncertainty(precision, None)
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_both_missing_uses_defaults(self):
        """Test that both missing values use defaults."""
        expected = math.sqrt(DEFAULT_PRECISION**2 + DEFAULT_EXPERIMENTAL_ERROR**2)
        result = calculate_total_uncertainty(None, None)
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_non_negative_result(self):
        """Test that the result is always non-negative."""
        result = calculate_total_uncertainty(5.0, 5.0)
        assert result >= 0

        result = calculate_total_uncertainty(None, None)
        assert result >= 0

    def test_zero_values(self):
        """Test calculation with zero values."""
        result = calculate_total_uncertainty(0.0, 0.0)
        assert result == 0.0

    def test_large_values(self):
        """Test calculation with large values."""
        precision = 1000.0
        error = 1000.0
        expected = math.sqrt(precision**2 + error**2)
        result = calculate_total_uncertainty(precision, error)
        assert math.isclose(result, expected, rel_tol=1e-9)


class TestComputeUncertaintiesForDataFrame:
    """Tests for the compute_uncertainties_for_dataframe function."""

    def test_basic_computation(self):
        """Test basic uncertainty computation on a DataFrame."""
        data = {
            'formula': ['ABX3', 'CDX3'],
            'T_d': [500, 600],
            'precision_celsius': [5.0, 10.0],
            'experimental_error': [2.0, 3.0]
        }
        df = pd.DataFrame(data)
        result = compute_uncertainties_for_dataframe(df)

        assert 'total_uncertainty' in result.columns
        assert len(result) == 2

        # Check specific values
        expected_0 = math.sqrt(5.0**2 + 2.0**2)
        expected_1 = math.sqrt(10.0**2 + 3.0**2)

        assert math.isclose(result.iloc[0]['total_uncertainty'], expected_0, rel_tol=1e-9)
        assert math.isclose(result.iloc[1]['total_uncertainty'], expected_1, rel_tol=1e-9)

    def test_missing_precision_column(self):
        """Test behavior when precision column is missing (should use default)."""
        data = {
            'formula': ['ABX3'],
            'T_d': [500],
            'experimental_error': [5.0]
        }
        df = pd.DataFrame(data)
        result = compute_uncertainties_for_dataframe(df)

        # Should use default precision (10.0)
        expected = math.sqrt(DEFAULT_PRECISION**2 + 5.0**2)
        assert math.isclose(result.iloc[0]['total_uncertainty'], expected, rel_tol=1e-9)

    def test_missing_error_column(self):
        """Test behavior when error column is missing (should use default)."""
        data = {
            'formula': ['ABX3'],
            'T_d': [500],
            'precision_celsius': [5.0]
        }
        df = pd.DataFrame(data)
        result = compute_uncertainties_for_dataframe(df)

        # Should use default error (0.0)
        expected = math.sqrt(5.0**2 + DEFAULT_EXPERIMENTAL_ERROR**2)
        assert math.isclose(result.iloc[0]['total_uncertainty'], expected, rel_tol=1e-9)

    def test_all_missing_values(self):
        """Test behavior when all values are missing."""
        data = {
            'formula': ['ABX3'],
            'T_d': [500]
        }
        df = pd.DataFrame(data)
        result = compute_uncertainties_for_dataframe(df)

        # Should use both defaults
        expected = math.sqrt(DEFAULT_PRECISION**2 + DEFAULT_EXPERIMENTAL_ERROR**2)
        assert math.isclose(result.iloc[0]['total_uncertainty'], expected, rel_tol=1e-9)

    def test_non_negative_results(self):
        """Test that all results are non-negative."""
        data = {
            'formula': ['ABX3', 'CDX3', 'EFX3'],
            'T_d': [500, 600, 700],
            'precision_celsius': [5.0, None, 15.0],
            'experimental_error': [None, 5.0, None]
        }
        df = pd.DataFrame(data)
        result = compute_uncertainties_for_dataframe(df)

        assert all(result['total_uncertainty'] >= 0)

    def test_custom_column_names(self):
        """Test with custom column names."""
        data = {
            'formula': ['ABX3'],
            'T_d': [500],
            'my_precision': [5.0],
            'my_error': [3.0]
        }
        df = pd.DataFrame(data)
        result = compute_uncertainties_for_dataframe(
            df,
            precision_column='my_precision',
            error_column='my_error',
            output_column='my_uncertainty'
        )

        assert 'my_uncertainty' in result.columns
        expected = math.sqrt(5.0**2 + 3.0**2)
        assert math.isclose(result.iloc[0]['my_uncertainty'], expected, rel_tol=1e-9)