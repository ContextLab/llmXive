"""
Unit tests for correlation analysis module.

Tests Spearman coefficient computation and correlation analysis functions.
Implements T030 requirements for correlation analysis testing.
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from correlation_analysis import (
    compute_spearman_correlation,
    join_metrics_for_correlation,
    calculate_correlations,
    save_correlation_results,
    validate_correlation_results
)


class TestSpearmanCorrelation:
    """Tests for Spearman correlation computation."""

    def test_perfect_positive_correlation(self):
        """Test that perfectly correlated data yields correlation of 1.0."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])

        corr, p_value = compute_spearman_correlation(x, y)

        assert abs(corr - 1.0) < 1e-6, f"Expected correlation ~1.0, got {corr}"
        assert p_value < 0.05, "Expected significant p-value for perfect correlation"

    def test_perfect_negative_correlation(self):
        """Test that perfectly negatively correlated data yields correlation of -1.0."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])

        corr, p_value = compute_spearman_correlation(x, y)

        assert abs(corr - (-1.0)) < 1e-6, f"Expected correlation ~-1.0, got {corr}"
        assert p_value < 0.05, "Expected significant p-value for perfect negative correlation"

    def test_no_correlation(self):
        """Test that uncorrelated data yields correlation near 0."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)

        corr, p_value = compute_spearman_correlation(x, y)

        assert abs(corr) < 0.3, f"Expected correlation near 0, got {corr}"

    def test_nan_filtering(self):
        """Test that NaN values are properly filtered."""
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, np.nan, 10.0])

        corr, p_value = compute_spearman_correlation(x, y)

        # Should compute correlation on valid pairs only
        assert not np.isnan(corr), "Correlation should not be NaN after filtering"

    def test_infinite_filtering(self):
        """Test that infinite values are properly filtered."""
        x = np.array([1.0, 2.0, np.inf, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, np.inf])

        corr, p_value = compute_spearman_correlation(x, y)

        # Should compute correlation on valid pairs only
        assert not np.isnan(corr), "Correlation should not be NaN after filtering"

    def test_insufficient_data_points(self):
        """Test handling of insufficient data points."""
        x = np.array([1.0, np.nan])
        y = np.array([2.0, np.nan])

        corr, p_value = compute_spearman_correlation(x, y)

        # Should return default values for insufficient data
        assert corr == 0.0
        assert p_value == 1.0

    def test_mismatched_lengths(self):
        """Test that mismatched array lengths raise an error."""
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([1.0, 2.0])

        with pytest.raises(ValueError):
            compute_spearman_correlation(x, y)


class TestJoinMetrics:
    """Tests for metrics joining functionality."""

    def test_join_on_common_key(self):
        """Test joining dataframes on common key column."""
        clone_df = pd.DataFrame({
            'file_id': [1, 2, 3],
            'clone_density': [0.1, 0.2, 0.3]
        })

        perplexity_df = pd.DataFrame({
            'file_id': [1, 2, 3],
            'perplexity': [10.0, 20.0, 30.0]
        })

        bug_df = pd.DataFrame({
            'file_id': [1, 2, 3],
            'accuracy': [0.8, 0.9, 0.7]
        })

        merged = join_metrics_for_correlation(clone_df, perplexity_df, bug_df)

        assert len(merged) == 3
        assert 'clone_density' in merged.columns
        assert 'perplexity' in merged.columns
        assert 'accuracy' in merged.columns

    def test_inner_join_excludes_missing(self):
        """Test that inner join excludes records without matches."""
        clone_df = pd.DataFrame({
            'file_id': [1, 2, 3],
            'clone_density': [0.1, 0.2, 0.3]
        })

        perplexity_df = pd.DataFrame({
            'file_id': [1, 3],  # Missing file_id 2
            'perplexity': [10.0, 30.0]
        })

        bug_df = pd.DataFrame({
            'file_id': [1, 2, 3],
            'accuracy': [0.8, 0.9, 0.7]
        })

        merged = join_metrics_for_correlation(clone_df, perplexity_df, bug_df)

        # Only file_ids 1 and 3 should remain
        assert len(merged) == 2
        assert list(merged['file_id']) == [1, 3]

    def test_missing_key_column_raises_error(self):
        """Test that missing key column raises ValueError."""
        clone_df = pd.DataFrame({
            'id': [1, 2, 3],  # Wrong column name
            'clone_density': [0.1, 0.2, 0.3]
        })

        perplexity_df = pd.DataFrame({
            'file_id': [1, 2, 3],
            'perplexity': [10.0, 20.0, 30.0]
        })

        bug_df = pd.DataFrame({
            'file_id': [1, 2, 3],
            'accuracy': [0.8, 0.9, 0.7]
        })

        with pytest.raises(ValueError):
            join_metrics_for_correlation(clone_df, perplexity_df, bug_df, key_column='file_id')


