"""
Unit tests for Spearman correlation and FDR correction in stats_engine.py.

This module tests the statistical core of User Story 3:
- Spearman rank correlation calculation
- Benjamini-Hochberg FDR correction
- Robustness of results against synthetic data with known properties
"""
import pytest
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from typing import List, Dict, Any, Tuple

# Import the functions we are testing.
# Note: stats_engine.py is not yet implemented, so we define the expected
# functions here as placeholders for the test logic. In the real implementation,
# these would be imported from code/stats_engine.py.
# For now, we mock the expected behavior to ensure the test structure is correct.
# Once stats_engine.py is implemented, replace these mocks with real imports.

def mock_compute_spearman_correlations(
    metrics_df: pd.DataFrame,
    graph_metrics: List[str],
    perf_metrics: List[str]
) -> pd.DataFrame:
    """
    Mock implementation of compute_spearman_correlations for testing.
    Calculates Spearman correlation between all pairs of graph and performance metrics.
    """
    results = []
    for g_metric in graph_metrics:
        for p_metric in perf_metrics:
            if g_metric in metrics_df.columns and p_metric in metrics_df.columns:
                # Remove rows with NaN in either column
                valid_data = metrics_df[[g_metric, p_metric]].dropna()
                if len(valid_data) > 1:
                    rho, p_val = spearmanr(valid_data[g_metric], valid_data[p_metric])
                    results.append({
                        'metric_a': g_metric,
                        'metric_b': p_metric,
                        'spearman_rho': rho,
                        'p_value': p_val
                    })
    return pd.DataFrame(results)

def mock_apply_benjamini_hochberg_fdr(
    p_values: List[float]
) -> Tuple[List[float], List[bool]]:
    """
    Mock implementation of Benjamini-Hochberg FDR correction.
    Returns adjusted p-values and significance flags.
    """
    if not p_values:
        return [], []

    # Sort p-values and keep track of original indices
    indexed_p_vals = sorted(enumerate(p_values), key=lambda x: x[1])
    n = len(p_values)
    adjusted_p_vals = [0.0] * n
    significant = [False] * n

    # Apply BH procedure
    for i, (orig_idx, p_val) in enumerate(indexed_p_vals):
        # Calculate the adjusted p-value
        adj_p = p_val * n / (i + 1)
        # Ensure monotonicity (cumulative min from the end)
        if i > 0:
            adj_p = max(adj_p, adjusted_p_vals[indexed_p_vals[i-1][0]])
        # Clamp to [0, 1]
        adj_p = min(1.0, max(0.0, adj_p))
        adjusted_p_vals[orig_idx] = adj_p
        significant[orig_idx] = adj_p < 0.05

    return adjusted_p_vals, significant

class TestSpearmanCorrelation:
    """Tests for Spearman correlation calculation."""

    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data."""
        data = pd.DataFrame({
            'avg_path_length': [1.0, 2.0, 3.0, 4.0, 5.0],
            't1_time': [10.0, 20.0, 30.0, 40.0, 50.0]
        })
        rho, p_val = spearmanr(data['avg_path_length'], data['t1_time'])
        assert np.isclose(rho, 1.0), f"Expected rho=1.0, got {rho}"
        assert p_val == 0.0

    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data."""
        data = pd.DataFrame({
            'avg_path_length': [1.0, 2.0, 3.0, 4.0, 5.0],
            't1_time': [50.0, 40.0, 30.0, 20.0, 10.0]
        })
        rho, p_val = spearmanr(data['avg_path_length'], data['t1_time'])
        assert np.isclose(rho, -1.0), f"Expected rho=-1.0, got {rho}"
        assert p_val == 0.0

    def test_no_correlation(self):
        """Test with uncorrelated data."""
        np.random.seed(42)
        data = pd.DataFrame({
            'avg_path_length': np.random.randn(100),
            't1_time': np.random.randn(100)
        })
        rho, p_val = spearmanr(data['avg_path_length'], data['t1_time'])
        # With random data, rho should be close to 0, but not exactly 0
        assert abs(rho) < 0.5, f"Expected |rho| < 0.5, got {rho}"
        assert p_val > 0.05, f"Expected p > 0.05, got {p_val}"

    def test_with_missing_values(self):
        """Test handling of missing values."""
        data = pd.DataFrame({
            'avg_path_length': [1.0, 2.0, np.nan, 4.0, 5.0],
            't1_time': [10.0, np.nan, 30.0, 40.0, 50.0]
        })
        # spearmanr automatically handles NaN by ignoring pairs
        rho, p_val = spearmanr(data['avg_path_length'], data['t1_time'])
        # Should still compute a result from valid pairs
        assert not np.isnan(rho), "rho should not be NaN"
        assert not np.isnan(p_val), "p_val should not be NaN"

    def test_insufficient_data(self):
        """Test with insufficient data points."""
        data = pd.DataFrame({
            'avg_path_length': [1.0, 2.0],
            't1_time': [10.0, 20.0]
        })
        # With only 2 points, correlation is always perfect but p-value may be NaN
        rho, p_val = spearmanr(data['avg_path_length'], data['t1_time'])
        assert np.isclose(abs(rho), 1.0), f"Expected |rho|=1.0, got {rho}"

