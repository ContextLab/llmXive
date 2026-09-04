"""
Unit tests for the correlation analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure code path is available
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from modeling.correlations import calculate_correlations

class TestCalculateCorrelations:
    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data."""
        data = pd.DataFrame({
            "mean_atomic_radius": [1.0, 2.0, 3.0, 4.0, 5.0],
            "electronegativity_var": [1.0, 2.0, 3.0, 4.0, 5.0],
            "vec": [1.0, 2.0, 3.0, 4.0, 5.0],
            "size_mismatch": [1.0, 2.0, 3.0, 4.0, 5.0],
            "cte": [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        result = calculate_correlations(data)
        # All features should have correlation of 1.0
        assert result.loc[result["feature"] == "mean_atomic_radius", "correlation_coefficient"].values[0] == 1.0

    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data."""
        data = pd.DataFrame({
            "mean_atomic_radius": [1.0, 2.0, 3.0, 4.0, 5.0],
            "electronegativity_var": [1.0, 2.0, 3.0, 4.0, 5.0],
            "vec": [1.0, 2.0, 3.0, 4.0, 5.0],
            "size_mismatch": [1.0, 2.0, 3.0, 4.0, 5.0],
            "cte": [5.0, 4.0, 3.0, 2.0, 1.0]
        })
        result = calculate_correlations(data)
        assert result.loc[result["feature"] == "mean_atomic_radius", "correlation_coefficient"].values[0] == -1.0

    def test_no_correlation(self):
        """Test with uncorrelated data."""
        np.random.seed(42)
        data = pd.DataFrame({
            "mean_atomic_radius": np.random.rand(100),
            "electronegativity_var": np.random.rand(100),
            "vec": np.random.rand(100),
            "size_mismatch": np.random.rand(100),
            "cte": np.random.rand(100)
        })
        result = calculate_correlations(data)
        # Correlations should be close to 0, but not exactly 0 due to randomness
        # We just check they are finite and within [-1, 1]
        for _, row in result.iterrows():
            assert -1.0 <= row["correlation_coefficient"] <= 1.0
            assert np.isfinite(row["correlation_coefficient"])

    def test_handles_nan(self):
        """Test that NaN values are handled correctly."""
        data = pd.DataFrame({
            "mean_atomic_radius": [1.0, np.nan, 3.0, 4.0, 5.0],
            "electronegativity_var": [1.0, 2.0, np.nan, 4.0, 5.0],
            "vec": [1.0, 2.0, 3.0, np.nan, 5.0],
            "size_mismatch": [1.0, 2.0, 3.0, 4.0, np.nan],
            "cte": [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        result = calculate_correlations(data)
        # Should still calculate correlation for the valid pairs
        for _, row in result.iterrows():
            assert -1.0 <= row["correlation_coefficient"] <= 1.0

    def test_rounding_precision(self):
        """Test that correlations are rounded to 4 decimal places."""
        # Create data that results in a long decimal correlation
        data = pd.DataFrame({
            "mean_atomic_radius": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "electronegativity_var": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 10.0],
            "vec": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "size_mismatch": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "cte": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        })
        result = calculate_correlations(data)
        # Check that the coefficient has at most 4 decimal places
        for _, row in result.iterrows():
            coeff = row["correlation_coefficient"]
            if not np.isnan(coeff):
                # Verify it is a float rounded to 4 decimals
                assert round(coeff, 4) == coeff