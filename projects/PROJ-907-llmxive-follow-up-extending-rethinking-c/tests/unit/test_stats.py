import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os
from src.stats_analysis import (
    perform_bootstrap_test, 
    compute_paired_difference_stats,
    run_statistical_analysis
)

class TestBootstrapSignificance:
    """Unit tests for the non-parametric bootstrap implementation."""

    def test_bootstrap_test_with_known_data(self):
        """Test bootstrap with data where we know the mean is significantly non-zero."""
        # Create a list of differences that are clearly positive
        differences = [0.5, 0.6, 0.55, 0.48, 0.52]
        
        result = perform_bootstrap_test(differences, n_resamples=1000)
        
        # The p-value should be very low (close to 0) because the mean is 0.524
        # and 0 is far away from the distribution of means
        assert "p_value" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        assert "bootstrap_distribution" in result
        
        # The CI should not include 0
        assert result["ci_lower"] > 0 or result["ci_upper"] < 0
        # Since all values are positive, CI should be positive
        assert result["ci_lower"] > 0

    def test_bootstrap_test_with_zero_mean(self):
        """Test bootstrap with data centered around zero."""
        # Create a list of differences centered around 0
        differences = [-0.1, 0.1, -0.05, 0.05, 0.0]
        
        result = perform_bootstrap_test(differences, n_resamples=1000)
        
        # The p-value should be high (close to 1) because 0 is in the middle
        assert result["p_value"] > 0.1  # Likely not significant

    def test_bootstrap_distribution_type(self):
        """Verify the bootstrap distribution is a list of floats."""
        differences = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = perform_bootstrap_test(differences, n_resamples=100)
        
        assert isinstance(result["bootstrap_distribution"], list)
        assert all(isinstance(x, float) for x in result["bootstrap_distribution"])

    def test_empty_differences_raises_error(self):
        """Test that an empty list of differences raises an error."""
        with pytest.raises(ValueError):
            perform_bootstrap_test([])

    def test_compute_paired_difference_stats(self):
        """Test the paired difference calculation."""
        dynamic = [0.8, 0.9, 0.85]
        static = [0.82, 0.91, 0.84]
        
        result = compute_paired_difference_stats(dynamic, static)
        
        # Differences: [0.02, 0.01, -0.01] -> Mean: 0.00666...
        expected_mean = (0.02 + 0.01 - 0.01) / 3
        assert abs(result["mean"] - expected_mean) < 1e-6
        assert "std" in result
        assert "differences" in result

    def test_run_statistical_analysis_structure(self):
        """
        Test the structure of the output from run_statistical_analysis.
        Since running the full benchmark is expensive, we mock the subprocess call.
        """
        mock_fids = (
            [[0.8, 0.9], [0.81, 0.89]], # Dynamic, Static for seed 1
            [[0.79, 0.88], [0.8, 0.87]] # Dynamic, Static for seed 2
        )
        
        with patch('src.stats_analysis.run_benchmark_with_seed') as mock_run:
            # Mock return values for 2 seeds
            mock_run.side_effect = [
                ([0.8, 0.9], [0.81, 0.89]),
                ([0.79, 0.88], [0.8, 0.87])
            ]
            
            # We can't easily test the file writing in a unit test without mocking too much,
            # but we can test the logic up to the result dictionary creation if we refactor.
            # For now, we verify the function signature and that it doesn't crash with mocked inputs.
            # Note: run_statistical_analysis calls subprocess, so we need to mock that too if we want to run it.
            # But we already mocked run_benchmark_with_seed which is the heavy part.
            
            # Actually, run_statistical_analysis calls run_benchmark_with_seed which calls subprocess.
            # We mocked run_benchmark_with_seed, so the subprocess call is bypassed.
            try:
                # We need to mock the file writing too to avoid side effects in tests
                with patch('src.stats_analysis.Path.open', MagicMock()):
                    with patch('src.stats_analysis.Path.mkdir'):
                        result = run_statistical_analysis(n_seeds=2)
                        
                        # Check keys exist
                        assert "mean_difference" in result
                        assert "std_difference" in result
                        assert "p_value" in result
                        assert "bootstrap_results" in result
                        assert "statistical_limitations" in result
                        
                        # Check types
                        assert isinstance(result["mean_difference"], float)
                        assert isinstance(result["statistical_limitations"], str)
                        assert "N=5" in result["statistical_limitations"] or "N=2" in result["statistical_limitations"]
            except Exception as e:
                pytest.fail(f"run_statistical_analysis failed with mocked inputs: {e}")