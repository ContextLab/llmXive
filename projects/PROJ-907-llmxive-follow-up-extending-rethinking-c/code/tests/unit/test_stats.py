"""
Unit tests for statistical analysis module (T023, T026).

Tests the bootstrap significance test and paired difference statistics.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.stats_analysis import (
    perform_bootstrap_test,
    compute_paired_difference_stats,
    run_statistical_analysis
)


class TestBootstrapSignificance:
    """Tests for the bootstrap significance testing functionality."""

    def test_perform_bootstrap_test_basic(self):
        """Test basic bootstrap functionality with known data."""
        # Create a simple difference list
        differences = [0.1, 0.2, 0.3, 0.4, 0.5]

        result = perform_bootstrap_test(differences, n_bootstrap=100, random_state=42)

        # Verify structure
        assert "n_bootstrap" in result
        assert "bootstrap_mean" in result
        assert "bootstrap_std" in result
        assert "ci_95_lower" in result
        assert "ci_95_upper" in result
        assert "bootstrap_p_value" in result
        assert "observed_mean" in result

        # Verify values are reasonable
        assert result["n_bootstrap"] == 100
        assert result["observed_mean"] == pytest.approx(0.3, rel=0.01)
        assert result["ci_95_lower"] < result["ci_95_upper"]
        assert 0 <= result["bootstrap_p_value"] <= 1

    def test_perform_bootstrap_test_empty_list(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="Differences list cannot be empty"):
            perform_bootstrap_test([])

    def test_perform_bootstrap_test_reproducibility(self):
        """Test that same seed produces same results."""
        differences = [0.1, 0.2, 0.3, 0.4, 0.5]

        result1 = perform_bootstrap_test(differences, n_bootstrap=1000, random_state=42)
        result2 = perform_bootstrap_test(differences, n_bootstrap=1000, random_state=42)

        # Results should be identical with same seed
        assert result1["bootstrap_mean"] == result2["bootstrap_mean"]
        assert result1["ci_95_lower"] == result2["ci_95_lower"]
        assert result1["bootstrap_p_value"] == result2["bootstrap_p_value"]

    def test_perform_bootstrap_test_different_seeds(self):
        """Test that different seeds produce different results."""
        differences = [0.1, 0.2, 0.3, 0.4, 0.5]

        result1 = perform_bootstrap_test(differences, n_bootstrap=1000, random_state=42)
        result2 = perform_bootstrap_test(differences, n_bootstrap=1000, random_state=123)

        # Results should be different (with high probability)
        assert result1["bootstrap_mean"] != result2["bootstrap_mean"]

    def test_perform_bootstrap_test_large_sample(self):
        """Test bootstrap with larger sample size."""
        np.random.seed(42)
        differences = np.random.normal(loc=0.5, scale=0.2, size=100).tolist()

        result = perform_bootstrap_test(differences, n_bootstrap=1000, random_state=42)

        assert result["observed_mean"] > 0  # Should be positive
        assert result["ci_95_lower"] > 0  # CI should exclude 0 for this case

    def test_compute_paired_difference_stats_basic(self):
        """Test basic paired difference computation."""
        static_scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        dynamic_scores = [0.05, 0.15, 0.25, 0.35, 0.45]

        result = compute_paired_difference_stats(static_scores, dynamic_scores)

        # Verify structure
        assert "mean" in result
        assert "std" in result
        assert "median" in result
        assert "min" in result
        assert "max" in result
        assert "t_statistic" in result
        assert "p_value" in result
        assert "n_samples" in result
        assert "differences" in result

        # Verify differences are computed correctly (all should be 0.05)
        expected_diffs = [0.05] * 5
        assert result["differences"] == pytest.approx(expected_diffs)
        assert result["mean"] == pytest.approx(0.05)
        assert result["std"] == pytest.approx(0.0)  # All same value
        assert result["n_samples"] == 5

    def test_compute_paired_difference_stats_unequal_lengths(self):
        """Test that unequal lengths raise ValueError."""
        static_scores = [0.1, 0.2, 0.3]
        dynamic_scores = [0.05, 0.15]

        with pytest.raises(ValueError, match="Score lists must have equal length"):
            compute_paired_difference_stats(static_scores, dynamic_scores)

    def test_compute_paired_difference_stats_empty_lists(self):
        """Test that empty lists raise ValueError."""
        with pytest.raises(ValueError, match="Score lists cannot be empty"):
            compute_paired_difference_stats([], [])

    def test_compute_paired_difference_stats_negative_differences(self):
        """Test with negative differences (static < dynamic)."""
        static_scores = [0.1, 0.2, 0.3]
        dynamic_scores = [0.2, 0.3, 0.4]

        result = compute_paired_difference_stats(static_scores, dynamic_scores)

        # All differences should be -0.1
        assert result["mean"] == pytest.approx(-0.1)
        assert result["min"] == pytest.approx(-0.1)
        assert result["max"] == pytest.approx(-0.1)

    def test_compute_paired_difference_stats_with_ttest(self):
        """Test that t-statistic and p-value are computed."""
        static_scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        dynamic_scores = [0.15, 0.25, 0.35, 0.45, 0.55]

        result = compute_paired_difference_stats(static_scores, dynamic_scores)

        # Should have valid t-statistic and p-value
        assert result["t_statistic"] != 0
        assert 0 <= result["p_value"] <= 1

    @patch('src.stats_analysis.run_benchmark')
    def test_run_statistical_analysis_mocked(self, mock_run_benchmark):
        """Test run_statistical_analysis with mocked benchmark."""
        # Mock benchmark to return fixed values
        mock_run_benchmark.side_effect = [
            {'static_fid': 0.1, 'dynamic_fid': 0.05},
            {'static_fid': 0.12, 'dynamic_fid': 0.07},
            {'static_fid': 0.11, 'dynamic_fid': 0.06},
            {'static_fid': 0.13, 'dynamic_fid': 0.08},
            {'static_fid': 0.14, 'dynamic_fid': 0.09},
        ]

        with patch('src.stats_analysis.get_results_path', return_value='/tmp/test_results'):
            with patch('src.stats_analysis.ensure_directories_exist'):
                with patch('builtins.open'):
                    results = run_statistical_analysis(
                        n_seeds=3,
                        seeds=[42, 123, 456]
                    )

        # Verify structure
        assert "analysis_config" in results
        assert "paired_difference" in results
        assert "bootstrap_results" in results
        assert "individual_results" in results
        assert "statistical_significance" in results

        # Verify we got results for 3 seeds
        assert len(results["individual_results"]) == 3
        assert results["analysis_config"]["n_seeds"] == 3

    @patch('src.stats_analysis.run_benchmark')
    def test_run_statistical_analysis_with_error(self, mock_run_benchmark):
        """Test that errors in benchmark are properly propagated."""
        # First call succeeds, second fails
        mock_run_benchmark.side_effect = [
            {'static_fid': 0.1, 'dynamic_fid': 0.05},
            RuntimeError("Benchmark failed"),
        ]

        with patch('src.stats_analysis.get_results_path', return_value='/tmp/test_results'):
            with patch('src.stats_analysis.ensure_directories_exist'):
                with pytest.raises(RuntimeError, match="Benchmark failed"):
                    run_statistical_analysis(
                        n_seeds=2,
                        seeds=[42, 123]
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])