class TestCalculateCorrelations:
    """Tests for correlation calculation."""

    def test_all_correlations_computed(self):
        """Test that all three correlations are computed."""
        merged_df = pd.DataFrame({
            'file_id': range(100),
            'clone_density': np.random.rand(100),
            'perplexity': np.random.rand(100) * 100,
            'accuracy': np.random.rand(100)
        })

        results = calculate_correlations(merged_df)

        assert 'clone_density_vs_perplexity' in results
        assert 'clone_density_vs_accuracy' in results
        assert 'perplexity_vs_accuracy' in results

    def test_results_contain_required_fields(self):
        """Test that results contain all required fields."""
        merged_df = pd.DataFrame({
            'file_id': range(100),
            'clone_density': np.random.rand(100),
            'perplexity': np.random.rand(100) * 100,
            'accuracy': np.random.rand(100)
        })

        results = calculate_correlations(merged_df)

        for correlation_name, metrics in results.items():
            assert 'correlation' in metrics
            assert 'p_value' in metrics
            assert 'n_samples' in metrics

    def test_correlation_values_in_valid_range(self):
        """Test that correlation values are in [-1, 1]."""
        merged_df = pd.DataFrame({
            'file_id': range(100),
            'clone_density': np.random.rand(100),
            'perplexity': np.random.rand(100) * 100,
            'accuracy': np.random.rand(100)
        })

        results = calculate_correlations(merged_df)

        for correlation_name, metrics in results.items():
            assert -1.0 <= metrics['correlation'] <= 1.0, \
                f"{correlation_name}: correlation {metrics['correlation']} out of range"

    def test_p_values_in_valid_range(self):
        """Test that p-values are in [0, 1]."""
        merged_df = pd.DataFrame({
            'file_id': range(100),
            'clone_density': np.random.rand(100),
            'perplexity': np.random.rand(100) * 100,
            'accuracy': np.random.rand(100)
        })

        results = calculate_correlations(merged_df)

        for correlation_name, metrics in results.items():
            assert 0.0 <= metrics['p_value'] <= 1.0, \
                f"{correlation_name}: p-value {metrics['p_value']} out of range"


class TestSaveCorrelationResults:
    """Tests for saving correlation results."""

    def test_save_to_csv(self):
        """Test that results are saved to CSV file."""
        results = {
            'test_correlation': {
                'correlation': 0.5,
                'p_value': 0.01,
                'n_samples': 100
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            saved_path = save_correlation_results(results, output_path)

            assert os.path.exists(saved_path)

            # Verify CSV content
            df = pd.read_csv(saved_path)
            assert len(df) == 1
            assert df['correlation_coefficient'].iloc[0] == 0.5
            assert df['p_value'].iloc[0] == 0.01
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_creates_output_directory(self):
        """Test that output directory is created if it doesn't exist."""
        results = {
            'test_correlation': {
                'correlation': 0.5,
                'p_value': 0.01,
                'n_samples': 100
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
          output_path = os.path.join(tmpdir, 'subdir', 'results.csv')
          save_correlation_results(results, output_path)
          assert os.path.exists(output_path)


class TestValidateCorrelationResults:
    """Tests for result validation."""

    def test_valid_results_pass(self):
        """Test that valid results pass validation."""
        results = {
            'test_correlation': {
                'correlation': 0.5,
                'p_value': 0.01,
                'n_samples': 1000
            }
        }

        assert validate_correlation_results(results, min_samples=1000) is True

    def test_insufficient_samples_fail(self):
        """Test that insufficient samples fail validation."""
        results = {
            'test_correlation': {
                'correlation': 0.5,
                'p_value': 0.01,
                'n_samples': 500
            }
        }

        assert validate_correlation_results(results, min_samples=1000) is False

    def test_nan_correlation_fails(self):
        """Test that NaN correlation fails validation."""
        results = {
            'test_correlation': {
                'correlation': float('nan'),
                'p_value': 0.01,
                'n_samples': 1000
            }
        }

        assert validate_correlation_results(results, min_samples=100) is False
