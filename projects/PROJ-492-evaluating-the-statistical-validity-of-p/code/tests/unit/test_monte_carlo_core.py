"""
Unit tests for Monte-Carlo framework core functions.
"""

import pytest
import numpy as np
from pathlib import Path

# Ensure we can import from the code directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.monte_carlo_core import (
    set_seeds,
    generate_null_binary_data,
    generate_null_continuous_data,
    simulate_z_test_statistic,
    simulate_fisher_exact_table,
    simulate_welch_t_statistic,
    simulate_binomial_statistic,
    compute_empirical_p_value,
    run_monte_carlo_validation_core
)


class TestMonteCarloCore:
    """Test suite for Monte-Carlo core functions."""

    def test_set_seeds(self):
        """Test that set_seeds properly initializes random state."""
        set_seeds(42)
        val1 = np.random.random()
        set_seeds(42)
        val2 = np.random.random()
        assert val1 == val2, "Seeding should produce reproducible results"

    def test_generate_null_binary_data(self):
        """Test binary data generation under null hypothesis."""
        control, treatment = generate_null_binary_data(100, 100, 0.5)
        
        assert len(control) == 100, "Control group size mismatch"
        assert len(treatment) == 100, "Treatment group size mismatch"
        assert np.all(np.isin(control, [0, 1])), "Binary outcomes should be 0 or 1"
        assert np.all(np.isin(treatment, [0, 1])), "Binary outcomes should be 0 or 1"

    def test_generate_null_continuous_data(self):
        """Test continuous data generation under null hypothesis."""
        control, treatment = generate_null_continuous_data(100, 100, 0.0, 1.0)
        
        assert len(control) == 100, "Control group size mismatch"
        assert len(treatment) == 100, "Treatment group size mismatch"
        assert control.dtype in [np.float64, np.float32], "Continuous data should be float"
        assert treatment.dtype in [np.float64, np.float32], "Continuous data should be float"

    def test_simulate_z_test_statistic(self):
        """Test z-test statistic simulation."""
        z_stats = simulate_z_test_statistic(100, 100, 0.5, 100)
        
        assert len(z_stats) == 100, "Should have 100 simulated statistics"
        assert all(isinstance(s, float) for s in z_stats), "Statistics should be floats"

    def test_simulate_fisher_exact_table(self):
        """Test Fisher's exact test table simulation."""
        tables = simulate_fisher_exact_table(100, 100, 0.5, 10)
        
        assert len(tables) == 10, "Should have 10 simulated tables"
        assert all(t.shape == (2, 2) for t in tables), "All tables should be 2x2"

    def test_simulate_welch_t_statistic(self):
        """Test Welch's t-test statistic simulation."""
        t_stats = simulate_welch_t_statistic(100, 100, 0.0, 1.0, 100)
        
        assert len(t_stats) == 100, "Should have 100 simulated statistics"
        assert all(isinstance(s, float) for s in t_stats), "Statistics should be floats"

    def test_simulate_binomial_statistic(self):
        """Test binomial statistic simulation."""
        counts = simulate_binomial_statistic(100, 0.5, 100)
        
        assert len(counts) == 100, "Should have 100 simulated counts"
        assert all(isinstance(c, int) for c in counts), "Counts should be integers"
        assert all(0 <= c <= 100 for c in counts), "Counts should be within [0, n]"

    def test_compute_empirical_p_value_two_tailed(self):
        """Test empirical p-value computation (two-tailed)."""
        simulated = [0.1, 0.2, 0.3, 0.4, 0.5, -0.1, -0.2, -0.3, -0.4, -0.5]
        observed = 0.45
        
        p_value = compute_empirical_p_value(simulated, observed, two_tailed=True)
        
        # Values >= 0.45 in absolute: 0.5, -0.5 -> 2 values
        # p-value = (2 + 1) / (10 + 1) = 3/11
        expected = 3 / 11
        assert abs(p_value - expected) < 1e-10, f"Expected {expected}, got {p_value}"

    def test_compute_empirical_p_value_one_tailed(self):
        """Test empirical p-value computation (one-tailed)."""
        simulated = [0.1, 0.2, 0.3, 0.4, 0.5, -0.1, -0.2, -0.3, -0.4, -0.5]
        observed = 0.45
        
        p_value = compute_empirical_p_value(simulated, observed, two_tailed=False)
        
        # Values >= 0.45: 0.5 -> 1 value
        # p-value = (1 + 1) / (10 + 1) = 2/11
        expected = 2 / 11
        assert abs(p_value - expected) < 1e-10, f"Expected {expected}, got {p_value}"

    def test_run_monte_carlo_validation_core_z_test(self):
        """Test full Monte Carlo validation for z-test."""
        result = run_monte_carlo_validation_core(
            test_type='z_test',
            n_control=100,
            n_treatment=100,
            n_replicates=50,
            observed_stat=1.5,
            baseline_param=0.5
        )
        
        assert 'test_type' in result
        assert result['test_type'] == 'z_test'
        assert 'empirical_p_value' in result
        assert 'simulated_stats_summary' in result

    def test_run_monte_carlo_validation_core_welch_t(self):
        """Test full Monte Carlo validation for Welch's t-test."""
        result = run_monte_carlo_validation_core(
            test_type='welch_t',
            n_control=100,
            n_treatment=100,
            n_replicates=50,
            observed_stat=2.0,
            baseline_param=0.0
        )
        
        assert 'test_type' in result
        assert result['test_type'] == 'welch_t'
        assert 'empirical_p_value' in result

    def test_run_monte_carlo_validation_core_invalid_type(self):
        """Test that invalid test type raises error."""
        with pytest.raises(ValueError, match="Unknown test type"):
            run_monte_carlo_validation_core(
                test_type='invalid_type',
                n_control=100,
                n_treatment=100,
                n_replicates=50,
                observed_stat=1.0,
                baseline_param=0.5
            )

    def test_reproducibility(self):
        """Test that results are reproducible with same seed."""
        result1 = run_monte_carlo_validation_core(
            test_type='z_test',
            n_control=50,
            n_treatment=50,
            n_replicates=20,
            observed_stat=1.0,
            baseline_param=0.5
        )
        
        result2 = run_monte_carlo_validation_core(
            test_type='z_test',
            n_control=50,
            n_treatment=50,
            n_replicates=20,
            observed_stat=1.0,
            baseline_param=0.5
        )
        
        # Results should be identical due to fixed seed in function
        assert result1['empirical_p_value'] == result2['empirical_p_value']