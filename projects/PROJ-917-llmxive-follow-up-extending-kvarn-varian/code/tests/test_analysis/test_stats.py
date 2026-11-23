"""
Unit tests for statistical analysis utilities.
"""
import pytest
import numpy as np
from analysis.stats import (
    compute_theoretical_lower_bound,
    perform_paired_t_test,
    run_epsilon_sensitivity_analysis
)

class TestTheoreticalLowerBound:
    def test_proportional_squared_model(self):
        """Test the proportional squared noise model."""
        delta = 0.1
        expected = (delta ** 2) / 12.0
        result = compute_theoretical_lower_bound(delta, "proportional_squared")
        assert np.isclose(result, expected)

    def test_invalid_noise_model(self):
        """Test that an invalid noise model raises ValueError."""
        with pytest.raises(ValueError, match="Unknown noise model"):
            compute_theoretical_lower_bound(0.1, "invalid_model")

class TestPairedTTest:
    def test_basic_t_test(self):
        """Test a basic paired t-test."""
        sample_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        sample_b = [1.1, 2.1, 3.1, 4.1, 5.1]
        
        result = perform_paired_t_test(sample_a, sample_b)
        
        assert 't_statistic' in result
        assert 'p_value' in result
        assert 'mean_diff' in result
        assert result['mean_diff'] == pytest.approx(-0.1, rel=1e-5)
        assert result['n'] == 5

    def test_equal_samples(self):
        """Test t-test with identical samples (should have t=0)."""
        sample = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = perform_paired_t_test(sample, sample)
        
        assert np.isclose(result['t_statistic'], 0.0)
        assert np.isclose(result['p_value'], 1.0)

    def test_mismatched_lengths(self):
        """Test that mismatched sample lengths raise ValueError."""
        sample_a = [1.0, 2.0, 3.0]
        sample_b = [1.0, 2.0]
        
        with pytest.raises(ValueError, match="Samples must have the same length"):
            perform_paired_t_test(sample_a, sample_b)

    def test_small_sample_size(self):
        """Test that sample size < 2 raises ValueError."""
        sample_a = [1.0]
        sample_b = [1.0]
        
        with pytest.raises(ValueError, match="Samples must have at least 2 elements"):
            perform_paired_t_test(sample_a, sample_b)

class TestEpsilonSensitivityAnalysis:
    def test_analysis_structure(self):
        """Test that the sensitivity analysis returns the expected structure."""
        # Mock simulation results
        mock_results = [
            {'accumulated_kl': 0.5},
            {'accumulated_kl': 0.6},
            {'accumulated_kl': 0.55}
        ]
        
        result = run_epsilon_sensitivity_analysis(
            mock_results,
            epsilon_start=1e-8,
            epsilon_end=1e-2,
            epsilon_steps=5
        )
        
        assert 'epsilon_values' in result
        assert 'mean_kl_per_epsilon' in result
        assert 'std_kl_per_epsilon' in result
        assert 'min_kl' in result
        assert 'optimal_epsilon' in result
        assert 'num_simulation_runs' in result
        
        assert len(result['epsilon_values']) == 5
        assert len(result['mean_kl_per_epsilon']) == 5
        assert len(result['std_kl_per_epsilon']) == 5

    def test_empty_simulation_results(self):
        """Test that empty simulation results raise ValueError."""
        with pytest.raises(ValueError, match="No valid accumulated_kl values"):
            run_epsilon_sensitivity_analysis([])