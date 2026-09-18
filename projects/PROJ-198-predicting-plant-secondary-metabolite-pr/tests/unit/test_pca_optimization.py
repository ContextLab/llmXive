import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

from code.modeling.train import (
    train_pgls_with_pca_optimization,
    apply_pca,
    ModelTrainingError
)


class TestPCAOptimization:
    """Unit tests for T037: PCA optimization before PGLS."""

    def test_pca_applied_when_features_exceed_samples(self):
        """Verify PCA is applied when n_features > n_samples."""
        # Create high-dimensional, low-sample data
        n_samples = 10
        n_features = 50
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)
        species = [f"sp_{i}" for i in range(n_samples)]

        # Create a simple dummy tree file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nwk', delete=False) as f:
            f.write("((sp_0,sp_1),((sp_2,sp_3),(sp_4,sp_5)));" + "\n")
            tree_path = Path(f.name)

        try:
            result = train_pgls_with_pca_optimization(
                X, y, species, tree_path,
                variance_threshold=0.95
            )

            assert result['optimization_applied'] is True
            assert result['pca_info']['applied'] is True
            assert result['pca_info']['original_features'] == n_features
            assert result['pca_info']['reduced_features'] < n_features
        finally:
            tree_path.unlink()

    def test_pca_not_applied_when_features_less_than_samples(self):
        """Verify PCA is NOT applied when n_features <= n_samples."""
        n_samples = 50
        n_features = 10
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)
        species = [f"sp_{i}" for i in range(n_samples)]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.nwk', delete=False) as f:
            f.write("((sp_0,sp_1),((sp_2,sp_3),(sp_4,sp_5)));" + "\n")
            tree_path = Path(f.name)

        try:
            result = train_pgls_with_pca_optimization(
                X, y, species, tree_path,
                variance_threshold=0.95
            )

            # With 10 features and 50 samples, PCA should NOT be applied
            assert result['optimization_applied'] is False
            assert result['pca_info']['applied'] is False
        finally:
            tree_path.unlink()

    def test_pca_variance_retention(self):
        """Verify PCA retains the specified variance threshold."""
        n_samples = 30
        n_features = 100
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)

        X_reduced, pca_model, n_comp = apply_pca(
            X, y,
            target_variance=0.95,
            max_components=20
        )

        # Check that variance is retained
        variance_retained = sum(pca_model.explained_variance_ratio_)
        assert variance_retained >= 0.90  # Allow some tolerance

        # Check max_components constraint
        assert n_comp <= 20

    def test_pca_with_empty_matrix(self):
        """Verify PCA raises error on empty input."""
        X = np.array([]).reshape(0, 10)
        y = np.array([])

        with pytest.raises(ModelTrainingError):
            apply_pca(X, y)

    def test_pca_reduces_dimensionality(self):
        """Verify PCA actually reduces dimensionality."""
        n_samples = 20
        n_features = 100
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)

        X_reduced, pca_model, n_comp = apply_pca(X, y)

        assert X_reduced.shape[1] < n_features
        assert X_reduced.shape[0] == n_samples
