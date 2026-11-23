import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analyze import (
    calculate_correlation_matrix,
    calculate_p_values,
    benjamini_hochberg_fdr,
    calculate_vif,
    bootstrap_feature_importance,
    verify_stability_metrics,
    save_stability_metrics
)
from sklearn.ensemble import GradientBoostingRegressor

class TestCorrelationAnalysis:
    def test_correlation_matrix_calculation(self):
        """Test that correlation matrix is calculated correctly."""
        # Create sample data
        np.random.seed(42)
        df = pd.DataFrame({
            'A': np.random.randn(100),
            'B': np.random.randn(100),
            'C': np.random.randn(100)
        })
        
        # Calculate correlation matrix
        result = calculate_correlation_matrix(df)
        
        # Verify result is a DataFrame
        assert isinstance(result, pd.DataFrame)
        assert result.shape[0] == 3
        assert result.shape[1] == 6  # 3 original + 3 suffixes
        
    def test_p_values_calculation(self):
        """Test that p-values are calculated correctly."""
        np.random.seed(42)
        df = pd.DataFrame({
            'A': np.random.randn(100),
            'B': np.random.randn(100),
            'C': np.random.randn(100)
        })
        
        p_vals = calculate_p_values(df)
        
        assert isinstance(p_vals, pd.DataFrame)
        assert p_vals.shape == (3, 3)
        # Diagonal should be 0.0
        assert all(p_vals.values[i, i] == 0.0 for i in range(3))

class TestFDRCorrection:
    def test_fdr_correction(self):
        """Test Benjamini-Hochberg FDR correction."""
        np.random.seed(42)
        p_values = pd.DataFrame({
            'A': [0.01, 0.05, 0.1, 0.2],
            'B': [0.02, 0.06, 0.12, 0.25],
            'C': [0.03, 0.07, 0.15, 0.3]
        })
        
        fdr_result = benjamini_hochberg_fdr(p_values)
        
        assert isinstance(fdr_result, pd.DataFrame)
        assert fdr_result.shape == p_values.shape
        # FDR adjusted values should be >= original values
        assert all(fdr_result.values >= p_values.values)

class TestVIF:
    def test_vif_calculation(self):
        """Test VIF calculation."""
        np.random.seed(42)
        df = pd.DataFrame({
            'A': np.random.randn(100),
            'B': np.random.randn(100),
            'C': np.random.randn(100)
        })
        
        vif_data = calculate_vif(df)
        
        assert isinstance(vif_data, dict)
        assert len(vif_data) == 3
        # VIF should be >= 1
        for vif_val in vif_data.values():
            assert vif_val >= 1.0

class TestBootstrapStability:
    def test_bootstrap_feature_importance(self):
        """Test bootstrap feature importance calculation."""
        np.random.seed(42)
        n_samples = 200
        n_features = 3
        
        X = pd.DataFrame({
            f'feat_{i}': np.random.randn(n_samples) for i in range(n_features)
        })
        y = pd.Series(np.random.randn(n_samples))
        
        # Create a simple model
        model = GradientBoostingRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        # Run bootstrap (use fewer samples for speed in tests)
        results = bootstrap_feature_importance(model, X, y, n_resamples=50)
        
        assert isinstance(results, dict)
        assert 'ci_lower' in results
        assert 'ci_upper' in results
        assert 'feature_importances' in results
        assert 'feature_names' in results
        assert len(results['ci_lower']) == n_features
        assert len(results['ci_upper']) == n_features
        
        # CI bounds should be valid (lower <= upper)
        for lower, upper in zip(results['ci_lower'], results['ci_upper']):
            assert lower <= upper

class TestStabilityMetricsVerification:
    def test_verify_stability_metrics_success(self, tmp_path):
        """Test verification of valid stability metrics file."""
        metrics = {
            'ci_lower': [0.1, 0.2, 0.3],
            'ci_upper': [0.4, 0.5, 0.6],
            'feature_importances': [0.2, 0.3, 0.4],
            'feature_names': ['A', 'B', 'C'],
            'n_resamples': 1000
        }
        
        output_path = tmp_path / "stability_metrics.json"
        save_stability_metrics(metrics, output_path)
        
        assert verify_stability_metrics(output_path)

    def test_verify_stability_metrics_missing_keys(self, tmp_path):
        """Test verification fails with missing keys."""
        metrics = {
            'ci_lower': [0.1, 0.2],
            # Missing ci_upper, feature_importances, etc.
        }
        
        output_path = tmp_path / "stability_metrics.json"
        save_stability_metrics(metrics, output_path)
        
        assert not verify_stability_metrics(output_path)

    def test_verify_stability_metrics_file_not_found(self):
        """Test verification fails when file doesn't exist."""
        assert not verify_stability_metrics(Path("nonexistent.json"))
