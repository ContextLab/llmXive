"""
Integration tests for bootstrap significance testing functionality.

Tests the paired bootstrap test for comparing coverage deviations
between forecasting models.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import the module under test
from evaluation.bootstrap_test import (
    paired_bootstrap_test,
    compare_models_coverage,
    run_all_pairwise_comparisons,
    aggregate_bootstrap_results
)
from utils.exceptions import DataValidationError, CalibrationError


class TestPairedBootstrapTest:
    """Tests for the paired_bootstrap_test function."""

    def test_identical_distributions_high_pvalue(self):
        """When two models have identical deviations, p-value should be high."""
        np.random.seed(42)
        n_series = 50
        dev = np.random.normal(0.02, 0.05, n_series)

        result = paired_bootstrap_test(dev, dev, n_resamples=500, random_seed=42)

        assert result['p_value'] > 0.10  # Should not reject null
        assert result['observed_diff'] == pytest.approx(0.0, abs=1e-10)
        assert not result['significant']

    def test_different_distributions_low_pvalue(self):
        """When models differ significantly, p-value should be low."""
        np.random.seed(42)
        n_series = 100
        dev_a = np.random.normal(0.05, 0.03, n_series)
        dev_b = np.random.normal(-0.05, 0.03, n_series)

        result = paired_bootstrap_test(dev_a, dev_b, n_resamples=1000, random_seed=42)

        assert result['p_value'] < 0.05  # Should reject null
        assert result['significant']
        assert result['observed_diff'] > 0

    def test_empty_array_raises_error(self):
        """Empty arrays should raise DataValidationError."""
        with pytest.raises(DataValidationError):
            paired_bootstrap_test([], [], n_resamples=100)

    def test_mismatched_lengths_raises_error(self):
        """Arrays of different lengths should raise DataValidationError."""
        with pytest.raises(DataValidationError):
            paired_bootstrap_test([1, 2, 3], [1, 2], n_resamples=100)

    def test_confidence_interval_bounds(self):
        """Confidence interval should contain observed diff when p-value is high."""
        np.random.seed(123)
        n_series = 50
        dev = np.random.normal(0.01, 0.02, n_series)

        result = paired_bootstrap_test(dev, dev, n_resamples=1000, alpha=0.10, random_seed=123)

        lower, upper = result['confidence_interval']
        # With identical distributions, CI should include 0
        assert lower <= 0 <= upper


class TestCompareModelsCoverage:
    """Tests for compare_models_coverage function."""

    @pytest.fixture
    def sample_results_df(self):
        """Create a sample results DataFrame."""
        np.random.seed(42)
        n_series = 30

        data = []
        for i in range(n_series):
            data.append({
                'model': 'ARIMA',
                'confidence_level': 0.80,
                'coverage_deviation': np.random.normal(0.02, 0.05)
            })
            data.append({
                'model': 'Prophet',
                'confidence_level': 0.80,
                'coverage_deviation': np.random.normal(-0.01, 0.05)
            })
            data.append({
                'model': 'ARIMA',
                'confidence_level': 0.95,
                'coverage_deviation': np.random.normal(0.03, 0.04)
            })
            data.append({
                'model': 'Prophet',
                'confidence_level': 0.95,
                'coverage_deviation': np.random.normal(0.01, 0.04)
            })

        return pd.DataFrame(data)

    def test_basic_comparison(self, sample_results_df):
        """Test basic model comparison functionality."""
        result = compare_models_coverage(
            sample_results_df,
            'ARIMA',
            'Prophet',
            confidence_level=0.80,
            n_resamples=500,
            random_seed=42
        )

        assert 'p_value' in result
        assert 'observed_diff' in result
        assert 'significant' in result
        assert result['model_a'] == 'ARIMA'
        assert result['model_b'] == 'Prophet'
        assert result['confidence_level'] == 0.80

    def test_missing_columns_raises_error(self):
        """Missing required columns should raise DataValidationError."""
        df = pd.DataFrame({'model': ['A'], 'other': [0.1]})
        with pytest.raises(DataValidationError):
            compare_models_coverage(df, 'A', 'B', 0.80, n_resamples=100)

    def test_missing_confidence_level_raises_error(self):
        """Non-existent confidence level should raise DataValidationError."""
        df = pd.DataFrame({
            'model': ['A', 'B'],
            'confidence_level': [0.90, 0.90],
            'coverage_deviation': [0.01, 0.02]
        })
        with pytest.raises(DataValidationError):
            compare_models_coverage(df, 'A', 'B', 0.80, n_resamples=100)


class TestRunAllPairwiseComparisons:
    """Tests for run_all_pairwise_comparisons function."""

    @pytest.fixture
    def multi_model_df(self):
        """Create a DataFrame with multiple models and confidence levels."""
        np.random.seed(99)
        models = ['ARIMA', 'Prophet', 'LSTM']
        conf_levels = [0.80, 0.95]
        n_series = 20

        data = []
        for model in models:
            for cl in conf_levels:
                for _ in range(n_series):
                    data.append({
                        'model': model,
                        'confidence_level': cl,
                        'coverage_deviation': np.random.normal(0.02, 0.05)
                    })

        return pd.DataFrame(data)

    def test_all_pairs_computed(self, multi_model_df):
        """All model pairs should be tested."""
        result = run_all_pairwise_comparisons(
            multi_model_df,
            models=['ARIMA', 'Prophet', 'LSTM'],
            confidence_levels=[0.80, 0.95],
            n_resamples=200,
            random_seed=42
        )

        assert len(result) == 3 * 2  # 3 pairs (ARIMA-Prophet, ARIMA-LSTM, Prophet-LSTM) * 2 confidence levels

        # Check all expected pairs are present
        pairs = set(zip(result['model_a'], result['model_b']))
        expected_pairs = {
            ('ARIMA', 'Prophet'),
            ('ARIMA', 'LSTM'),
            ('Prophet', 'LSTM')
        }
        assert pairs == expected_pairs

    def test_empty_result_on_no_data(self):
        """Empty DataFrame returned when no valid comparisons possible."""
        df = pd.DataFrame({
            'model': ['A'],
            'confidence_level': [0.80],
            'coverage_deviation': [0.01]
        })
        result = run_all_pairwise_comparisons(
            df,
            models=['A', 'B'],
            confidence_levels=[0.80],
            n_resamples=100
        )
        assert result.empty


class TestAggregateBootstrapResults:
    """Tests for aggregate_bootstrap_results function."""

    @pytest.fixture
    def temp_output_path(self, tmp_path):
        """Create a temporary output path."""
        return str(tmp_path / "bootstrap_results.csv")

    def test_saves_to_csv(self, multi_model_df, temp_output_path):
        """Results should be saved to CSV file."""
        result = aggregate_bootstrap_results(
            multi_model_df,
            models=['ARIMA', 'Prophet'],
            confidence_levels=[0.80],
            output_path=temp_output_path,
            n_resamples=200,
            random_seed=42
        )

        # Check file exists
        assert Path(temp_output_path).exists()

        # Check DataFrame has content
        assert not result.empty
        assert 'p_value' in result.columns

    def test_empty_on_no_comparisons(self, temp_output_path):
        """Should handle case with no valid comparisons."""
        df = pd.DataFrame({
            'model': ['A'],
            'confidence_level': [0.80],
            'coverage_deviation': [0.01]
        })
        result = aggregate_bootstrap_results(
            df,
            models=['A', 'B'],
            confidence_levels=[0.80],
            output_path=temp_output_path,
            n_resamples=100
        )

        assert result.empty
        # File might not be created if no results
        # assert not Path(temp_output_path).exists()  # Optional