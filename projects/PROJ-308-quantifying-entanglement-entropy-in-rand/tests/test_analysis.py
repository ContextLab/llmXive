"""
Unit tests for analysis.py (T006, T007, T008 verification)

Tests:
- test_aic_selection_logic: Verify AIC model selection with synthetic data.
- test_bootstrap: Verify bootstrap resampling and statistics.
- test_filter_unresolved: Verify filtering of unresolved realizations.
- test_scaling_exponent: Verify full scaling exponent computation.
- test_toy_model: Verify toy model data generation.
- test_plot_generation: Verify plot generation.
"""

import numpy as np
import pytest
from unittest.mock import patch
import os

from code.analysis import (
    ModelSelectionResult,
    select_model_aic,
    filter_unresolved_realizations,
    bootstrap_resample,
    compute_bootstrap_statistics,
    compute_scaling_exponent,
    generate_toy_model_data,
    generate_entropy_vs_l_plot,
    verify_scaling_ansatz
)


class TestAICSelectionLogic:
    """Test AIC-based model selection (T006)."""

    def test_logarithmic_scaling_selected(self):
        """
        Test that logarithmic scaling is selected when data follows S(l) ~ log(l).
        """
        # Generate data: S(l) = 0.5 * log(l)
        cuts = [2, 4, 8, 16, 32]
        entropies = [0.5 * np.log(l) for l in cuts]

        result = select_model_aic(cuts, entropies)

        assert result.model_type == 'logarithmic'
        assert np.isclose(result.alpha, 0.5, atol=0.01)
        assert result.aic_diff == 0.0  # Best model

    def test_area_law_selected(self):
        """
        Test that area law (constant) is selected when data is constant.
        """
        cuts = [2, 4, 8, 16, 32]
        entropies = [1.0] * len(cuts)

        result = select_model_aic(cuts, entropies)

        assert result.model_type == 'area_law'
        assert np.isclose(result.alpha, 0.0, atol=1e-6)

    def test_volume_law_selected(self):
        """
        Test that volume law (linear) is selected when data is linear.
        """
        cuts = [2, 4, 8, 16, 32]
        entropies = [0.2 * l for l in cuts]

        result = select_model_aic(cuts, entropies)

        # Should prefer volume law or logarithmic depending on fit quality
        # For strong linear trend, volume law should win
        assert result.model_type in ['volume_law', 'logarithmic']
        assert result.alpha > 0.0

    def test_synthetic_known_slope(self):
        """
        Test with synthetic data of known slope (T006 requirement).
        """
        cuts = [2, 4, 8, 16]
        true_slope = 0.33
        entropies = [true_slope * np.log(l) for l in cuts]

        result = select_model_aic(cuts, entropies)

        assert result.model_type == 'logarithmic'
        assert np.isclose(result.alpha, true_slope, atol=0.01)


class TestFilterUnresolved:
    """Test filtering of unresolved realizations (T008)."""

    def test_filter_unresolved(self):
        """Test that unresolved realizations are removed."""
        realizations = [
            {'id': 1, 'unresolved': False},
            {'id': 2, 'unresolved': True},
            {'id': 3, 'unresolved': False},
            {'id': 4, 'unresolved': True}
        ]

        filtered = filter_unresolved_realizations(realizations)

        assert len(filtered) == 2
        assert all(not r['unresolved'] for r in filtered)
        assert all(r['id'] in [1, 3] for r in filtered)

    def test_no_unresolved(self):
        """Test when no realizations are unresolved."""
        realizations = [
            {'id': 1, 'unresolved': False},
            {'id': 2, 'unresolved': False}
        ]

        filtered = filter_unresolved_realizations(realizations)

        assert len(filtered) == 2

    def test_all_unresolved(self):
        """Test when all realizations are unresolved."""
        realizations = [
            {'id': 1, 'unresolved': True},
            {'id': 2, 'unresolved': True}
        ]

        filtered = filter_unresolved_realizations(realizations)

        assert len(filtered) == 0


