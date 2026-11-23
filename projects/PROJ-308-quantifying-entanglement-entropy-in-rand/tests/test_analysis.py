"""
Tests for code/analysis.py
"""
import numpy as np
import pytest
import os
import sys
import json
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from analysis import (
    ModelSelectionResult,
    log_fit,
    linear_fit,
    constant_fit,
    compute_aic,
    select_model_aic,
    bootstrap_resample,
    compute_bootstrap_statistics,
    compute_scaling_exponent,
    filter_unresolved_realizations,
    log_amendment
)

class TestFilterUnresolved:
    """Tests for filter_unresolved_realizations function."""

    def test_filter_unresolved(self):
        """Test that unresolved realizations are correctly filtered out."""
        # Create mock data with mixed resolved/unresolved status
        data = [
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': False},
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': True, 'reason': 'convergence_fail'},
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': False},
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': True, 'reason': 'max_bond_exceeded'},
        ]

        filtered = filter_unresolved_realizations(data)

        # Should have 2 items left
        assert len(filtered) == 2
        # All remaining items should be resolved
        for item in filtered:
            assert not item.get('is_unresolved', False)

    def test_filter_with_reasons(self):
        """Test filtering with specific unresolved reasons."""
        data = [
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': False},
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': True, 'reason': 'convergence_fail'},
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': True, 'reason': 'other_reason'},
        ]

        # Filter only 'convergence_fail'
        filtered = filter_unresolved_realizations(data, unresolved_reasons=['convergence_fail'])

        # Should have 2 items: the resolved one and the one with 'other_reason'
        assert len(filtered) == 2
        # Check that the 'convergence_fail' one is gone
        reasons_in_filtered = [item.get('reason') for item in filtered if item.get('is_unresolved')]
        assert 'convergence_fail' not in reasons_in_filtered

    def test_empty_list(self):
        """Test filtering an empty list."""
        filtered = filter_unresolved_realizations([])
        assert len(filtered) == 0

    def test_all_resolved(self):
        """Test filtering when all are resolved."""
        data = [
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': False},
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': False},
        ]
        filtered = filter_unresolved_realizations(data)
        assert len(filtered) == 2

    def test_all_unresolved(self):
        """Test filtering when all are unresolved."""
        data = [
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': True},
            {'l_values': [1, 2, 3], 's_values': [0.1, 0.2, 0.3], 'is_unresolved': True},
        ]
        filtered = filter_unresolved_realizations(data)
        assert len(filtered) == 0

class TestAICSelection:
    """Tests for AIC-based model selection."""

    def test_aic_selection_logic(self):
        """Test AIC selection with synthetic data of known slope."""
        # Generate data that follows a logarithmic law
        l_vals = np.array([2, 4, 8, 16, 32])
        alpha_true = 0.5
        intercept_true = 0.1
        s_vals = alpha_true * np.log(l_vals) + intercept_true + np.random.normal(0, 0.01, size=len(l_vals))

        result = select_model_aic(l_vals, s_vals)

        # Should select logarithmic model
        assert result.model_type == 'logarithmic'
        # Alpha should be close to true value
        assert abs(result.alpha - alpha_true) < 0.1

    def test_area_law_selection(self):
        """Test selection of area law (constant) model."""
        l_vals = np.array([2, 4, 8, 16, 32])
        s_vals = np.ones_like(l_vals) * 0.5 + np.random.normal(0, 0.01, size=len(l_vals))

        result = select_model_aic(l_vals, s_vals)

        # Should select area_law (constant)
        assert result.model_type == 'area_law'

    def test_volume_law_selection(self):
        """Test selection of volume law (linear) model."""
        l_vals = np.array([2, 4, 8, 16, 32])
        slope_true = 0.05
        intercept_true = 0.1
        s_vals = slope_true * l_vals + intercept_true + np.random.normal(0, 0.01, size=len(l_vals))

        result = select_model_aic(l_vals, s_vals)

        # Should select volume_law (linear)
        assert result.model_type == 'volume_law'
        assert abs(result.alpha - slope_true) < 0.01

class TestBootstrap:
    """Tests for bootstrap resampling."""

    def test_bootstrap(self):
        """Test bootstrap resampling generates reasonable statistics."""
        l_vals = np.array([2, 4, 8, 16, 32])
        alpha_true = 0.5
        s_vals = alpha_true * np.log(l_vals) + 0.1

        alphas = bootstrap_resample(l_vals, s_vals, n_resamples=100, random_seed=42)

        # Should have 100 samples (or close, if some failed)
        assert len(alphas) > 0
        
        stats_dict = compute_bootstrap_statistics(alphas)
        
        # Mean should be close to true alpha
        assert abs(stats_dict['mean'] - alpha_true) < 0.1
        # CI should contain the true value
        assert stats_dict['ci_low'] < alpha_true < stats_dict['ci_high']

class TestAICCalculation:
    """Tests for AIC calculation."""

    def test_compute_aic(self):
        """Test AIC calculation with known residuals."""
        residuals = np.array([0.1, -0.1, 0.2, -0.2])
        n_params = 2
        n_obs = 4

        aic = compute_aic(residuals, n_params, n_obs)

        # Manual calculation:
        # RSS = 0.01 + 0.01 + 0.04 + 0.04 = 0.1
        # AIC = 4 * ln(0.1/4) + 2*2 = 4 * ln(0.025) + 4
        expected_rss = np.sum(residuals**2)
        expected_aic = n_obs * np.log(expected_rss / n_obs) + 2 * n_params

        assert abs(aic - expected_aic) < 1e-6

class TestLogAmendment:
    """Tests for logging the AIC amendment."""

    def test_log_amendment_creates_file(self, tmp_path):
        """Test that log_amendment creates the validation log file."""
        log_file = str(tmp_path / "validation_log.txt")
        log_amendment(log_file=log_file)

        assert os.path.exists(log_file)
        with open(log_file, 'r') as f:
            content = f.read()
        assert "AMENDMENT: AIC used per Plan.md" in content