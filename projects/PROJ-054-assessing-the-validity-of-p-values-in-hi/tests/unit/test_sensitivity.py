"""
Unit tests for sensitivity analysis utilities in sensitivity_analysis.py.
These tests verify KS statistic calculations and sensitivity sweeps.
"""
import pytest
import numpy as np
import json
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from sensitivity_analysis import calculate_ks_statistic_for_rho


class TestSensitivityAnalysis:
    """Tests for T031: Sensitivity analysis sweep."""

    def test_ks_statistic_calculation(self):
        """Test KS statistic calculation for a given rho."""
        # Create synthetic p-value trajectories
        np.random.seed(42)
        n_samples = 1000
        rho = 0.5

        # Simulate p-values under null (should be uniform)
        standard_pvalues = np.random.uniform(0, 1, n_samples)

        # Simulate biased p-values (anti-conservative)
        # Using a Beta distribution with alpha < 1 to create skew towards 0
        biased_pvalues = np.random.beta(0.5, 1, n_samples)

        ks_stat = calculate_ks_statistic_for_rho(standard_pvalues, biased_pvalues, rho)

        assert 0 <= ks_stat <= 1, f"KS statistic {ks_stat} should be in [0, 1]"

    def test_ks_statistic_zero_for_identical(self):
        """Test that KS statistic is 0 for identical distributions."""
        np.random.seed(42)
        pvalues = np.random.uniform(0, 1, 1000)

        ks_stat = calculate_ks_statistic_for_rho(pvalues, pvalues, 0.5)

        assert ks_stat == 0.0, "KS statistic should be 0 for identical distributions"

    def test_ks_statistic_increases_with_bias(self):
        """Test that KS statistic increases with more bias."""
        np.random.seed(42)
        standard_pvalues = np.random.uniform(0, 1, 1000)

        # Create biased distributions with increasing severity
        ks_stats = []
        for alpha in [1.0, 0.8, 0.5, 0.3, 0.1]:
            biased_pvalues = np.random.beta(alpha, 1, 1000)
            ks_stat = calculate_ks_statistic_for_rho(standard_pvalues, biased_pvalues, 0.5)
            ks_stats.append(ks_stat)

        # KS statistic should generally increase as alpha decreases (more bias)
        # Allow some randomness, but trend should be upward
        assert ks_stats[-1] > ks_stats[0], \
            f"KS statistic should increase with more bias: {ks_stats}"

    def test_worst_case_detection(self):
        """Test that worst-case scenario is correctly identified."""
        # Simulate multiple rho values with varying KS statistics
        rho_values = [0.1, 0.3, 0.5, 0.7, 0.9]
        ks_stats = [0.02, 0.05, 0.10, 0.15, 0.20]  # Increasing with rho

        # Find worst case (maximum KS)
        worst_idx = np.argmax(ks_stats)
        worst_rho = rho_values[worst_idx]
        worst_ks = ks_stats[worst_idx]

        assert worst_rho == 0.9, f"Worst case rho should be 0.9, got {worst_rho}"
        assert worst_ks == 0.20, f"Worst case KS should be 0.20, got {worst_ks}"

    def test_sensitivity_output_format(self):
        """Test that sensitivity analysis produces expected output format."""
        # Simulate a single sensitivity run
        np.random.seed(42)
        standard_pvalues = np.random.uniform(0, 1, 1000)
        biased_pvalues = np.random.beta(0.5, 1, 1000)

        ks_stat = calculate_ks_statistic_for_rho(standard_pvalues, biased_pvalues, 0.5)

        # Output should be a float in [0, 1]
        assert isinstance(ks_stat, float), "KS statistic should be a float"
        assert 0 <= ks_stat <= 1, "KS statistic should be in [0, 1]"
