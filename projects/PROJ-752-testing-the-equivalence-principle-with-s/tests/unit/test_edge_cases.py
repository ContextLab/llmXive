"""
Unit tests for edge cases: missing data, empty results, and malformed inputs.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.preprocessing import filter_residuals, handle_sparse_satellites, align_time_series
from models.estimator import separate_fit_satellite
from analysis.eotvos import compute_eotvos_parameter
from utils.logging import DataUnavailableError

class TestDataFilteringEdgeCases:
    """Tests for data filtering with edge cases."""

    def test_filter_all_nan(self):
        """Test filtering when all residuals are NaN."""
        df = pd.DataFrame({
            'timestamp': [datetime.now(), datetime.now()],
            'residual': [np.nan, np.nan],
            'satellite_id': ['LAGEOS-1', 'LAGEOS-1']
        })
        result = filter_residuals(df, threshold=0.02)
        assert len(result) == 0, "Expected empty DataFrame when all residuals are NaN."

    def test_filter_all_exceeds(self):
        """Test filtering when all residuals exceed threshold."""
        df = pd.DataFrame({
            'timestamp': [datetime.now(), datetime.now()],
            'residual': [0.05, 0.10],
            'satellite_id': ['LAGEOS-1', 'LAGEOS-1']
        })
        result = filter_residuals(df, threshold=0.02)
        assert len(result) == 0, "Expected empty DataFrame when all residuals exceed threshold."

    def test_filter_none_exceeds(self):
        """Test filtering when no residuals exceed threshold."""
        df = pd.DataFrame({
            'timestamp': [datetime.now(), datetime.now()],
            'residual': [0.001, 0.01],
            'satellite_id': ['LAGEOS-1', 'LAGEOS-1']
        })
        result = filter_residuals(df, threshold=0.02)
        assert len(result) == 2, "Expected all rows to remain."

    def test_filter_empty_input(self):
        """Test filtering with an empty DataFrame."""
        df = pd.DataFrame(columns=['timestamp', 'residual', 'satellite_id'])
        result = filter_residuals(df, threshold=0.02)
        assert len(result) == 0, "Expected empty DataFrame as input was empty."

class TestSparseSatellites:
    """Tests for handling sparse satellite data."""

    def test_handle_empty_satellite_list(self):
        """Test handling an empty list of satellites."""
        satellites = []
        result = handle_sparse_satellites(satellites)
        assert result == [], "Expected empty list for empty input."

    def test_handle_satellite_with_no_data(self):
        """Test handling a satellite with no data points."""
        # Simulating a satellite with 0 days of arc
        satellites = [{'id': 'EMPTY-SAT', 'arc_days': 0, 'data': pd.DataFrame()}]
        result = handle_sparse_satellites(satellites)
        # Should exclude satellites with < 30 days
        excluded_ids = [s['id'] for s in result if s.get('excluded')]
        assert 'EMPTY-SAT' in excluded_ids, "Expected satellite with 0 days to be excluded."

    def test_handle_satellite_with_sufficient_data(self):
        """Test handling a satellite with sufficient data."""
        satellites = [{'id': 'GOOD-SAT', 'arc_days': 45, 'data': pd.DataFrame()}]
        result = handle_sparse_satellites(satellites)
        excluded_ids = [s['id'] for s in result if s.get('excluded')]
        assert 'GOOD-SAT' not in excluded_ids, "Expected satellite with 45 days to be included."

class TestTimeAlignmentEdgeCases:
    """Tests for time alignment edge cases."""

    def test_align_empty_datasets(self):
        """Test aligning empty datasets."""
        dfs = [pd.DataFrame(), pd.DataFrame()]
        result = align_time_series(dfs)
        assert len(result) == 0, "Expected empty result for empty inputs."

    def test_align_no_common_time(self):
        """Test aligning datasets with no common time."""
        df1 = pd.DataFrame({'timestamp': [datetime(2023, 1, 1)], 'val': [1]})
        df2 = pd.DataFrame({'timestamp': [datetime(2023, 1, 2)], 'val': [2]})
        result = align_time_series([df1, df2])
        # Depending on implementation, might be empty or have NaNs. 
        # Assuming strict intersection:
        assert len(result) == 0, "Expected empty result when no common time exists."

class TestEstimatorEdgeCases:
    """Tests for estimator edge cases."""

    def test_fit_empty_data(self):
        """Test fitting on empty data."""
        df = pd.DataFrame(columns=['timestamp', 'range', 'satellite_id'])
        with pytest.raises((ValueError, DataUnavailableError)):
            separate_fit_satellite(df, {'satellite_id': 'TEST'})

    def test_fit_insufficient_points(self):
        """Test fitting on insufficient data points."""
        # Need at least a few points for a fit
        df = pd.DataFrame({
            'timestamp': [datetime.now()],
            'range': [1000.0],
            'satellite_id': ['TEST']
        })
        with pytest.raises((ValueError, DataUnavailableError)):
            separate_fit_satellite(df, {'satellite_id': 'TEST'})

class TestEotvosEdgeCases:
    """Tests for Eotvos calculation edge cases."""

    def test_compute_eta_zero_g(self):
        """Test calculation when g is zero (should raise error)."""
        with pytest.raises(ZeroDivisionError):
            compute_eotvos_parameter(ac=1e-14, g=0.0, cov=[[1e-28, 0], [0, 1e-28]])

    def test_compute_eta_negative_ac(self):
        """Test calculation with negative ac (absolute value should be used)."""
        eta, ci = compute_eotvos_parameter(ac=-1e-14, g=9.8, cov=[[1e-28, 0], [0, 1e-28]])
        assert eta > 0, "Expected positive eta even with negative ac."

    def test_compute_eta_large_uncertainty(self):
        """Test calculation with large uncertainty."""
        eta, ci = compute_eotvos_parameter(ac=1e-14, g=9.8, cov=[[1e-10, 0], [0, 1e-10]])
        # CI should be wide
        assert (ci[1] - ci[0]) > 1e-10, "Expected wide confidence interval."
