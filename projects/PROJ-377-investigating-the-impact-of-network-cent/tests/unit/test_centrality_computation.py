import pytest
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
import tempfile
import os

from code.analysis.centrality import (
    extract_connectivity_matrix_for_subject,
    process_subject,
)


class TestExtractConnectivityMatrixForSubject:
    def test_returns_matrix(self):
        """Test that the function returns a connectivity matrix."""
        # Create a mock time series data
        n_regions = 10
        n_timepoints = 100
        time_series = np.random.randn(n_timepoints, n_regions)

        result = extract_connectivity_matrix_for_subject(time_series)

        assert isinstance(result, np.ndarray)
        assert result.shape == (n_regions, n_regions)

    def test_matrix_is_symmetric(self):
        """Test that the correlation matrix is symmetric."""
        n_regions = 10
        n_timepoints = 100
        time_series = np.random.randn(n_timepoints, n_regions)

        result = extract_connectivity_matrix_for_subject(time_series)

        # Correlation matrix should be symmetric
        np.testing.assert_array_almost_equal(result, result.T)

    def test_diagonal_is_ones(self):
        """Test that the diagonal of the correlation matrix is ones."""
        n_regions = 10
        n_timepoints = 100
        time_series = np.random.randn(n_timepoints, n_regions)

        result = extract_connectivity_matrix_for_subject(time_series)

        # Diagonal should be 1 (self-correlation)
        np.testing.assert_array_almost_equal(np.diag(result), np.ones(n_regions))

    def test_handles_small_sample(self):
        """Test behavior with small sample size."""
        n_regions = 5
        n_timepoints = 10
        time_series = np.random.randn(n_timepoints, n_regions)

        result = extract_connectivity_matrix_for_subject(time_series)

        assert result.shape == (n_regions, n_regions)

    def test_handles_constant_time_series(self):
        """Test behavior with constant time series (should handle division by zero)."""
        n_regions = 5
        n_timepoints = 10
        time_series = np.ones((n_timepoints, n_regions))

        # Should handle without crashing, possibly returning NaN or 0
        result = extract_connectivity_matrix_for_subject(time_series)
        assert result.shape == (n_regions, n_regions)


class TestProcessSubject:
    def test_returns_expected_keys(self):
        """Test that process_subject returns expected keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock data
            subject_id = "sub-001"
            time_series_path = Path(tmpdir) / "time_series.npy"
            region_names = [f"Region_{i}" for i in range(10)]
            region_names_path = Path(tmpdir) / "region_names.txt"

            time_series = np.random.randn(100, 10)
            np.save(time_series_path, time_series)

            with open(region_names_path, 'w') as f:
                f.write('\n'.join(region_names))

            result = process_subject(subject_id, str(time_series_path), str(region_names_path))

            assert isinstance(result, dict)
            assert 'subject_id' in result
            assert 'centrality_metrics' in result
            assert 'mean_fd' in result

    def test_handles_missing_time_series(self):
        """Test behavior when time series file is missing."""
        with pytest.raises(FileNotFoundError):
            process_subject("sub-001", "/nonexistent/path.npy", "/some/path.txt")

    def test_handles_missing_region_names(self):
        """Test behavior when region names file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            time_series_path = Path(tmpdir) / "time_series.npy"
            time_series = np.random.randn(100, 10)
            np.save(time_series_path, time_series)

            with pytest.raises(FileNotFoundError):
                process_subject("sub-001", str(time_series_path), "/nonexistent/path.txt")

    def test_mismatched_dimensions(self):
        """Test behavior when time series and region names dimensions don't match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subject_id = "sub-001"
            time_series_path = Path(tmpdir) / "time_series.npy"
            region_names_path = Path(tmpdir) / "region_names.txt"

            # 10 regions in time series
            time_series = np.random.randn(100, 10)
            np.save(time_series_path, time_series)

            # Only 5 region names
            region_names = [f"Region_{i}" for i in range(5)]
            with open(region_names_path, 'w') as f:
                f.write('\n'.join(region_names))

            # Should handle gracefully or raise appropriate error
            with pytest.raises((ValueError, IndexError)):
                process_subject(subject_id, str(time_series_path), str(region_names_path))
