"""
Unit tests for the bootstrap_aggregator module.

Tests cover:
- aggregate_power_results: Correct aggregation of bootstrap iterations
- compute_confidence_intervals: Wilson score interval calculation
- save_aggregated_results: JSON serialization and file writing
"""

import json
import tempfile
from pathlib import Path

import pytest
import numpy as np

from utils.bootstrap_aggregator import (
    aggregate_power_results,
    compute_confidence_intervals,
    save_aggregated_results
)


class TestAggregatePowerResults:
    """Tests for aggregate_power_results function."""

    def test_basic_aggregation(self):
        """Test basic aggregation of simple results."""
        results = [
            {"sample_size": 10, "kernel": "4s", "alpha": 0.05, "replication_success": True},
            {"sample_size": 10, "kernel": "4s", "alpha": 0.05, "replication_success": True},
            {"sample_size": 10, "kernel": "4s", "alpha": 0.05, "replication_success": False},
            {"sample_size": 20, "kernel": "4s", "alpha": 0.05, "replication_success": True},
        ]

        sample_sizes = [10, 20]
        alpha_values = [0.05]
        kernels = ["4s"]

        aggregated = aggregate_power_results(results, sample_sizes, alpha_values, kernels)

        assert "curves" in aggregated
        assert "4s" in aggregated["curves"]
        assert "0.05" in aggregated["curves"]["4s"]

        # Check rate for N=10: 2/3 = 0.666...
        rates_10 = aggregated["curves"]["4s"]["0.05"]["empirical_rates"][0]
        assert abs(rates_10 - 2/3) < 0.001

        # Check rate for N=20: 1/1 = 1.0
        rates_20 = aggregated["curves"]["4s"]["0.05"]["empirical_rates"][1]
        assert abs(rates_20 - 1.0) < 0.001

    def test_multiple_kernels(self):
        """Test aggregation across multiple kernels."""
        results = [
            {"sample_size": 10, "kernel": "4s", "alpha": 0.05, "replication_success": True},
            {"sample_size": 10, "kernel": "8s", "alpha": 0.05, "replication_success": False},
        ]

        sample_sizes = [10]
        alpha_values = [0.05]
        kernels = ["4s", "8s"]

        aggregated = aggregate_power_results(results, sample_sizes, alpha_values, kernels)

        # 4s: 1/1 = 1.0
        rate_4s = aggregated["curves"]["4s"]["0.05"]["empirical_rates"][0]
        assert abs(rate_4s - 1.0) < 0.001

        # 8s: 0/1 = 0.0
        rate_8s = aggregated["curves"]["8s"]["0.05"]["empirical_rates"][0]
        assert abs(rate_8s - 0.0) < 0.001

    def test_multiple_alphas(self):
        """Test aggregation across multiple alpha values."""
        results = [
            {"sample_size": 10, "kernel": "4s", "alpha": 0.01, "replication_success": True},
            {"sample_size": 10, "kernel": "4s", "alpha": 0.05, "replication_success": False},
            {"sample_size": 10, "kernel": "4s", "alpha": 0.1, "replication_success": True},
        ]

        sample_sizes = [10]
        alpha_values = [0.01, 0.05, 0.1]
        kernels = ["4s"]

        aggregated = aggregate_power_results(results, sample_sizes, alpha_values, kernels)

        # Check each alpha
        assert abs(aggregated["curves"]["4s"]["0.01"]["empirical_rates"][0] - 1.0) < 0.001
        assert abs(aggregated["curves"]["4s"]["0.05"]["empirical_rates"][0] - 0.0) < 0.001
        assert abs(aggregated["curves"]["4s"]["0.1"]["empirical_rates"][0] - 1.0) < 0.001

    def test_missing_fields(self):
        """Test handling of results with missing fields."""
        results = [
            {"sample_size": 10, "kernel": "4s", "replication_success": True},  # Missing alpha
            {"sample_size": 10, "kernel": "4s", "alpha": 0.05, "replication_success": True},
        ]

        sample_sizes = [10]
        alpha_values = [0.05]
        kernels = ["4s"]

        aggregated = aggregate_power_results(results, sample_sizes, alpha_values, kernels)

        # Should only count the complete result
        rate = aggregated["curves"]["4s"]["0.05"]["empirical_rates"][0]
        assert abs(rate - 1.0) < 0.001

    def test_empty_results(self):
        """Test handling of empty results list."""
        results = []
        sample_sizes = [10]
        alpha_values = [0.05]
        kernels = ["4s"]

        aggregated = aggregate_power_results(results, sample_sizes, alpha_values, kernels)

        # Should have NaN rates
        rate = aggregated["curves"]["4s"]["0.05"]["empirical_rates"][0]
        assert np.isnan(rate)


class TestComputeConfidenceIntervals:
    """Tests for compute_confidence_intervals function."""

    def test_basic_ci(self):
        """Test basic confidence interval calculation."""
        rates = [0.5, 0.8, 0.2]
        n = 100

        cis = compute_confidence_intervals(rates, n)

        assert len(cis) == 3

        # Check that intervals are within [0, 1]
        for low, high in cis:
            assert 0 <= low <= high <= 1

    def test_nan_handling(self):
        """Test handling of NaN rates."""
        rates = [np.nan, 0.5, np.nan]
        n = 100

        cis = compute_confidence_intervals(rates, n)

        assert np.isnan(cis[0][0])
        assert not np.isnan(cis[1][0])
        assert np.isnan(cis[2][0])

    def test_zero_iterations(self):
        """Test handling of zero iterations."""
        rates = [0.5]
        n = 0

        cis = compute_confidence_intervals(rates, n)

        assert np.isnan(cis[0][0])


class TestSaveAggregatedResults:
    """Tests for save_aggregated_results function."""

    def test_save_and_load(self):
        """Test saving and reloading aggregated results."""
        aggregated_data = {
            "sample_sizes": [10, 20],
            "alpha_values": [0.05],
            "kernels": ["4s"],
            "curves": {
                "4s": {
                    "0.05": {
                        "empirical_rates": [0.5, 0.8],
                        "confidence_intervals_95": [(0.4, 0.6), (0.7, 0.9)],
                        "n_iterations": [50, 50]
                    }
                }
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_results.json"
            save_aggregated_results(aggregated_data, str(output_path))

            assert output_path.exists()

            with open(output_path, 'r') as f:
                loaded = json.load(f)

            assert "metadata" in loaded
            assert "data" in loaded
            assert loaded["data"]["sample_sizes"] == [10, 20]

    def test_creates_parent_directories(self):
        """Test that parent directories are created if they don't exist."""
        aggregated_data = {"sample_sizes": [10], "curves": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "results.json"
            save_aggregated_results(aggregated_data, str(output_path))

            assert output_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])