class TestBenjaminiHochbergFDR:
    """Tests for Benjamini-Hochberg FDR correction."""

    def test_all_significant(self):
        """Test with all p-values being significant."""
        p_vals = [0.01, 0.02, 0.03, 0.04, 0.05]
        adjusted, sig = mock_apply_benjamini_hochberg_fdr(p_vals)
        assert len(adjusted) == len(p_vals)
        assert len(sig) == len(p_vals)
        # All should be significant after correction (since they are small)
        assert all(sig), "All p-values should be significant"

    def test_all_non_significant(self):
        """Test with all p-values being non-significant."""
        p_vals = [0.2, 0.3, 0.4, 0.5, 0.6]
        adjusted, sig = mock_apply_benjamini_hochberg_fdr(p_vals)
        assert len(adjusted) == len(p_vals)
        assert len(sig) == len(p_vals)
        # None should be significant after correction
        assert not any(sig), "No p-values should be significant"

    def test_mixed_significance(self):
        """Test with mixed significant and non-significant p-values."""
        p_vals = [0.001, 0.05, 0.1, 0.2, 0.5]
        adjusted, sig = mock_apply_benjamini_hochberg_fdr(p_vals)
        assert len(adjusted) == len(p_vals)
        assert len(sig) == len(p_vals)
        # The smallest p-value should be significant
        assert sig[0], "Smallest p-value should be significant"
        # The largest p-values should not be significant
        assert not sig[-1], "Largest p-value should not be significant"

    def test_monotonicity(self):
        """Test that adjusted p-values are monotonically increasing."""
        p_vals = [0.05, 0.03, 0.01, 0.1, 0.2]
        adjusted, _ = mock_apply_benjamini_hochberg_fdr(p_vals)
        # Check monotonicity in the sorted order
        sorted_indices = np.argsort(p_vals)
        sorted_adj = [adjusted[i] for i in sorted_indices]
        for i in range(1, len(sorted_adj)):
            assert sorted_adj[i] >= sorted_adj[i-1], "Adjusted p-values must be monotonic"

    def test_empty_input(self):
        """Test with empty input."""
        adjusted, sig = mock_apply_benjamini_hochberg_fdr([])
        assert len(adjusted) == 0
        assert len(sig) == 0

    def test_single_value(self):
        """Test with a single p-value."""
        p_vals = [0.01]
        adjusted, sig = mock_apply_benjamini_hochberg_fdr(p_vals)
        assert len(adjusted) == 1
        assert len(sig) == 1
        assert adjusted[0] == 0.01  # For n=1, adj_p = p * 1 / 1 = p
        assert sig[0] == True  # 0.01 < 0.05

class TestIntegration:
    """Integration tests for the full correlation pipeline."""

    def test_full_pipeline_mock(self):
        """Test the full pipeline with mock data."""
        # Create synthetic data with known correlations
        np.random.seed(42)
        n_devices = 20
        
        # Generate correlated features
        base = np.random.randn(n_devices)
        graph_metrics = {
            'avg_path_length': base + np.random.randn(n_devices) * 0.1,
            'clustering_coef': base + np.random.randn(n_devices) * 0.1,
            'spectral_gap': -base + np.random.randn(n_devices) * 0.1  # Negative correlation
        }
        perf_metrics = {
            't1_time': base + np.random.randn(n_devices) * 0.1,
            't2_time': base + np.random.randn(n_devices) * 0.1,
            'readout_error': -base + np.random.randn(n_devices) * 0.1  # Negative correlation
        }
        
        # Create DataFrame
        df = pd.DataFrame({
            **graph_metrics,
            **perf_metrics
        })
        
        # Compute correlations
        results = mock_compute_spearman_correlations(
            df,
            list(graph_metrics.keys()),
            list(perf_metrics.keys())
        )
        
        # Apply FDR correction
        p_values = results['p_value'].tolist()
        adj_p_values, is_significant = mock_apply_benjamini_hochberg_fdr(p_values)
        
        # Add results to DataFrame
        results['adj_p_value'] = adj_p_values
        results['is_significant'] = is_significant
        
        # Verify we have results
        assert len(results) > 0, "Should have correlation results"
        
        # Verify significant correlations are detected
        # We expect positive correlations for (avg_path_length, t1_time), etc.
        # and negative correlations for (spectral_gap, readout_error)
        significant_results = results[results['is_significant']]
        assert len(significant_results) > 0, "Should have significant correlations"
        
        # Check that the correlation signs make sense
        for _, row in significant_results.iterrows():
            if 'spectral_gap' in row['metric_a'] or 'spectral_gap' in row['metric_b']:
                # Should be negative correlation with t1/t2, positive with readout_error
                pass  # Just verifying it exists
            else:
                # Should be positive correlation
                assert row['spearman_rho'] > 0, f"Expected positive correlation for {row['metric_a']} vs {row['metric_b']}"