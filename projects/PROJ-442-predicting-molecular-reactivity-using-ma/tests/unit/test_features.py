import pytest
import numpy as np
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import pandas as pd

from src.data.schemas import FeatureVector
from src.modeling.config import load_config


class TestDimensionalityReduction:
    """Unit tests for dimensionality reduction pipeline (Variance Threshold + SelectKBest)."""

    @pytest.fixture
    def sample_feature_matrix(self):
        """Create a sample feature matrix for testing."""
        np.random.seed(42)
        n_samples = 100
        n_features = 50

        # Create features with varying variance
        features = np.random.randn(n_samples, n_features)

        # Make some features have zero variance (constant)
        features[:, 0:5] = 1.0  # Constant features

        # Make some features have very low variance
        features[:, 5:10] = np.random.randn(n_samples, 5) * 0.001

        # Create target variable
        target = np.random.randn(n_samples)

        return pd.DataFrame(features, columns=[f'feat_{i}' for i in range(n_features)]), target

    @pytest.fixture
    def sample_config(self):
        """Load sample configuration."""
        return load_config()

    def test_variance_threshold_removal(self, sample_feature_matrix):
        """Test that VarianceThreshold removes constant and low-variance features."""
        X, y = sample_feature_matrix

        # Initialize VarianceThreshold with default threshold (0)
        vt = VarianceThreshold(threshold=0.0)

        # Fit and transform
        X_transformed = vt.fit_transform(X)

        # Check that constant features were removed
        original_features = X.shape[1]
        transformed_features = X_transformed.shape[1]

        # At least the 5 constant features should be removed
        assert transformed_features < original_features
        assert transformed_features >= 0

    def test_variance_threshold_custom_threshold(self, sample_feature_matrix):
        """Test VarianceThreshold with custom threshold."""
        X, y = sample_feature_matrix

        # Use a threshold that should remove low-variance features
        vt = VarianceThreshold(threshold=0.01)

        X_transformed = vt.fit_transform(X)

        # Verify transformation succeeded
        assert X_transformed.shape[0] == X.shape[0]
        assert X_transformed.shape[1] <= X.shape[1]

    def test_selectkbest_feature_selection(self, sample_feature_matrix):
        """Test SelectKBest for feature selection."""
        X, y = sample_feature_matrix

        # Initialize SelectKBest with f_regression and k=10
        k = 10
        selector = SelectKBest(score_func=f_regression, k=k)

        # Fit and transform
        X_transformed = selector.fit_transform(X, y)

        # Check that exactly k features are selected (or all if fewer than k)
        assert X_transformed.shape[1] <= k
        assert X_transformed.shape[1] > 0
        assert X_transformed.shape[0] == X.shape[0]

    def test_selectkbest_scores(self, sample_feature_matrix):
        """Test that SelectKBest computes scores correctly."""
        X, y = sample_feature_matrix

        k = 10
        selector = SelectKBest(score_func=f_regression, k=k)

        # Fit to compute scores
        selector.fit(X, y)

        # Check that scores were computed
        assert hasattr(selector, 'scores_')
        assert len(selector.scores_) == X.shape[1]

        # Check that p-values were computed
        assert hasattr(selector, 'pvalues_')
        assert len(selector.pvalues_) == X.shape[1]

    def test_combined_pipeline(self, sample_feature_matrix):
        """Test combined VarianceThreshold + SelectKBest pipeline."""
        X, y = sample_feature_matrix

        # Create pipeline: VarianceThreshold -> SelectKBest
        pipeline = Pipeline([
            ('variance_threshold', VarianceThreshold(threshold=0.01)),
            ('select_k_best', SelectKBest(score_func=f_regression, k=10))
        ])

        # Fit and transform
        X_transformed = pipeline.fit_transform(X, y)

        # Verify output dimensions
        assert X_transformed.shape[0] == X.shape[0]
        assert X_transformed.shape[1] <= 10
        assert X_transformed.shape[1] > 0

    def test_pipeline_with_standardization(self, sample_feature_matrix):
        """Test pipeline with standardization step."""
        X, y = sample_feature_matrix

        # Create pipeline with standardization
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('variance_threshold', VarianceThreshold(threshold=0.01)),
            ('select_k_best', SelectKBest(score_func=f_regression, k=10))
        ])

        # Fit and transform
        X_transformed = pipeline.fit_transform(X, y)

        # Verify output dimensions
        assert X_transformed.shape[0] == X.shape[0]
        assert X_transformed.shape[1] <= 10
        assert X_transformed.shape[1] > 0

    def test_selectkbest_all_features(self, sample_feature_matrix):
        """Test SelectKBest when k >= number of features."""
        X, y = sample_feature_matrix

        # Set k to be larger than number of features
        k = X.shape[1] + 10
        selector = SelectKBest(score_func=f_regression, k=k)

        X_transformed = selector.fit_transform(X, y)

        # Should return all features (after variance thresholding)
        assert X_transformed.shape[1] <= X.shape[1]
        assert X_transformed.shape[1] > 0

    def test_empty_features_after_threshold(self, sample_feature_matrix):
        """Test behavior when all features have zero variance."""
        X, y = sample_feature_matrix

        # Make all features constant
        X_constant = np.ones_like(X)

        # Apply VarianceThreshold
        vt = VarianceThreshold(threshold=0.0)
        X_transformed = vt.fit_transform(X_constant)

        # Should return empty array
        assert X_transformed.shape[1] == 0
        assert X_transformed.shape[0] == X.shape[0]

    def test_feature_selection_deterministic(self, sample_feature_matrix):
        """Test that feature selection is deterministic with same seed."""
        X, y = sample_feature_matrix

        # Set seed for reproducibility
        np.random.seed(42)
        selector1 = SelectKBest(score_func=f_regression, k=10)
        selector1.fit(X, y)
        X1 = selector1.transform(X)

        np.random.seed(42)
        selector2 = SelectKBest(score_func=f_regression, k=10)
        selector2.fit(X, y)
        X2 = selector2.transform(X)

        # Results should be identical
        assert np.allclose(X1, X2)

    def test_config_integration(self, sample_config):
        """Test that pipeline respects configuration settings."""
        # Verify config has dimensionality reduction settings
        assert 'dimensionality_reduction' in sample_config
        config = sample_config['dimensionality_reduction']

        assert 'variance_threshold' in config
        assert 'select_k_best' in config
        assert 'k' in config['select_k_best']
        assert 'score_function' in config['select_k_best']

        # Verify values are valid
        assert config['variance_threshold'] >= 0
        assert config['select_k_best']['k'] > 0
        assert config['select_k_best']['score_function'] in ['f_regression', 'mutual_info_regression']