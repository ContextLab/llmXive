"""
Unit tests for correlation analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from code.analysis.correlations import (
    load_metrics_data,
    perform_pca_on_metrics,
    apply_fdr_correction,
    perform_partial_correlation,
    run_correlations_with_fd_covariate
)

@pytest.fixture
def sample_metrics_df():
    """Create a sample DataFrame with metrics."""
    np.random.seed(42)
    n = 50
    return pd.DataFrame({
        'subject_id': [f'sub-{i:03d}' for i in range(n)],
        'modularity': np.random.uniform(0.3, 0.7, n),
        'global_efficiency': np.random.uniform(0.4, 0.8, n),
        'participation_coef': np.random.uniform(0.1, 0.5, n),
        'within_module_degree': np.random.uniform(1.0, 3.0, n),
        'mean_fd': np.random.uniform(0.05, 0.3, n),
        'motor_score': np.random.uniform(50, 100, n)
    })

@pytest.fixture
def temp_metrics_file(sample_metrics_df, tmp_path):
    """Create a temporary metrics file."""
    file_path = tmp_path / "aggregated_metrics.csv"
    sample_metrics_df.to_csv(file_path, index=False)
    return file_path

def test_perform_pca_on_metrics(sample_metrics_df):
    """Test PCA execution and output shapes."""
    pca_model, loadings, factor_scores = perform_pca_on_metrics(sample_metrics_df, n_components=2)
    
    # Check loadings shape
    assert loadings.shape == (4, 2), f"Expected (4, 2), got {loadings.shape}"
    assert list(loadings.index) == ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    # Check factor scores shape
    assert factor_scores.shape == (50, 3), f"Expected (50, 3), got {factor_scores.shape}"
    assert list(factor_scores.columns) == ['subject_id', 'pca_factor_1', 'pca_factor_2']
    
    # Check explained variance
    assert len(pca_model.explained_variance_ratio_) == 2
    assert sum(pca_model.explained_variance_ratio_) > 0

def test_apply_fdr_correction():
    """Test FDR correction logic."""
    p_values = [0.001, 0.01, 0.02, 0.05, 0.1, 0.2]
    q_values = apply_fdr_correction(p_values)
    
    assert len(q_values) == len(p_values)
    # q-values should be monotonically increasing with p-values
    assert all(q_values[i] <= q_values[j] for i, j in zip(range(len(q_values)-1), range(1, len(q_values))))
    # All q-values should be <= 1.0
    assert all(q <= 1.0 for q in q_values)

def test_perform_partial_correlation():
    """Test partial correlation calculation."""
    np.random.seed(42)
    n = 100
    x = np.random.randn(n)
    y = np.random.randn(n)
    z = np.random.randn(n)
    
    r, p = perform_partial_correlation(x, y, z)
    
    assert isinstance(r, float)
    assert -1 <= r <= 1
    assert 0 <= p <= 1

def test_run_correlations_with_fd_covariate(sample_metrics_df):
    """Test correlation with FD covariate."""
    results = run_correlations_with_fd_covariate(sample_metrics_df)
    
    assert len(results) > 0
    assert 'metric' in results.columns
    assert 'r' in results.columns
    assert 'p' in results.columns
    assert 'n' in results.columns
    assert 'covariate_controlled' in results.columns
    
    # Check that r values are in valid range
    assert all(-1 <= r <= 1 for r in results['r'])
    
    # Check that p values are in valid range
    assert all(0 <= p <= 1 for p in results['p'])