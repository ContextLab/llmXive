"""
Unit tests for sensitivity analysis module (T025).

Tests the parametric bootstrap implementation and stability proportion calculations
for the sensitivity analysis task.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from diagnostics.sensitivity_analysis import (
    calculate_metrics_at_cutoff,
    run_parametric_bootstrap,
    run_sensitivity_analysis
)
from utils.config import set_seed


class TestCalculateMetricsAtCutoff:
    """Tests for calculate_metrics_at_cutoff function."""

    def test_stability_proportion_calculation(self):
        """Test that stability proportion is calculated correctly."""
        p_values = np.array([0.01, 0.03, 0.07, 0.15, 0.25])
        cutoff = 0.05

        result = calculate_metrics_at_cutoff(p_values, cutoff)

        assert result['cutoff'] == cutoff
        assert result['significant_count'] == 2  # 0.01 and 0.03
        assert result['total_count'] == 5
        assert result['stability_proportion'] == 0.4  # 2/5

    def test_all_significant(self):
        """Test when all p-values are significant."""
        p_values = np.array([0.001, 0.01, 0.02, 0.04])
        cutoff = 0.05

        result = calculate_metrics_at_cutoff(p_values, cutoff)

        assert result['stability_proportion'] == 1.0

    def test_none_significant(self):
        """Test when no p-values are significant."""
        p_values = np.array([0.1, 0.2, 0.3, 0.5])
        cutoff = 0.05

        result = calculate_metrics_at_cutoff(p_values, cutoff)

        assert result['stability_proportion'] == 0.0

    def test_empty_array(self):
        """Test with empty p-values array."""
        p_values = np.array([])
        cutoff = 0.05

        result = calculate_metrics_at_cutoff(p_values, cutoff)

        assert result['stability_proportion'] == 0.0
        assert result['total_count'] == 0

    def test_is_significant_at_05(self):
        """Test the is_significant_at_05 flag."""
        p_values_significant = np.array([0.01, 0.02, 0.03, 0.04, 0.06])  # 4/5 > 0.5
        p_values_not_significant = np.array([0.01, 0.02, 0.06, 0.07, 0.08])  # 2/5 < 0.5

        result_sig = calculate_metrics_at_cutoff(p_values_significant, 0.05)
        result_not_sig = calculate_metrics_at_cutoff(p_values_not_significant, 0.05)

        assert result_sig['is_significant_at_05'] is True
        assert result_not_sig['is_significant_at_05'] is False


class TestRunParametricBootstrap:
    """Tests for run_parametric_bootstrap function."""

    def test_bootstrap_reproducibility(self):
        """Test that bootstrap results are reproducible with same seed."""
        # Create sample data
        np.random.seed(42)
        data = pd.DataFrame({
            'language': ['Python'] * 50 + ['JavaScript'] * 50 + ['Java'] * 50,
            'resolution_time_hours': np.concatenate([
                np.random.lognormal(3, 1, 50),
                np.random.lognormal(3.2, 1.1, 50),
                np.random.lognormal(3.1, 1.05, 50)
            ])
        })

        # Run bootstrap twice with same seed
        rng1 = np.random.default_rng(42)
        p_values1 = run_parametric_bootstrap(data, 'language', 'resolution_time_hours', 100, 42, rng1)

        rng2 = np.random.default_rng(42)
        p_values2 = run_parametric_bootstrap(data, 'language', 'resolution_time_hours', 100, 42, rng2)

        # Results should be identical
        assert len(p_values1) == len(p_values2)
        np.testing.assert_array_almost_equal(p_values1, p_values2)

    def test_bootstrap_returns_valid_p_values(self):
        """Test that bootstrap returns valid p-values in [0, 1]."""
        data = pd.DataFrame({
            'language': ['A'] * 30 + ['B'] * 30,
            'resolution_time_hours': np.concatenate([
                np.random.lognormal(2, 0.5, 30),
                np.random.lognormal(2.5, 0.6, 30)
            ])
        })

        rng = np.random.default_rng(42)
        p_values = run_parametric_bootstrap(data, 'language', 'resolution_time_hours', 50, 42, rng)

        # Check all values are valid probabilities
        assert np.all(p_values >= 0)
        assert np.all(p_values <= 1)
        assert len(p_values) > 0

    def test_bootstrap_with_different_resample_counts(self):
        """Test that bootstrap respects n_resamples parameter."""
        data = pd.DataFrame({
            'language': ['X'] * 20 + ['Y'] * 20,
            'resolution_time_hours': np.concatenate([
                np.random.lognormal(2, 0.5, 20),
                np.random.lognormal(2.3, 0.6, 20)
            ])
        })

        rng1 = np.random.default_rng(42)
        p_values_10 = run_parametric_bootstrap(data, 'language', 'resolution_time_hours', 10, 42, rng1)

        rng2 = np.random.default_rng(42)
        p_values_50 = run_parametric_bootstrap(data, 'language', 'resolution_time_hours', 50, 42, rng2)

        assert len(p_values_10) == 10
        assert len(p_values_50) == 50


class TestRunSensitivityAnalysis:
    """Tests for run_sensitivity_analysis function."""

    def test_default_cutoffs(self):
        """Test that default cutoffs are used when not specified."""
        data = pd.DataFrame({
            'language': ['A'] * 25 + ['B'] * 25,
            'resolution_time_hours': np.concatenate([
                np.random.lognormal(2, 0.5, 25),
                np.random.lognormal(2.3, 0.6, 25)
            ])
        })

        results = run_sensitivity_analysis(
            data=data,
            group_column='language',
            value_column='resolution_time_hours',
            n_resamples=10,
            seed=42
        )

        assert 'results_by_cutoff' in results
        assert '0.01' in results['results_by_cutoff']
        assert '0.05' in results['results_by_cutoff']
        assert '0.1' in results['results_by_cutoff']

    def test_custom_cutoffs(self):
        """Test that custom cutoffs are respected."""
        data = pd.DataFrame({
            'language': ['A'] * 20 + ['B'] * 20,
            'resolution_time_hours': np.concatenate([
                np.random.lognormal(2, 0.5, 20),
                np.random.lognormal(2.3, 0.6, 20)
            ])
        })

        custom_cutoffs = [0.001, 0.025, 0.15]
        results = run_sensitivity_analysis(
            data=data,
            group_column='language',
            value_column='resolution_time_hours',
            cutoffs=custom_cutoffs,
            n_resamples=10,
            seed=42
        )

        assert results['cutoffs_evaluated'] == custom_cutoffs
        for cutoff in custom_cutoffs:
            assert str(cutoff) in results['results_by_cutoff']

    def test_results_structure(self):
        """Test that results have expected structure."""
        data = pd.DataFrame({
            'language': ['A'] * 15 + ['B'] * 15,
            'resolution_time_hours': np.concatenate([
                np.random.lognormal(2, 0.5, 15),
                np.random.lognormal(2.3, 0.6, 15)
            ])
        })

        results = run_sensitivity_analysis(
            data=data,
            n_resamples=5,
            seed=42
        )

        # Check required fields
        assert results['analysis_type'] == 'parametric_bootstrap_sensitivity'
        assert 'overall_statistics' in results
        assert 'results_by_cutoff' in results
        assert 'interpretation' in results

        # Check overall statistics
        stats = results['overall_statistics']
        assert 'mean_p_value' in stats
        assert 'median_p_value' in stats
        assert 'std_p_value' in stats
        assert 'total_resamples' in stats

        # Check interpretation has language requirement
        assert results['interpretation']['language'] == 'associational'

    def test_stability_proportion_calculation(self):
        """Test that stability proportions are calculated correctly."""
        data = pd.DataFrame({
            'language': ['A'] * 30 + ['B'] * 30,
            'resolution_time_hours': np.concatenate([
                np.random.lognormal(2, 0.5, 30),
                np.random.lognormal(2.3, 0.6, 30)
            ])
        })

        results = run_sensitivity_analysis(
            data=data,
            n_resamples=20,
            seed=42
        )

        # Check that stability proportions are between 0 and 1
        for cutoff_str, metrics in results['results_by_cutoff'].items():
            assert 0.0 <= metrics['stability_proportion'] <= 1.0
            assert metrics['significant_count'] <= metrics['total_count']


class TestIntegration:
    """Integration tests for the full sensitivity analysis pipeline."""

    def test_end_to_end_with_realistic_data(self):
        """Test full pipeline with realistic multi-group data."""
        # Create realistic multi-language dataset
        np.random.seed(42)
        languages = ['Python', 'JavaScript', 'Java', 'C++', 'Go']
        data = []

        for i, lang in enumerate(languages):
            n_issues = np.random.randint(40, 60)
            # Different distributions for different languages
            resolution_times = np.random.lognormal(
                mean=3.0 + i * 0.1,
                sigma=0.8 + i * 0.05,
                size=n_issues
            )
            data.extend([{'language': lang, 'resolution_time_hours': t} for t in resolution_times])

        df = pd.DataFrame(data)

        # Run sensitivity analysis
        results = run_sensitivity_analysis(
            data=df,
            group_column='language',
            value_column='resolution_time_hours',
            n_resamples=20,
            seed=42
        )

        # Verify results
        assert len(results['results_by_cutoff']) == 3  # 3 default cutoffs
        assert results['overall_statistics']['total_resamples'] == 20

        # All stability proportions should be valid
        for cutoff_str, metrics in results['results_by_cutoff'].items():
            assert metrics['stability_proportion'] >= 0.0
            assert metrics['stability_proportion'] <= 1.0

    def test_seed_reproducibility_full_pipeline(self):
        """Test that full pipeline is reproducible with same seed."""
        data = pd.DataFrame({
            'language': ['A'] * 20 + ['B'] * 20,
            'resolution_time_hours': np.concatenate([
                np.random.lognormal(2, 0.5, 20),
                np.random.lognormal(2.3, 0.6, 20)
            ])
        })

        results1 = run_sensitivity_analysis(data=data, n_resamples=10, seed=123)
        results2 = run_sensitivity_analysis(data=data, n_resamples=10, seed=123)

        # Results should be identical
        assert results1['overall_statistics']['mean_p_value'] == results2['overall_statistics']['mean_p_value']
        for cutoff_str in results1['results_by_cutoff']:
            assert results1['results_by_cutoff'][cutoff_str]['stability_proportion'] == \
                   results2['results_by_cutoff'][cutoff_str]['stability_proportion']
