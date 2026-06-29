"""
Integration test for sensitivity analysis (T027).

Tests the threshold sensitivity sweep functionality as specified in FR-005.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json

import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.sensitivity import run_threshold_sweep, compute_sensitivity_metrics, generate_sensitivity_report


class TestThresholdSensitivity:
    """Test suite for threshold sensitivity analysis."""

    @pytest.fixture
    def sample_data(self):
        """Create sample preprocessed data for testing."""
        np.random.seed(42)
        n_samples = 100

        data = pd.DataFrame({
            'choice': np.random.choice([0, 1], size=n_samples),
            'salience_score': np.random.uniform(0, 1, size=n_samples),
            'lives_lost': np.random.randint(0, 10, size=n_samples)
        })
        return data

    @pytest.fixture
    def threshold_range(self):
        """Return a small threshold range for quick testing."""
        return (0.3, 0.7, 5)

    def test_threshold_sweep_runs(self, sample_data, threshold_range):
        """Test that threshold sweep completes without errors."""
        results = run_threshold_sweep(
            data=sample_data,
            threshold_range=threshold_range,
            salience_weight=0.5,
            drift_rate=0.0,
            seed=42
        )

        assert 'thresholds' in results
        assert 'log_likelihoods' in results
        assert 'aic_values' in results
        assert 'best_threshold' in results
        assert 'min_aic' in results

        assert len(results['thresholds']) == threshold_range[2]
        assert len(results['log_likelihoods']) == threshold_range[2]
        assert len(results['aic_values']) == threshold_range[2]

    def test_threshold_sweep_returns_valid_ranges(self, sample_data, threshold_range):
        """Test that thresholds are within the specified range."""
        results = run_threshold_sweep(
            data=sample_data,
            threshold_range=threshold_range,
            salience_weight=0.5,
            drift_rate=0.0,
            seed=42
        )

        thresholds = np.array(results['thresholds'])
        assert np.all(thresholds >= threshold_range[0])
        assert np.all(thresholds <= threshold_range[1])

    def test_aic_computation(self, sample_data, threshold_range):
        """Test that AIC values are computed correctly."""
        results = run_threshold_sweep(
            data=sample_data,
            threshold_range=threshold_range,
            salience_weight=0.5,
            drift_rate=0.0,
            seed=42
        )

        aic_values = np.array(results['aic_values'])
        assert np.all(np.isfinite(aic_values))
        assert len(aic_values) > 0

    def test_compute_sensitivity_metrics(self, sample_data, threshold_range):
        """Test sensitivity metrics computation."""
        results = run_threshold_sweep(
            data=sample_data,
            threshold_range=threshold_range,
            salience_weight=0.5,
            drift_rate=0.0,
            seed=42
        )

        metrics = compute_sensitivity_metrics(results)

        assert 'aic_range' in metrics
        assert 'mean_sensitivity' in metrics
        assert 'max_sensitivity' in metrics
        assert 'optimal_threshold' in metrics
        assert 'optimal_aic' in metrics

        assert metrics['aic_range'] >= 0
        assert metrics['mean_sensitivity'] >= 0
        assert metrics['max_sensitivity'] >= 0

    def test_threshold_sweep_reproducibility(self, sample_data, threshold_range):
        """Test that results are reproducible with same seed."""
        results1 = run_threshold_sweep(
            data=sample_data,
            threshold_range=threshold_range,
            salience_weight=0.5,
            drift_rate=0.0,
            seed=123
        )

        results2 = run_threshold_sweep(
            data=sample_data,
            threshold_range=threshold_range,
            salience_weight=0.5,
            drift_rate=0.0,
            seed=123
        )

        assert np.allclose(results1['log_likelihoods'], results2['log_likelihoods'])
        assert np.allclose(results1['aic_values'], results2['aic_values'])
        assert results1['best_threshold'] == results2['best_threshold']

    def test_generate_sensitivity_report(self, sample_data, threshold_range, tmp_path):
        """Test report generation."""
        results = run_threshold_sweep(
            data=sample_data,
            threshold_range=threshold_range,
            salience_weight=0.5,
            drift_rate=0.0,
            seed=42
        )

        metrics = compute_sensitivity_metrics(results)
        output_path = tmp_path / 'test_report.json'

        generate_sensitivity_report(results, metrics, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            report = json.load(f)

        assert report['analysis_type'] == 'threshold_sensitivity'
        assert 'results' in report
        assert 'metrics' in report
        assert 'interpretation' in report

    def test_low_probability_range(self):
        """Test with low probability threshold range as per FR-005."""
        np.random.seed(42)
        sample_data = pd.DataFrame({
            'choice': np.random.choice([0, 1], size=50),
            'salience_score': np.random.uniform(0, 1, size=50)
        })

        # Low probability range: 0.05 to 0.3
        threshold_range = (0.05, 0.3, 6)

        results = run_threshold_sweep(
            data=sample_data,
            threshold_range=threshold_range,
            salience_weight=0.5,
            drift_rate=0.0,
            seed=42
        )

        # Verify all thresholds are in low probability range
        thresholds = np.array(results['thresholds'])
        assert np.all(thresholds >= 0.05)
        assert np.all(thresholds <= 0.3)

        metrics = compute_sensitivity_metrics(results)
        assert metrics['optimal_threshold'] >= 0.05
        assert metrics['optimal_threshold'] <= 0.3

    def test_empty_data_handling(self):
        """Test behavior with empty data (should raise or handle gracefully)."""
        empty_data = pd.DataFrame(columns=['choice', 'salience_score'])

        with pytest.raises((ValueError, IndexError)):
            run_threshold_sweep(
                data=empty_data,
                threshold_range=(0.3, 0.7, 5),
                salience_weight=0.5,
                drift_rate=0.0,
                seed=42
            )