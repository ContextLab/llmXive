import pytest
import pandas as pd
import numpy as np
from src.models.fit import fit_gaussian_glm, fit_ridge_regression

class TestFitModels:
    @pytest.fixture
    def sample_data(self):
        """Create a small synthetic dataset for testing model fitting."""
        np.random.seed(42)
        n = 100
        data = {
            'feature_1': np.random.randn(n),
            'feature_2': np.random.randn(n),
            'feature_3': np.random.randn(n),
            'outcome_deviation': np.random.randn(n)
        }
        df = pd.DataFrame(data)
        X = df[['feature_1', 'feature_2', 'feature_3']]
        y = df['outcome_deviation']
        return X, y

    def test_fit_gaussian_glm(self, sample_data):
        """Test that Gaussian GLM fitting returns expected dictionary keys."""
        X, y = sample_data
        result = fit_gaussian_glm(X, y)
        
        assert isinstance(result, dict)
        assert result['model_type'] == 'Gaussian GLM'
        assert 'coefficients' in result
        assert 'p_values' in result
        assert 'aic' in result
        assert 'r_squared' in result
        assert 'converged' in result
        assert len(result['coefficients']) == len(X.columns) + 1  # +1 for intercept

    def test_fit_ridge_regression(self, sample_data):
        """Test that Ridge Regression fitting returns expected dictionary keys."""
        X, y = sample_data
        result = fit_ridge_regression(X, y)
        
        assert isinstance(result, dict)
        assert result['model_type'] == 'Ridge Regression'
        assert 'coefficients' in result
        assert 'r_squared' in result
        assert 'mse' in result
        assert 'alpha' in result
        assert len(result['coefficients']) == len(X.columns) + 1  # +1 for intercept

    def test_ridge_alpha_parameter(self, sample_data):
        """Test that changing alpha affects the model coefficients."""
        X, y = sample_data
        result_alpha_1 = fit_ridge_regression(X, y, alpha=1.0)
        result_alpha_10 = fit_ridge_regression(X, y, alpha=10.0)
        
        # Coefficients should differ due to regularization strength
        assert result_alpha_1['coefficients'] != result_alpha_10['coefficients']