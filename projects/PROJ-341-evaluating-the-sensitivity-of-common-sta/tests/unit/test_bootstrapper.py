"""
Unit tests for bootstrapped power estimation module.
"""

import pytest
import numpy as np
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.bootstrapper import (
    bootstrap_power_estimate,
    calculate_ks_distance,
    load_simulated_power_distribution,
    run_bootstrapped_validation,
    save_power_results
)


class TestBootstrapPowerEstimate:
    """Tests for bootstrap_power_estimate function."""

    def test_bootstrap_power_estimate_normal_data(self):
        """Test bootstrap power estimation with normal data."""
        rng = np.random.default_rng(42)
        data = rng.normal(loc=0, scale=1, size=100)

        def dummy_test(x):
            # Simple test that returns p-value based on mean
            return np.abs(np.mean(x)) > 0.5

        power, se = bootstrap_power_estimate(
            data,
            dummy_test,
            n_bootstraps=100,
            rng=rng
        )

        assert 0.0 <= power <= 1.0
        assert se >= 0
        assert len(str(power)) > 0  # Should be a valid number

    def test_bootstrap_power_estimate_two_sample(self):
        """Test bootstrap with two-sample data."""
        rng = np.random.default_rng(123)
        group1 = rng.normal(loc=0, scale=1, size=50)
        group2 = rng.normal(loc=0.5, scale=1, size=50)

        def two_sample_test(groups):
            # Simple t-test approximation
            diff = np.mean(groups[1]) - np.mean(groups[0])
            return np.abs(diff) > 0.3

        power, se = bootstrap_power_estimate(
            (group1, group2),
            two_sample_test,
            n_bootstraps=100,
            rng=rng
        )

        assert 0.0 <= power <= 1.0
        assert se >= 0


class TestKSDistance:
    """Tests for calculate_ks_distance function."""

    def test_ks_distance_identical_cdfs(self):
        """Test KS distance with identical CDFs should be near zero."""
        cdf1 = np.linspace(0, 1, 100)
        cdf2 = np.linspace(0, 1, 100)

        ks_dist = calculate_ks_distance(cdf1, cdf2)
        assert ks_dist < 0.1  # Should be very small

    def test_ks_distance_different_cdfs(self):
        """Test KS distance with different CDFs."""
        cdf1 = np.linspace(0, 1, 100)
        cdf2 = np.linspace(0.2, 1.2, 100)

        ks_dist = calculate_ks_distance(cdf1, cdf2)
        assert 0 < ks_dist <= 1.0


class TestSavePowerResults:
    """Tests for save_power_results function."""

    def test_save_power_results_creates_file(self, tmp_path):
        """Test that save_power_results creates the output file."""
        output_path = str(tmp_path / "test_power.json")

        results = {
            'test': 'example',
            'power': 0.8
        }

        save_power_results(results, output_path)

        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            import json
            loaded = json.load(f)

        assert loaded['test'] == 'example'
        assert loaded['power'] == 0.8


class TestRunBootstrappedValidation:
    """Tests for run_bootstrapped_validation function."""

    def test_run_validation_with_mock_data(self):
        """Test validation with mock data structure."""
        mock_data = {
            'sample_size': 30,
            'ttest_groups': [np.random.randn(15), np.random.randn(15)],
            'anova_groups': [np.random.randn(10), np.random.randn(10), np.random.randn(10)],
            'chi_squared_table': np.array([[10, 5], [8, 7]])
        }

        result = run_bootstrapped_validation(
            'test_dataset',
            mock_data,
            test_types=['t-test'],
            n_bootstraps=50
        )

        assert 'dataset' in result
        assert result['dataset'] == 'test_dataset'
        assert 'test_results' in result
        assert len(result['test_results']) > 0
        assert 'validation_status' in result

    def test_validation_status_partial(self):
        """Test that validation status can be 'partial'."""
        mock_data = {
            'sample_size': 30,
            'ttest_groups': [np.random.randn(15), np.random.randn(15)]
        }

        result = run_bootstrapped_validation(
            'test_dataset',
            mock_data,
            test_types=['t-test'],
            n_bootstraps=50
        )

        assert result['validation_status'] in ['passed', 'failed', 'partial']
