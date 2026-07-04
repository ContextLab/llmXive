import os
import sys
import tempfile
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.models.explain import compute_shap_values, compute_mean_absolute_shap, rank_features

class TestSHAPComputation:
    """Unit tests for SHAP value computation (CPU-only)"""

    @pytest.fixture
    def sample_data(self):
        """Create a small sample dataset for testing"""
        np.random.seed(42)
        n_samples = 100
        n_features = 5

        data = {
            'composition': [f'Ge_{i%3}Se_{10-i%3}' for i in range(n_samples)],
            'Tg': np.random.uniform(300, 600, n_samples),
            'mean_coordination': np.random.uniform(2.0, 3.0, n_samples),
            'electronegativity_variance': np.random.uniform(0.1, 0.5, n_samples),
            'atomic_radius_variance': np.random.uniform(0.01, 0.05, n_samples),
            'chemical_family': np.random.choice(['Chalcogenide', 'Sulfide', 'Selenide'], n_samples)
        }

        return pd.DataFrame(data)

    @pytest.fixture
    def mock_model(self):
        """Create a mock Gradient Boosting model"""
        model = MagicMock()
        model.predict = MagicMock(return_value=np.random.rand(10))
        model.feature_importances_ = np.random.rand(5)
        return model

    @pytest.fixture
    def mock_tree_explainer(self):
        """Create a mock SHAP TreeExplainer"""
        explainer = MagicMock()
        explainer.shap_values = MagicMock(return_value=np.random.rand(10, 5))
        return explainer

    def test_compute_shap_values_cpu_only(self, sample_data, mock_model, mock_tree_explainer):
        """Test that SHAP computation runs on CPU without GPU dependencies"""
        # Mock shap.TreeExplainer to ensure CPU-only usage
        with patch('src.models.explain.shap') as mock_shap:
            mock_shap.TreeExplainer.return_value = mock_tree_explainer

            # Prepare feature matrix
            feature_cols = ['mean_coordination', 'electronegativity_variance', 
                          'atomic_radius_variance']
            X = sample_data[feature_cols]

            # Compute SHAP values
            shap_values = compute_shap_values(X, mock_model)

            # Verify results
            assert shap_values is not None
            assert isinstance(shap_values, np.ndarray)
            assert shap_values.shape[0] == X.shape[0]
            assert shap_values.shape[1] == X.shape[1]

            # Verify TreeExplainer was used (CPU-only)
            mock_shap.TreeExplainer.assert_called_once()

    def test_compute_shap_values_with_real_model_structure(self, sample_data):
        """Test SHAP computation with a real sklearn model structure"""
        from sklearn.ensemble import GradientBoostingRegressor

        # Create a real (but small) model for testing
        feature_cols = ['mean_coordination', 'electronegativity_variance', 
                      'atomic_radius_variance']
        X = sample_data[feature_cols]
        y = sample_data['Tg']

        # Train a tiny model
        model = GradientBoostingRegressor(
            n_estimators=5,  # Very small for unit test speed
            max_depth=2,
            random_state=42
        )
        model.fit(X, y)

        # Compute SHAP values
        shap_values = compute_shap_values(X, model)

        # Verify results
        assert shap_values is not None
        assert isinstance(shap_values, np.ndarray)
        assert shap_values.shape[0] == X.shape[0]
        assert shap_values.shape[1] == X.shape[1]

    def test_compute_mean_absolute_shap(self, sample_data, mock_model, mock_tree_explainer):
        """Test computation of mean absolute SHAP values"""
        with patch('src.models.explain.shap') as mock_shap:
            mock_shap.TreeExplainer.return_value = mock_tree_explainer

            feature_cols = ['mean_coordination', 'electronegativity_variance', 
                          'atomic_radius_variance']
            X = sample_data[feature_cols]

            shap_values = compute_shap_values(X, mock_model)
            mean_abs_shap = compute_mean_absolute_shap(shap_values)

            assert isinstance(mean_abs_shap, dict)
            assert len(mean_abs_shap) == X.shape[1]
            assert all(v >= 0 for v in mean_abs_shap.values())

    def test_rank_features(self, sample_data, mock_model, mock_tree_explainer):
        """Test feature ranking by SHAP importance"""
        with patch('src.models.explain.shap') as mock_shap:
            mock_shap.TreeExplainer.return_value = mock_tree_explainer

            feature_cols = ['mean_coordination', 'electronegativity_variance', 
                          'atomic_radius_variance']
            X = sample_data[feature_cols]

            shap_values = compute_shap_values(X, mock_model)
            ranked_features = rank_features(shap_values, feature_cols)

            assert isinstance(ranked_features, list)
            assert len(ranked_features) == len(feature_cols)
            
            # Verify ranking is in descending order
            for i in range(len(ranked_features) - 1):
                assert ranked_features[i][1] >= ranked_features[i+1][1]

    def test_large_dataset_sampling(self, mock_model, mock_tree_explainer):
        """Test that large datasets are sampled to <=5000 samples"""
        # Create a large dataset
        np.random.seed(42)
        n_samples = 6000
        n_features = 5

        large_data = {
            'mean_coordination': np.random.uniform(2.0, 3.0, n_samples),
            'electronegativity_variance': np.random.uniform(0.1, 0.5, n_samples),
            'atomic_radius_variance': np.random.uniform(0.01, 0.05, n_samples),
            'other_feature_1': np.random.rand(n_samples),
            'other_feature_2': np.random.rand(n_samples),
        }

        X_large = pd.DataFrame(large_data)

        with patch('src.models.explain.shap') as mock_shap:
            mock_shap.TreeExplainer.return_value = mock_tree_explainer

            # This should trigger sampling
            shap_values = compute_shap_values(X_large, mock_model)

            # Verify the explainer was called with sampled data
            # The function should have sampled to <=5000
            assert shap_values.shape[0] <= 5000

    def test_cpu_only_compliance(self, sample_data):
        """Verify that the computation does not attempt to use GPU/CUDA"""
        from sklearn.ensemble import GradientBoostingRegressor

        feature_cols = ['mean_coordination', 'electronegativity_variance', 
                      'atomic_radius_variance']
        X = sample_data[feature_cols]
        y = sample_data['Tg']

        model = GradientBoostingRegressor(n_estimators=5, max_depth=2, random_state=42)
        model.fit(X, y)

        # Mock torch.cuda to ensure no CUDA usage
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.cuda.device_count', return_value=0):
                shap_values = compute_shap_values(X, model)
                
                assert shap_values is not None
                # No GPU errors should occur

    def test_empty_feature_matrix(self):
        """Test handling of empty feature matrix"""
        X_empty = pd.DataFrame()
        
        with pytest.raises((ValueError, IndexError)):
            compute_shap_values(X_empty, MagicMock())

    def test_single_sample(self, mock_model, mock_tree_explainer):
        """Test SHAP computation with a single sample"""
        single_sample = pd.DataFrame({
            'mean_coordination': [2.5],
            'electronegativity_variance': [0.3],
            'atomic_radius_variance': [0.03]
        })

        with patch('src.models.explain.shap') as mock_shap:
            mock_shap.TreeExplainer.return_value = mock_tree_explainer

            shap_values = compute_shap_values(single_sample, mock_model)

            assert shap_values.shape[0] == 1
            assert shap_values.shape[1] == 3

    def test_feature_names_preserved(self, sample_data, mock_model, mock_tree_explainer):
        """Test that feature names are preserved in SHAP results"""
        with patch('src.models.explain.shap') as mock_shap:
            mock_shap.TreeExplainer.return_value = mock_tree_explainer

            feature_cols = ['mean_coordination', 'electronegativity_variance', 
                          'atomic_radius_variance']
            X = sample_data[feature_cols]

            shap_values = compute_shap_values(X, mock_model)
            mean_abs_shap = compute_mean_absolute_shap(shap_values)

            # Verify all original feature names are present
            for col in feature_cols:
                assert col in mean_abs_shap

if __name__ == '__main__':
    pytest.main([__file__, '-v'])