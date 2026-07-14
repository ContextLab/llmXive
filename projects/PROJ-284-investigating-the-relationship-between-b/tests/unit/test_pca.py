"""
Unit tests for PCA functionality.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from code.analysis.correlations import (
    perform_pca_on_metrics, 
    save_pca_results, 
    load_metrics_data
)

@pytest.fixture
def sample_metrics_df():
    """Create a sample DataFrame with metrics for testing."""
    np.random.seed(42)
    n_subjects = 50
    return pd.DataFrame({
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'modularity': np.random.uniform(0.3, 0.8, n_subjects),
        'global_efficiency': np.random.uniform(0.1, 0.5, n_subjects),
        'participation_coef': np.random.uniform(0.2, 0.6, n_subjects),
        'within_module_degree': np.random.uniform(0.1, 0.4, n_subjects)
    })

def test_perform_pca_on_metrics(sample_metrics_df):
    """Test PCA computation on metrics."""
    pca, scores, X = perform_pca_on_metrics(sample_metrics_df)
    
    # Check PCA model is fitted
    assert pca is not None
    assert pca.n_components_ == 2
    
    # Check scores shape
    assert scores.shape == (len(sample_metrics_df), 2)
    
    # Check loadings sum to 1 (variance explained)
    assert np.isclose(pca.explained_variance_ratio_.sum(), 1.0, atol=1e-5)

def test_save_pca_results(sample_metrics_df, tmp_path):
    """Test saving PCA results to CSV."""
    pca, scores, X = perform_pca_on_metrics(sample_metrics_df)
    
    loadings_path = tmp_path / "pca_loadings.csv"
    scores_path = tmp_path / "factor_scores.csv"
    
    save_pca_results(pca, scores, sample_metrics_df, str(loadings_path), str(scores_path))
    
    # Check files were created
    assert loadings_path.exists()
    assert scores_path.exists()
    
    # Check file contents
    loadings_df = pd.read_csv(loadings_path)
    scores_df = pd.read_csv(scores_path)
    
    assert 'component_1' in loadings_df.columns
    assert 'component_2' in loadings_df.columns
    assert 'subject_id' in scores_df.columns
    assert 'pca_factor_1' in scores_df.columns
    assert len(scores_df) == len(sample_metrics_df)

def test_pca_loadings_structure(sample_metrics_df):
    """Test that PCA loadings have correct structure."""
    pca, scores, X = perform_pca_on_metrics(sample_metrics_df)
    
    # Check loadings matrix
    assert pca.components_.shape == (2, 4)  # 2 components, 4 metrics
    
    # Check that loadings are reasonable (not all zeros)
    assert np.any(np.abs(pca.components_) > 0.01)