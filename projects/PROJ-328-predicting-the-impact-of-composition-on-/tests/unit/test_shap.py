"""
Unit tests for code/evaluation/shap_analysis.py
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluation.shap_analysis import SHAPAnalyzer


class TestSHAP:
    """Tests for SHAP analysis."""

    @pytest.fixture
    def sample_features(self):
        """Create sample feature data."""
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'feature_1': np.random.randn(n),
            'feature_2': np.random.randn(n),
            'feature_3': np.random.randn(n),
            'feature_4': np.random.randn(n),
        })

    @pytest.fixture
    def sample_model(self):
        """Create a simple model for SHAP analysis."""
        from sklearn.linear_model import LinearRegression
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 4)
        y = 2 * X[:, 0] + 3 * X[:, 1] + np.random.randn(n) * 0.1
        
        model = LinearRegression()
        model.fit(X, y)
        return model

    def test_shap_values_calculation(self, sample_features, sample_model):
        """Test SHAP values calculation."""
        analyzer = SHAPAnalyzer()
        
        shap_values = analyzer.calculate_shap_values(
            sample_model,
            sample_features
        )
        
        assert shap_values.shape == sample_features.shape

    def test_mean_abs_shap_values(self, sample_features, sample_model):
        """Test mean absolute SHAP values calculation."""
        analyzer = SHAPAnalyzer()
        
        mean_abs_shap = analyzer.calculate_mean_abs_shap(
            sample_model,
            sample_features
        )
        
        assert len(mean_abs_shap) == len(sample_features.columns)
        assert all(v >= 0 for v in mean_abs_shap.values())

    def test_feature_ranking(self, sample_features, sample_model):
        """Test feature ranking by SHAP importance."""
        analyzer = SHAPAnalyzer()
        
        ranking = analyzer.rank_features(
            sample_model,
            sample_features
        )
        
        assert len(ranking) == len(sample_features.columns)
        
        # Check that ranking is sorted by importance
        for i in range(len(ranking) - 1):
            assert ranking[i]['mean_abs_shap_value'] >= ranking[i+1]['mean_abs_shap_value']

    def test_save_shap_ranking(self, sample_features, sample_model, tmp_path):
        """Test saving SHAP ranking to file."""
        analyzer = SHAPAnalyzer()
        
        ranking = analyzer.rank_features(
            sample_model,
            sample_features
        )
        
        output_path = tmp_path / "shap_ranking.yaml"
        analyzer.save_shap_ranking(ranking, str(output_path))
        
        assert output_path.exists()

    def test_top_k_features(self, sample_features, sample_model):
        """Test top-k feature selection."""
        analyzer = SHAPAnalyzer()
        
        top_3 = analyzer.get_top_k_features(
            sample_model,
            sample_features,
            k=3
        )
        
        assert len(top_3) == 3
