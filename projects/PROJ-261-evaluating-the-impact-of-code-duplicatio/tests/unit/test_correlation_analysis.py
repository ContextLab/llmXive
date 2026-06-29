"""
Unit tests for correlation_analysis.py Spearman coefficient computation.

Tests the compute_spearman_correlation function and related correlation
analysis functionality.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from correlation_analysis import (
    compute_spearman_correlation,
    compute_correlation_matrix,
    load_metrics_data,
    run_correlation_analysis,
    save_correlation_results
)


class TestComputeSpearmanCorrelation:
    """Tests for the compute_spearman_correlation function."""

    def test_perfect_positive_correlation(self):
        """Test that perfectly correlated arrays return coefficient of 1.0."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])

        corr, p_value = compute_spearman_correlation(x, y)

        assert abs(corr - 1.0) < 1e-10, f"Expected 1.0, got {corr}"
        assert p_value == 0.0

    def test_perfect_negative_correlation(self):
        """Test that perfectly anti-correlated arrays return coefficient of -1.0."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([10.0, 8.0, 6.0, 4.0, 2.0])

        corr, p_value = compute_spearman_correlation(x, y)

        assert abs(corr - (-1.0)) < 1e-10, f"Expected -1.0, got {corr}"
        assert p_value == 0.0

    def test_no_correlation(self):
        """Test that uncorrelated arrays return coefficient near 0."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)

        corr, p_value = compute_spearman_correlation(x, y)

        # With random data, correlation should be close to 0
        assert abs(corr) < 0.3, f"Expected near 0, got {corr}"
        assert p_value > 0.05

    def test_moderate_positive_correlation(self):
        """Test moderate positive correlation with noise."""
        np.random.seed(42)
        x = np.arange(50, dtype=float)
        y = x * 2 + np.random.randn(50) * 10

        corr, p_value = compute_spearman_correlation(x, y)

        # Should have moderate to strong positive correlation
        assert 0.7 < corr < 1.0, f"Expected 0.7-1.0, got {corr}"
        assert p_value < 0.05

    def test_moderate_negative_correlation(self):
        """Test moderate negative correlation with noise."""
        np.random.seed(42)
        x = np.arange(50, dtype=float)
        y = -x * 2 + np.random.randn(50) * 10

        corr, p_value = compute_spearman_correlation(x, y)

        # Should have moderate to strong negative correlation
        assert -1.0 < corr < -0.7, f"Expected -1.0 to -0.7, got {corr}"
        assert p_value < 0.05

    def test_single_element_array(self):
        """Test that single element arrays raise appropriate error."""
        x = np.array([1.0])
        y = np.array([2.0])

        with pytest.raises(ValueError, match="Cannot compute correlation"):
            compute_spearman_correlation(x, y)

    def test_empty_arrays(self):
        """Test that empty arrays raise ValueError."""
        x = np.array([])
        y = np.array([])

        with pytest.raises(ValueError, match="Cannot compute correlation"):
            compute_spearman_correlation(x, y)

    def test_different_length_arrays(self):
        """Test that different length arrays raise ValueError."""
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([1.0, 2.0])

        with pytest.raises(ValueError, match="Arrays must have same length"):
            compute_spearman_correlation(x, y)

    def test_nan_policy_propagate(self):
        """Test that nan_policy='propagate' handles NaN values."""
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])

        # With propagate, should not raise but return NaN correlation
        corr, p_value = compute_spearman_correlation(x, y, nan_policy='propagate')

        # Result may be NaN or a computed value depending on scipy version
        assert isinstance(corr, float)
        assert isinstance(p_value, float)

    def test_nan_policy_omit(self):
        """Test that nan_policy='omit' removes NaN pairs."""
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])

        corr, p_value = compute_spearman_correlation(x, y, nan_policy='omit')

        # Should compute correlation on remaining 4 valid pairs
        assert abs(corr - 1.0) < 1e-10, f"Expected 1.0, got {corr}"
        assert p_value == 0.0

    def test_nan_policy_raise(self):
        """Test that nan_policy='raise' raises ValueError on NaN."""
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])

        with pytest.raises(ValueError, match="NaN values detected"):
            compute_spearman_correlation(x, y, nan_policy='raise')

    def test_all_nan_after_omit(self):
        """Test error when all pairs are NaN after omitting."""
        x = np.array([np.nan, np.nan, np.nan])
        y = np.array([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="No valid pairs remaining"):
            compute_spearman_correlation(x, y, nan_policy='omit')

    def test_constant_values(self):
        """Test handling of constant values (zero variance)."""
        x = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        # Should handle gracefully, possibly returning 0 or NaN
        corr, p_value = compute_spearman_correlation(x, y)
        assert isinstance(corr, float)
        assert isinstance(p_value, float)

    def test_large_arrays(self):
        """Test computation on large arrays."""
        np.random.seed(42)
        n = 10000
        x = np.random.randn(n)
        y = x * 0.5 + np.random.randn(n) * 0.5

        corr, p_value = compute_spearman_correlation(x, y)

        # Should complete without error
        assert isinstance(corr, float)
        assert isinstance(p_value, float)
        assert -1.0 <= corr <= 1.0
        assert 0.0 <= p_value <= 1.0

    def test_integer_inputs(self):
        """Test that integer arrays are handled correctly."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])

        corr, p_value = compute_spearman_correlation(x, y)

        assert abs(corr - 1.0) < 1e-10

    def test_negative_values(self):
        """Test with negative values in arrays."""
        x = np.array([-5.0, -3.0, -1.0, 1.0, 3.0, 5.0])
        y = np.array([-10.0, -6.0, -2.0, 2.0, 6.0, 10.0])

        corr, p_value = compute_spearman_correlation(x, y)

        assert abs(corr - 1.0) < 1e-10

    def test_returns_tuple(self):
        """Test that function returns a tuple of (correlation, p_value)."""
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([3.0, 2.0, 1.0])

        result = compute_spearman_correlation(x, y)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)


class TestComputeCorrelationMatrix:
    """Tests for the compute_correlation_matrix function."""

    def test_basic_correlation_matrix(self):
        """Test basic correlation matrix computation."""
        df = pd.DataFrame({
            'a': [1.0, 2.0, 3.0, 4.0, 5.0],
            'b': [2.0, 4.0, 6.0, 8.0, 10.0],
            'c': [5.0, 3.0, 1.0, 3.0, 5.0]
        })

        matrix = compute_correlation_matrix(df, ['a', 'b', 'c'])

        assert matrix.shape == (3, 3)
        assert matrix.index.tolist() == ['a', 'b', 'c']
        assert matrix.columns.tolist() == ['a', 'b', 'c']
        assert matrix.loc['a', 'a'] == 1.0
        assert matrix.loc['b', 'b'] == 1.0
        assert matrix.loc['c', 'c'] == 1.0

    def test_missing_columns(self):
        """Test error when columns are missing from DataFrame."""
        df = pd.DataFrame({
            'a': [1.0, 2.0, 3.0],
            'b': [2.0, 4.0, 6.0]
        })

        with pytest.raises(ValueError, match="Missing columns"):
            compute_correlation_matrix(df, ['a', 'b', 'c'])

    def test_symmetric_matrix(self):
        """Test that correlation matrix is symmetric."""
        df = pd.DataFrame({
            'a': np.random.randn(50),
            'b': np.random.randn(50),
            'c': np.random.randn(50)
        })

        matrix = compute_correlation_matrix(df, ['a', 'b', 'c'])

        # Check symmetry
        assert np.allclose(matrix.values, matrix.values.T)


class TestRunCorrelationAnalysis:
    """Tests for the run_correlation_analysis function."""

    def test_basic_analysis(self):
        """Test basic correlation analysis execution."""
        np.random.seed(42)
        df = pd.DataFrame({
            'clone_density': np.random.randn(100),
            'perplexity': np.random.randn(100),
            'pass@1': np.random.randn(100)
        })

        results = run_correlation_analysis(df)

        assert 'correlations' in results
        assert 'sample_size' in results
        assert results['sample_size'] == 100
        assert 'clone_perplexity' in results['correlations']
        assert 'clone_accuracy' in results['correlations']
        assert 'perplexity_accuracy' in results['correlations']

    def test_missing_required_columns(self):
        """Test error when required columns are missing."""
        df = pd.DataFrame({
            'clone_density': [1.0, 2.0, 3.0]
        })

        with pytest.raises(ValueError, match="Missing required columns"):
            run_correlation_analysis(df)

    def test_without_accuracy_column(self):
        """Test analysis without accuracy column."""
        df = pd.DataFrame({
            'clone_density': np.random.randn(50),
            'perplexity': np.random.randn(50)
        })

        results = run_correlation_analysis(
            df,
            accuracy_column=None
        )

        assert 'clone_perplexity' in results['correlations']
        assert 'clone_accuracy' not in results['correlations']


class TestSaveCorrelationResults:
    """Tests for the save_correlation_results function."""

    def test_save_to_file(self, tmp_path):
        """Test saving results to CSV file."""
        results = {
            'timestamp': '2024-01-01T00:00:00',
            'sample_size': 100,
            'correlations': {
                'clone_perplexity': {
                    'coefficient': 0.5,
                    'p_value': 0.001
                }
            }
        }

        output_path = tmp_path / 'correlation_results.csv'
        save_correlation_results(results, output_path)

        assert output_path.exists()

        df = pd.read_csv(output_path)
        assert len(df) == 1
        assert df.iloc[0]['metric_pair'] == 'clone_perplexity'
        assert df.iloc[0]['coefficient'] == 0.5
        assert df.iloc[0]['p_value'] == 0.001

    def test_create_parent_directories(self, tmp_path):
        """Test that parent directories are created if needed."""
        results = {
            'timestamp': '2024-01-01T00:00:00',
            'sample_size': 100,
            'correlations': {
                'test_metric': {
                    'coefficient': 0.5,
                    'p_value': 0.001
                }
            }
        }

        output_path = tmp_path / 'subdir1' / 'subdir2' / 'results.csv'
        save_correlation_results(results, output_path)

        assert output_path.exists()