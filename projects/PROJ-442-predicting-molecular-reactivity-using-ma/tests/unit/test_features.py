"""
Unit tests for molecular feature extraction and dimensionality reduction pipelines.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import RDKit and scikit-learn components
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
from sklearn.pipeline import Pipeline

# Project imports based on API surface
# Note: Actual feature extraction logic will be in src/data/preprocessing.py (T021)
# We test the pipeline components directly here

# Mock data generator for testing
def create_mock_feature_dataframe(n_samples=100, n_features=50):
    """Create a mock feature dataframe for testing dimensionality reduction."""
    np.random.seed(42)
    data = np.random.rand(n_samples, n_features)
    
    # Add some features with zero variance (should be removed by VarianceThreshold)
    data[:, 0] = 1.0  # Constant feature
    data[:, 1] = 0.5  # Another constant feature
    
    # Add a feature with very low variance
    data[:, 2] = np.random.choice([0.1, 0.2], size=n_samples)
    
    # Create target variable correlated with some features
    y = data[:, 10:20].sum(axis=1) + np.random.normal(0, 0.1, n_samples)
    
    feature_names = [f"feature_{i}" for i in range(n_features)]
    df = pd.DataFrame(data, columns=feature_names)
    return df, y

class TestVarianceThreshold:
    """Tests for VarianceThreshold dimensionality reduction."""

    def test_variance_threshold_removes_constant_features(self):
        """Test that VarianceThreshold removes features with zero variance."""
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        # Create VarianceThreshold with threshold=0
        vt = VarianceThreshold(threshold=0.0)
        vt.fit(df)
        
        # Get number of features to keep
        n_features_kept = vt.get_support().sum()
        
        # We expect at least 47 features to be kept (50 - 3 constant/low-variance)
        assert n_features_kept >= 47, f"Expected at least 47 features, got {n_features_kept}"
        
        # Verify specific constant features are removed
        assert not vt.get_support()[0], "Constant feature at index 0 should be removed"
        assert not vt.get_support()[1], "Constant feature at index 1 should be removed"

    def test_variance_threshold_with_custom_threshold(self):
        """Test VarianceThreshold with a custom threshold."""
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        # Use a threshold that should remove the low variance feature
        vt = VarianceThreshold(threshold=0.01)
        vt.fit(df)
        
        n_features_kept = vt.get_support().sum()
        assert n_features_kept < 50, "Some features should be removed with threshold=0.01"

    def test_variance_threshold_transform_output_shape(self):
        """Test that transform output has correct shape."""
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        vt = VarianceThreshold(threshold=0.0)
        vt.fit(df)
        
        df_transformed = vt.transform(df)
        
        # Check dimensions
        assert df_transformed.shape[0] == 100, "Number of samples should be preserved"
        assert df_transformed.shape[1] < 50, "Number of features should be reduced"

class TestSelectKBest:
    """Tests for SelectKBest dimensionality reduction."""

    def test_select_kbest_selects_top_features(self):
        """Test that SelectKBest selects the top k features."""
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        k = 10
        selector = SelectKBest(score_func=f_regression, k=k)
        selector.fit(df, y)
        
        # Get selected features
        selected_mask = selector.get_support()
        n_selected = selected_mask.sum()
        
        assert n_selected == k, f"Expected exactly {k} features to be selected, got {n_selected}"

    def test_select_kbest_with_all_features(self):
        """Test SelectKBest with k equal to number of features."""
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        k = 50
        selector = SelectKBest(score_func=f_regression, k=k)
        selector.fit(df, y)
        
        selected_mask = selector.get_support()
        n_selected = selected_mask.sum()
        
        assert n_selected == 50, "All features should be selected when k=n_features"

    def test_select_kbest_transform_output(self):
        """Test that transform output has correct shape."""
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        k = 15
        selector = SelectKBest(score_func=f_regression, k=k)
        selector.fit(df, y)
        
        df_transformed = selector.transform(df)
        
        assert df_transformed.shape[0] == 100, "Number of samples should be preserved"
        assert df_transformed.shape[1] == k, f"Number of features should be {k}"

    def test_select_kbest_scores(self):
        """Test that scores are computed correctly."""
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        k = 10
        selector = SelectKBest(score_func=f_regression, k=k)
        selector.fit(df, y)
        
        scores = selector.scores_
        
        assert len(scores) == 50, "Should have scores for all features"
        assert all(s >= 0 for s in scores), "F-regression scores should be non-negative"

class TestDimensionalityReductionPipeline:
    """Tests for the combined dimensionality reduction pipeline."""

    def test_combined_pipeline_vt_then_selectkbest(self):
        """Test the full pipeline: VarianceThreshold followed by SelectKBest."""
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        # Create pipeline
        pipeline = Pipeline([
            ('variance_threshold', VarianceThreshold(threshold=0.0)),
            ('select_kbest', SelectKBest(score_func=f_regression, k=10))
        ])
        
        pipeline.fit(df, y)
        
        # Transform
        df_transformed = pipeline.transform(df)
        
        # Check final shape
        assert df_transformed.shape[0] == 100, "Samples should be preserved"
        assert df_transformed.shape[1] == 10, "Should have exactly 10 features after pipeline"

    def test_pipeline_with_different_k_values(self):
        """Test pipeline with different k values for SelectKBest."""
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        for k in [5, 10, 20]:
            pipeline = Pipeline([
                ('variance_threshold', VarianceThreshold(threshold=0.0)),
                ('select_kbest', SelectKBest(score_func=f_regression, k=k))
            ])
            
            pipeline.fit(df, y)
            df_transformed = pipeline.transform(df)
            
            assert df_transformed.shape[1] == k, f"Pipeline should output {k} features"

    def test_pipeline_handles_low_variance_features(self):
        """Test that pipeline properly handles low variance features before SelectKBest."""
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        # Create pipeline with low threshold
        pipeline = Pipeline([
            ('variance_threshold', VarianceThreshold(threshold=0.01)),
            ('select_kbest', SelectKBest(score_func=f_regression, k=10))
        ])
        
        pipeline.fit(df, y)
        df_transformed = pipeline.transform(df)
        
        # Should have removed low variance features first
        assert df_transformed.shape[0] == 100
        assert df_transformed.shape[1] == 10

class TestFeatureSelectionIntegration:
    """Integration tests for feature selection with mock molecular data."""

    def test_feature_selection_with_realistic_data(self):
        """Test feature selection with data that mimics molecular descriptors."""
        # Create data with some features that are highly correlated (common in molecular data)
        np.random.seed(42)
        n_samples = 200
        n_features = 100
        
        # Generate base features
        X = np.random.rand(n_samples, n_features)
        
        # Add some highly correlated features (like molecular descriptors often are)
        X[:, 10] = X[:, 0] * 0.95 + np.random.normal(0, 0.01, n_samples)
        X[:, 11] = X[:, 0] * 0.98 + np.random.normal(0, 0.01, n_samples)
        
        # Create target with known relationships
        y = (X[:, 5] * 2 + X[:, 15] * 1.5 + X[:, 25] * 1.0 + 
             np.random.normal(0, 0.5, n_samples))
        
        # Apply VarianceThreshold
        vt = VarianceThreshold(threshold=0.0)
        X_vt = vt.fit_transform(X)
        
        # Apply SelectKBest
        selector = SelectKBest(score_func=f_regression, k=10)
        X_selected = selector.fit_transform(X_vt, y)
        
        # Verify results
        assert X_selected.shape[0] == n_samples
        assert X_selected.shape[1] == 10
        
        # Check that selected features include the important ones (5, 15, 25)
        # Note: Due to randomness, they might not all be selected, but at least one should be
        selected_indices = np.where(selector.get_support())[0]
        
        # Map back to original indices (accounting for variance threshold removal)
        original_indices = np.where(vt.get_support())[0]
        if len(original_indices) > 0:
            selected_original = original_indices[selected_indices]
            # At least one of the important features should be selected
            important_features = [5, 15, 25]
            found_important = any(f in selected_original for f in important_features)
            assert found_important, "At least one important feature should be selected"

    def test_pipeline_reproducibility(self):
        """Test that the pipeline produces reproducible results."""
        np.random.seed(123)
        df, y = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        pipeline = Pipeline([
            ('variance_threshold', VarianceThreshold(threshold=0.0)),
            ('select_kbest', SelectKBest(score_func=f_regression, k=10))
        ])
        
        pipeline.fit(df, y)
        result1 = pipeline.transform(df)
        
        # Reset and run again
        np.random.seed(123)
        df2, y2 = create_mock_feature_dataframe(n_samples=100, n_features=50)
        
        pipeline2 = Pipeline([
            ('variance_threshold', VarianceThreshold(threshold=0.0)),
            ('select_kbest', SelectKBest(score_func=f_regression, k=10))
        ])
        
        pipeline2.fit(df2, y2)
        result2 = pipeline2.transform(df2)
        
        # Results should be identical
        assert np.allclose(result1, result2), "Pipeline results should be reproducible"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])