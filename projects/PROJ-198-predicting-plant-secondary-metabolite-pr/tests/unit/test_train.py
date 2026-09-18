import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.modeling.train import (
    train_pgls_with_pca_optimization,
    apply_pca,
    determine_cv_method,
    ModelTrainingError
)
from code.modeling.phylo import construct_covariance_matrix, PhylogenyError

@pytest.fixture
def sample_features():
    """Generate sample feature matrix."""
    np.random.seed(42)
    return np.random.randn(30, 15)  # 30 samples, 15 features

@pytest.fixture
def sample_target():
    """Generate sample target vector."""
    np.random.seed(42)
    return np.random.randn(30)

@pytest.fixture
def mock_phylogeny_path(tmp_path):
    """Create a mock phylogenetic tree file."""
    tree_content = "(A:1.0, (B:0.5, C:0.5):0.5, D:1.5);"
    tree_path = tmp_path / "mock_tree.nwk"
    tree_path.write_text(tree_content)
    return tree_path

def test_apply_pca_reduction(sample_features):
    """Test that PCA reduces dimensionality correctly."""
    X_pca, pca_model, scaler = apply_pca(sample_features, n_components=5)
    
    assert X_pca.shape[1] == 5
    assert X_pca.shape[0] == sample_features.shape[0]
    assert hasattr(pca_model, 'explained_variance_ratio_')

def test_apply_pca_variance_threshold(sample_features):
    """Test PCA with variance threshold."""
    X_pca, pca_model, scaler = apply_pca(sample_features, n_components=0.95)
    
    # Should explain at least 95% variance
    assert pca_model.explained_variance_ratio_.sum() >= 0.95

def test_determine_cv_method_loo():
    """Test CV method selection for small datasets."""
    assert determine_cv_method(15) == 'loo'
    assert determine_cv_method(19) == 'loo'

def test_determine_cv_method_5fold():
    """Test CV method selection for larger datasets."""
    assert determine_cv_method(20) == '5fold'
    assert determine_cv_method(100) == '5fold'

def test_train_pgls_with_pca_optimization_high_features(
    sample_features, sample_target, mock_phylogeny_path
):
    """Test that PCA is applied when features > samples."""
    # Create scenario where features > samples
    X_large = np.random.randn(10, 50)  # 10 samples, 50 features
    y_small = np.random.randn(10)
    
    result = train_pgls_with_pca_optimization(
        X_large, y_small, mock_phylogeny_path,
        feature_threshold=10
    )
    
    assert result['pca_applied'] is True
    assert 'pca_info' in result
    assert result['pca_info']['original_features'] == 50
    assert result['pca_info']['reduced_features'] < 50

def test_train_pgls_with_pca_optimization_low_features(
    sample_features, sample_target, mock_phylogeny_path
):
    """Test that PCA is NOT applied when features <= samples."""
    result = train_pgls_with_pca_optimization(
        sample_features, sample_target, mock_phylogeny_path,
        feature_threshold=20
    )
    
    # With 15 features and 30 samples, PCA should not be applied
    assert result['pca_applied'] is False

def test_train_pgls_with_pca_optimization_default_threshold(
    sample_features, sample_target, mock_phylogeny_path
):
    """Test default threshold behavior (threshold = n_samples)."""
    # 30 samples, 15 features -> PCA not needed
    result = train_pgls_with_pca_optimization(
        sample_features, sample_target, mock_phylogeny_path
    )
    
    assert result['pca_applied'] is False

def test_train_pgls_with_pca_optimization_edge_case(
    sample_features, sample_target, mock_phylogeny_path
):
    """Test edge case where features == samples."""
    X_equal = np.random.randn(20, 20)
    y_equal = np.random.randn(20)
    
    result = train_pgls_with_pca_optimization(
        X_equal, y_equal, mock_phylogeny_path
    )
    
    # Features == samples, should not apply PCA with default threshold
    assert result['pca_applied'] is False

def test_train_pgls_with_pca_optimization_invalid_tree(
    sample_features, sample_target, tmp_path
):
    """Test error handling with invalid phylogeny."""
    invalid_tree = tmp_path / "invalid.nwk"
    invalid_tree.write_text("invalid tree content")
    
    with pytest.raises((PhylogenyError, ModelTrainingError, Exception)):
        train_pgls_with_pca_optimization(
            sample_features, sample_target, invalid_tree
        )

def test_pca_output_path(tmp_path, sample_features):
    """Test that PCA features are saved when path is provided."""
    output_path = tmp_path / "pca_output.csv"
    
    X_pca, pca_model, scaler = apply_pca(
        sample_features, n_components=5, output_path=output_path
    )
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert df.shape[1] == 5
    assert all(col.startswith('PC') for col in df.columns)