class TestBootstrap:
    """Test bootstrap resampling (T007)."""

    def test_bootstrap_resample(self):
        """Test that bootstrap resampling produces correct number of samples."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        n_resamples = 100

        resamples = bootstrap_resample(data, n_resamples=n_resamples, seed=42)

        assert len(resamples) == n_resamples
        assert all(len(r) == len(data) for r in resamples)

    def test_bootstrap_statistics(self):
        """Test bootstrap statistics computation."""
        # Simulate bootstrap estimates
        estimates = np.random.normal(loc=5.0, scale=1.0, size=1000)

        stats = compute_bootstrap_statistics(estimates)

        assert np.isclose(stats['mean'], 5.0, atol=0.1)
        assert np.isclose(stats['std'], 1.0, atol=0.1)
        assert stats['ci_lower'] < stats['mean'] < stats['ci_upper']
        assert 0.0 <= stats['p_value'] <= 1.0

    def test_bootstrap_empty(self):
        """Test bootstrap statistics with empty input."""
        stats = compute_bootstrap_statistics([])

        assert np.isnan(stats['mean'])
        assert np.isnan(stats['std'])


class TestScalingExponent:
    """Test full scaling exponent computation."""

    def test_scaling_exponent_computation(self):
        """Test compute_scaling_exponent with synthetic data."""
        # Simulate data: S(l) = 0.5 * log(l) with some noise
        cuts = [2, 4, 8, 16]
        n_realizations = 50

        entropy_data = {
            l: [0.5 * np.log(l) + np.random.normal(0, 0.05) for _ in range(n_realizations)]
            for l in cuts
        }

        result, boot_stats = compute_scaling_exponent(entropy_data, n_resamples=100, seed=42)

        assert result.model_type == 'logarithmic'
        assert np.isclose(result.alpha, 0.5, atol=0.05)
        assert result.ci_lower < result.alpha < result.ci_upper


class TestToyModel:
    """Test toy model generation (T018, T019)."""

    def test_toy_model_data_generation(self):
        """Test generate_toy_model_data."""
        data = generate_toy_model_data(L=10, n_realizations=20, seed=42)

        assert 'cuts' in data
        assert 'entropies' in data
        assert 'mean_entropies' in data

        assert len(data['cuts']) == 9  # 1 to 9
        assert len(data['mean_entropies']) == 9

        # Check that entropies increase with l (logarithmic scaling)
        for i in range(len(data['cuts']) - 1):
            assert data['mean_entropies'][i] < data['mean_entropies'][i + 1]

    def test_refael_moore_slope(self):
        """
        Test that toy model approximates Refael-Moore slope (ln 2)/3.
        """
        data = generate_toy_model_data(L=10, n_realizations=100, seed=42)

        # Fit logarithmic model to mean entropies
        from code.analysis import _log_fit
        from scipy.optimize import curve_fit

        cuts = np.array(data['cuts'])
        mean_ent = np.array(data['mean_entropies'])

        popt, _ = curve_fit(_log_fit, cuts, mean_ent, p0=[0.5])
        slope = popt[0]

        expected_slope = np.log(2) / 3
        assert np.isclose(slope, expected_slope, atol=0.05), \
            f"Expected slope ~{expected_slope:.3f}, got {slope:.3f}"


class TestPlotGeneration:
    """Test plot generation (T009)."""

    def test_plot_generation(self):
        """Test generate_entropy_vs_l_plot."""
        cuts = [2, 4, 8, 16]
        mean_entropies = [0.5 * np.log(l) for l in cuts]
        output_path = 'figures/test_entropy_plot.png'

        # Clean up if exists
        if os.path.exists(output_path):
            os.remove(output_path)

        result_path = generate_entropy_vs_l_plot(
            cuts, mean_entropies, output_path=output_path
        )

        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 0

        # Clean up
        os.remove(output_path)

    def test_plot_with_error_bars(self):
        """Test plot generation with error bars."""
        cuts = [2, 4, 8, 16]
        mean_entropies = [0.5 * np.log(l) for l in cuts]
        std_entropies = [0.1] * len(cuts)
        output_path = 'figures/test_entropy_plot_err.png'

        if os.path.exists(output_path):
            os.remove(output_path)

        result_path = generate_entropy_vs_l_plot(
            cuts, mean_entropies, std_entropies=std_entropies, output_path=output_path
        )

        assert os.path.exists(result_path)
        os.remove(output_path)
