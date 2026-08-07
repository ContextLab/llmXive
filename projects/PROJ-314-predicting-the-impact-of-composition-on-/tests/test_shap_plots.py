import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.generate_shap_plots import (
    save_feature_ranking,
    calculate_cv_stability,
    plot_shap_summary
)
import matplotlib
matplotlib.use('Agg') # Non-interactive backend for tests
import matplotlib.pyplot as plt

class TestSHAPPlots:
    
    @pytest.fixture
    def mock_data(self):
        """Create mock data for testing."""
        np.random.seed(42)
        n_samples = 50
        n_features = 5
        
        data = {
            'feature_a': np.random.randn(n_samples),
            'feature_b': np.random.randn(n_samples),
            'feature_c': np.random.randn(n_samples),
            'feature_d': np.random.randn(n_samples),
            'feature_e': np.random.randn(n_samples),
            'weibull_modulus': np.random.randn(n_samples)
        }
        return pd.DataFrame(data), ['feature_a', 'feature_b', 'feature_c', 'feature_d', 'feature_e']

    @pytest.fixture
    def mock_shap_values(self, mock_data):
        """Create mock SHAP values."""
        _, feature_cols = mock_data
        n_samples = len(feature_cols)
        # Return a 2D array of shape (n_samples, n_features)
        return np.random.randn(n_samples, len(feature_cols))

    def test_save_feature_ranking(self, mock_data, mock_shap_values, tmp_path):
        """Test that feature ranking table is saved correctly."""
        _, feature_cols = mock_data
        output_path = tmp_path / "ranking.csv"
        
        save_feature_ranking(mock_shap_values, feature_cols, output_path)
        
        assert output_path.exists(), "Feature ranking file was not created."
        
        df = pd.read_csv(output_path)
        assert 'feature' in df.columns, "Missing 'feature' column."
        assert 'mean_abs_shap_value' in df.columns, "Missing 'mean_abs_shap_value' column."
        assert len(df) == len(feature_cols), "Incorrect number of features."
        assert df['mean_abs_shap_value'].isna().sum() == 0, "Contains NaN values."

    def test_plot_shap_summary(self, mock_data, mock_shap_values, tmp_path):
        """Test that SHAP summary plot is generated."""
        X, _ = mock_data
        output_path = tmp_path / "shap_summary.png"
        
        plot_shap_summary(mock_shap_values, X, output_path)
        
        assert output_path.exists(), "SHAP summary plot was not created."
        assert output_path.stat().st_size > 0, "SHAP summary plot is empty."

    def test_calculate_cv_stability(self, mock_data):
        """Test CV stability calculation."""
        X, y = mock_data
        
        # Use a small sample size for speed in test
        stability_df = calculate_cv_stability(X, y, n_splits=3)
        
        assert 'feature' in stability_df.columns, "Missing 'feature' column."
        assert 'cv_stability_score' in stability_df.columns, "Missing 'cv_stability_score' column."
        assert len(stability_df) == len(X.columns), "Incorrect number of features in stability report."
        assert stability_df['cv_stability_score'].isna().sum() == 0, "Contains NaN CV scores."