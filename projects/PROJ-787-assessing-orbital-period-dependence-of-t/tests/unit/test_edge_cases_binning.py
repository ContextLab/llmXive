"""
Unit tests for edge cases in the binning module.
Tests scenarios such as empty bins, single-planet bins, and extreme period values.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the specific functions to test from the analysis module
# Based on the API surface: code/analysis/binning.py
from analysis.binning import create_log_bins, assign_bin_index, bin_planets_by_period


class TestCreateLogBins:
    """Tests for the create_log_bins function edge cases."""

    def test_empty_dataframe(self):
        """Test bin creation with an empty DataFrame."""
        df = pd.DataFrame(columns=['period', 'radius'])
        bins, bin_edges = create_log_bins(df, 'period', min_period=0.5, max_period=100.0, n_bins=10)
        assert len(bins) == 0
        assert len(bin_edges) == 11  # n_bins + 1 edges

    def test_single_planet(self):
        """Test bin creation with a single planet."""
        df = pd.DataFrame({'period': [10.0], 'radius': [1.5]})
        bins, bin_edges = create_log_bins(df, 'period', min_period=0.5, max_period=100.0, n_bins=10)
        # Should create bins, but only one will contain the planet
        assert len(bins) > 0
        assert len(bin_edges) == 11

    def test_extreme_period_values(self):
        """Test bin creation with extreme period values (very small and very large)."""
        df = pd.DataFrame({
            'period': [0.1, 0.5, 50.0, 150.0],
            'radius': [1.0, 1.5, 2.0, 2.5]
        })
        # min_period is 0.5, so 0.1 should be excluded or handled
        bins, bin_edges = create_log_bins(df, 'period', min_period=0.5, max_period=100.0, n_bins=10)
        # Check that bins are created within the specified range
        assert all(bins['bin_min'] >= 0.5) or len(bins) == 0
        assert all(bins['bin_max'] <= 100.0) or len(bins) == 0

    def test_logarithmic_spacing(self):
        """Test that bins are truly logarithmically spaced."""
        df = pd.DataFrame({'period': [1.0], 'radius': [1.0]})
        _, bin_edges = create_log_bins(df, 'period', min_period=1.0, max_period=100.0, n_bins=2)
        
        # For log spacing: log(100) - log(1) = 2 (in base 10)
        # With 2 bins, the middle edge should be at log(10) = 1.0 (in base 10) -> 10^1 = 10
        expected_middle = 10.0
        assert np.isclose(bin_edges[1], expected_middle, rtol=1e-5)


class TestAssignBinIndex:
    """Tests for the assign_bin_index function edge cases."""

    def test_period_below_min(self):
        """Test assigning bin index for a period below the minimum."""
        bin_edges = np.array([1.0, 10.0, 100.0])
        periods = [0.5, 1.0, 5.0, 10.0, 50.0, 100.0, 150.0]
        indices = assign_bin_index(periods, bin_edges)
        
        # Periods below min should get -1 or be excluded
        assert indices[0] == -1  # 0.5 is below min
        assert indices[1] == 0   # 1.0 is at min (inclusive)
        assert indices[-1] == -1 # 150.0 is above max

    def test_period_above_max(self):
        """Test assigning bin index for a period above the maximum."""
        bin_edges = np.array([1.0, 10.0, 100.0])
        periods = [150.0]
        indices = assign_bin_index(periods, bin_edges)
        assert indices[0] == -1

    def test_edge_case_exactly_on_boundary(self):
        """Test periods exactly on bin boundaries."""
        bin_edges = np.array([1.0, 10.0, 100.0])
        periods = [1.0, 10.0, 100.0]
        indices = assign_bin_index(periods, bin_edges)
        
        # 1.0 -> bin 0, 10.0 -> bin 1 (or 0 depending on implementation), 100.0 -> excluded
        # Typically: [1, 10) -> bin 0, [10, 100) -> bin 1, 100 -> excluded
        assert indices[0] == 0
        assert indices[1] == 1
        assert indices[2] == -1

    def test_single_bin(self):
        """Test assigning bin index when there is only one bin."""
        bin_edges = np.array([1.0, 100.0])
        periods = [5.0, 50.0]
        indices = assign_bin_index(periods, bin_edges)
        assert indices[0] == 0
        assert indices[1] == 0


class TestBinPlanetsByPeriod:
    """Tests for the bin_planets_by_period function edge cases."""

    def test_empty_input(self):
        """Test binning with an empty DataFrame."""
        df = pd.DataFrame(columns=['period', 'radius', 'radius_uncertainty'])
        result = bin_planets_by_period(df, min_period=0.5, max_period=100.0, n_bins=10)
        assert result.empty
        assert 'bin_index' not in result.columns or len(result) == 0

    def test_all_planets_excluded(self):
        """Test binning when all planets fall outside the period range."""
        df = pd.DataFrame({
            'period': [0.1, 0.2, 200.0, 300.0],
            'radius': [1.0, 1.5, 2.0, 2.5],
            'radius_uncertainty': [0.1, 0.1, 0.1, 0.1]
        })
        result = bin_planets_by_period(df, min_period=0.5, max_period=100.0, n_bins=10)
        # All should be excluded
        assert result.empty or (result['bin_index'] == -1).all()

    def test_single_planet_in_range(self):
        """Test binning with a single planet within the range."""
        df = pd.DataFrame({
            'period': [10.0],
            'radius': [1.5],
            'radius_uncertainty': [0.1]
        })
        result = bin_planets_by_period(df, min_period=0.5, max_period=100.0, n_bins=10)
        assert len(result) == 1
        assert result['bin_index'].iloc[0] >= 0

    def test_duplicate_periods(self):
        """Test binning with duplicate period values."""
        df = pd.DataFrame({
            'period': [10.0, 10.0, 10.0],
            'radius': [1.5, 1.6, 1.7],
            'radius_uncertainty': [0.1, 0.1, 0.1]
        })
        result = bin_planets_by_period(df, min_period=0.5, max_period=100.0, n_bins=10)
        assert len(result) == 3
        # All should be in the same bin
        assert result['bin_index'].nunique() == 1

    def test_malformed_data(self):
        """Test binning with malformed data (NaN, inf)."""
        df = pd.DataFrame({
            'period': [10.0, np.nan, np.inf, -5.0, 50.0],
            'radius': [1.5, 1.6, 1.7, 1.8, 2.0],
            'radius_uncertainty': [0.1, 0.1, 0.1, 0.1, 0.1]
        })
        # The function should handle these gracefully (drop or assign -1)
        result = bin_planets_by_period(df, min_period=0.5, max_period=100.0, n_bins=10)
        # Valid planets should be binned, invalid ones should be excluded
        assert len(result) <= 5
        # At least the valid ones (10.0 and 50.0) should be present
        valid_periods = result[result['bin_index'] >= 0]['period']
        assert 10.0 in valid_periods.values or 50.0 in valid_periods.values

    def test_very_small_periods(self):
        """Test binning with very small period values."""
        df = pd.DataFrame({
            'period': [0.5, 0.6, 0.7],
            'radius': [1.0, 1.1, 1.2],
            'radius_uncertainty': [0.1, 0.1, 0.1]
        })
        result = bin_planets_by_period(df, min_period=0.5, max_period=100.0, n_bins=10)
        assert len(result) == 3
        assert result['bin_index'].iloc[0] >= 0
        assert result['bin_index'].iloc[1] >= 0
        assert result['bin_index'].iloc[2] >= 0

    def test_very_large_periods(self):
        """Test binning with very large period values."""
        df = pd.DataFrame({
            'period': [80.0, 90.0, 99.0],
            'radius': [1.0, 1.1, 1.2],
            'radius_uncertainty': [0.1, 0.1, 0.1]
        })
        result = bin_planets_by_period(df, min_period=0.5, max_period=100.0, n_bins=10)
        assert len(result) == 3
        assert result['bin_index'].iloc[0] >= 0
        assert result['bin_index'].iloc[1] >= 0
        assert result['bin_index'].iloc[2] >= 0