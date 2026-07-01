"""
Integration tests for the statistical analysis module (T024).
Uses a mock dataset with known ground-truth correlations to verify
that the correlation analysis pipeline correctly identifies significant relationships.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.stats import compute_spearman_correlations, load_metrics_data
from config import get_data_root, ensure_directories


class TestCorrelationAnalysis:
    """Tests for Spearman correlation logic."""

    def test_spearman_perfect_positive_correlation(self):
        """Test that a perfectly linear increasing relationship yields rho=1."""
        data = pd.DataFrame({
            'metric': [1, 2, 3, 4, 5],
            'avalanche_exponent': [10, 20, 30, 40, 50]
        })
        
        structural_vars = ['metric']
        results = compute_spearman_correlations(data, structural_vars)
        
        assert len(results) == 1
        assert results.iloc[0]['metric'] == 'metric'
        assert np.isclose(results.iloc[0]['correlation'], 1.0)
        assert results.iloc[0]['p_value'] == 0.0  # p-value should be 0 for perfect correlation with n=5

    def test_spearman_no_correlation(self):
        """Test that random data yields low correlation (statistically insignificant usually)."""
        np.random.seed(42)
        data = pd.DataFrame({
            'metric': np.random.rand(100),
            'avalanche_exponent': np.random.rand(100)
        })
        
        structural_vars = ['metric']
        results = compute_spearman_correlations(data, structural_vars)
        
        assert len(results) == 1
        # We don't assert exact value, just that it runs and returns a valid float
        assert -1.0 <= results.iloc[0]['correlation'] <= 1.0
        assert 0.0 <= results.iloc[0]['p_value'] <= 1.0

    def test_handles_missing_columns(self):
        """Test that missing structural metric columns are handled gracefully."""
        data = pd.DataFrame({
            'metric_a': [1, 2, 3],
            'avalanche_exponent': [10, 20, 30]
        })
        
        structural_vars = ['metric_a', 'missing_metric']
        results = compute_spearman_correlations(data, structural_vars)
        
        assert len(results) == 2
        assert results.iloc[0]['metric'] == 'metric_a'
        assert results.iloc[0]['correlation'] == 1.0
        assert results.iloc[1]['metric'] == 'missing_metric'
        assert pd.isna(results.iloc[1]['correlation'])

    def test_insufficient_data_points(self):
        """Test behavior when n < 3."""
        data = pd.DataFrame({
            'metric': [1, 2],
            'avalanche_exponent': [10, 20]
        })
        
        structural_vars = ['metric']
        results = compute_spearman_correlations(data, structural_vars)
        
        assert len(results) == 1
        assert pd.isna(results.iloc[0]['correlation'])
        assert pd.isna(results.iloc[0]['p_value'])
        assert results.iloc[0]['n'] == 2

    def test_handles_nan_values(self):
        """Test that NaN values in data are dropped before correlation."""
        data = pd.DataFrame({
            'metric': [1, 2, np.nan, 4, 5],
            'avalanche_exponent': [10, np.nan, 30, 40, 50]
        })
        
        structural_vars = ['metric']
        results = compute_spearman_correlations(data, structural_vars)
        
        # Only 2 pairs should remain valid: (1,10) and (4,40), (5,50) -> wait, (4,40) and (5,50) are valid.
        # Row 0: 1, 10 -> Valid
        # Row 1: 2, NaN -> Invalid
        # Row 2: NaN, 30 -> Invalid
        # Row 3: 4, 40 -> Valid
        # Row 4: 5, 50 -> Valid
        # Total valid: 3
        assert results.iloc[0]['n'] == 3
        # Correlation of (1, 4, 5) and (10, 40, 50) is 1.0
        assert np.isclose(results.iloc[0]['correlation'], 1.0)

def test_load_metrics_data_missing_file():
    """Test that load_metrics_data raises FileNotFoundError if CSV is missing."""
    # Temporarily rename the file if it exists, or ensure it doesn't
    metrics_path = Path("data/results/exported_metrics.csv")
    original_exists = metrics_path.exists()
    
    if original_exists:
        metrics_path.rename(metrics_path.with_suffix('.csv.bak'))
    
    try:
        with pytest.raises(FileNotFoundError):
            load_metrics_data()
    finally:
        if original_exists:
            metrics_path.with_suffix('.csv.bak').rename(metrics_path)
        elif metrics_path.exists():
            metrics_path.unlink()


class TestIntegrationMockDataset:
    """
    Integration tests using a mock dataset of a small cohort of participants
    with known ground-truth correlations.
    """

    def test_known_positive_correlation_detected(self):
        """
        Create a mock dataset where 'degree_centrality' and 'avalanche_exponent'
        have a known strong positive correlation. Assert that the computed p_value < 0.05.
        """
        # Create a small cohort (N=20) with a known relationship
        np.random.seed(12345)
        n_subjects = 20
        
        # Generate a base variable
        base = np.random.rand(n_subjects)
        
        # Create metric with strong positive correlation to avalanche_exponent
        # avalanche_exponent = 2 * metric + noise
        metric_values = base
        noise = np.random.normal(0, 0.1, n_subjects)
        avalanche_values = 2.0 * metric_values + noise
        
        data = pd.DataFrame({
            'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
            'degree_centrality': metric_values,
            'clustering_coefficient': np.random.rand(n_subjects), # Unrelated metric
            'avalanche_exponent': avalanche_values
        })
        
        structural_vars = ['degree_centrality', 'clustering_coefficient']
        results = compute_spearman_correlations(data, structural_vars)
        
        # Find the row for degree_centrality
        degree_result = results[results['metric'] == 'degree_centrality'].iloc[0]
        
        # Assert strong correlation (rho > 0.8 expected for this noise level)
        assert degree_result['correlation'] > 0.8, f"Expected strong correlation, got {degree_result['correlation']}"
        
        # Assert statistical significance (p < 0.05)
        assert degree_result['p_value'] < 0.05, f"Expected p_value < 0.05, got {degree_result['p_value']}"
        
        # Assert the unrelated metric does not show significance (or is much weaker)
        clustering_result = results[results['metric'] == 'clustering_coefficient'].iloc[0]
        # We don't strictly assert p > 0.05 here as random chance could happen, 
        # but we assert the correlation is significantly lower than the known one
        assert clustering_result['correlation'] < degree_result['correlation'], \
            "Unrelated metric should have lower correlation than the known correlated one"

    def test_known_negative_correlation_detected(self):
        """
        Create a mock dataset with a known strong negative correlation.
        Assert p_value < 0.05 and correlation < 0.
        """
        np.random.seed(54321)
        n_subjects = 30
        
        base = np.random.rand(n_subjects)
        # Inverse relationship
        metric_values = base
        avalanche_values = -1.5 * metric_values + np.random.normal(0, 0.1, n_subjects)
        
        data = pd.DataFrame({
            'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
            'rich_club_coef': metric_values,
            'avalanche_exponent': avalanche_values
        })
        
        structural_vars = ['rich_club_coef']
        results = compute_spearman_correlations(data, structural_vars)
        
        result = results.iloc[0]
        
        # Assert strong negative correlation
        assert result['correlation'] < -0.8, f"Expected strong negative correlation, got {result['correlation']}"
        
        # Assert statistical significance
        assert result['p_value'] < 0.05, f"Expected p_value < 0.05, got {result['p_value']}"