import pytest
import numpy as np
import pandas as pd
import anndata
from pathlib import Path
import tempfile
import json

# Mock imports to avoid heavy dependencies in unit tests if necessary,
# but here we assume scanpy/leiden are available as per project requirements.
from clustering import (
    run_leiden_clustering,
    calculate_silhouette_score,
    optimize_resolution,
    calculate_fidelity_metrics,
    ClusteringError
)

@pytest.fixture
def mock_adata():
    """Create a mock AnnData object for testing."""
    np.random.seed(42)
    n_cells = 100
    n_genes = 50
    
    X = np.random.rand(n_cells, n_genes)
    obs = pd.DataFrame({
        'cell_type': ['type_A'] * 50 + ['type_B'] * 50
    }, index=[f'cell_{i}' for i in range(n_cells)])
    
    # Create mock PCA embedding
    X_pca = np.random.rand(n_cells, 10)
    
    adata = anndata.AnnData(X=X, obs=obs)
    adata.obsm['X_pca'] = X_pca
    return adata


def test_run_leiden_clustering(mock_adata):
    """Test that Leiden clustering runs and adds labels to obs."""
    adata = mock_adata.copy()
    # Pre-compute neighbors to avoid dependency on sc.pp.neighbors in this specific test
    # In real run_leiden_clustering, it checks for connectivities.
    # For this unit test, we simulate the state or run sc.pp.neighbors first.
    import scanpy as sc
    sc.pp.neighbors(adata, n_neighbors=15, use_rep='X_pca')
    
    result = run_leiden_clustering(adata, resolution=0.5)
    
    assert 'leiden' in result.obs.columns
    assert len(result.obs['leiden'].cat.categories) > 0


def test_calculate_silhouette_score(mock_adata):
    """Test silhouette score calculation."""
    import scanpy as sc
    adata = mock_adata.copy()
    sc.pp.neighbors(adata, n_neighbors=15, use_rep='X_pca')
    sc.tl.leiden(adata, resolution=0.5, key_added='leiden')
    
    score = calculate_silhouette_score(adata, labels_key='leiden')
    
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0


def test_optimize_resolution(mock_adata):
    """Test resolution optimization returns best resolution."""
    import scanpy as sc
    adata = mock_adata.copy()
    sc.pp.neighbors(adata, n_neighbors=15, use_rep='X_pca')
    
    best_res, best_score = optimize_resolution(adata, resolutions=[0.1, 0.5, 1.0])
    
    assert best_res in [0.1, 0.5, 1.0]
    assert isinstance(best_score, float)


def test_calculate_fidelity_metrics(mock_adata):
    """Test ARI and NMI calculation."""
    import scanpy as sc
    adata = mock_adata.copy()
    sc.pp.neighbors(adata, n_neighbors=15, use_rep='X_pca')
    sc.tl.leiden(adata, resolution=0.5, key_added='leiden')
    
    metrics = calculate_fidelity_metrics(adata, 'leiden', 'cell_type')
    
    assert 'ari' in metrics
    assert 'nmi' in metrics
    assert isinstance(metrics['ari'], float)
    assert isinstance(metrics['nmi'], float)


def test_clustering_error_missing_pca(mock_adata):
    """Test that ClusteringError is raised if PCA is missing."""
    adata = mock_adata.copy()
    del adata.obsm['X_pca']
    
    with pytest.raises(ClusteringError):
        calculate_silhouette_score(adata)
