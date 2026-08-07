"""
Unit tests for regression model constraints in src/analysis/regression.py.

This module verifies that the regression model:
1. Excludes Max_ACF_Lag1 as a predictor
2. Excludes Spectral_Density_Peak_Ratio as a predictor
3. Includes True_Hurst (or Estimated_Hurst), Log_N_eff, and their interaction
4. Calculates VIF for all predictors
"""
import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import tempfile
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.regression import (
    fit_regression_model,
    validate_predictors,
    calculate_vif,
    REGRESSION_EXCLUDED_PREDICTORS,
    REGRESSION_REQUIRED_PREDICTORS
)
from src.utils.config import set_seed

# Set random seed for reproducibility
set_seed(42)

@pytest.fixture
def sample_regression_data():
    """Create sample data for regression testing."""
    np.random.seed(42)
    n_samples = 1000
    
    # Simulate realistic data
    true_hurst = np.random.uniform(0.5, 0.95, n_samples)
    log_n_eff = np.random.uniform(2.0, 9.0, n_samples)
    
    # Create interaction term
    interaction = true_hurst * log_n_eff
    
    # Simulate rejection rate with some noise
    rejection_rate = (
        0.05 + 
        0.3 * true_hurst + 
        0.1 * log_n_eff + 
        0.15 * interaction +
        np.random.normal(0, 0.02, n_samples)
    )
    # Clip to valid range
    rejection_rate = np.clip(rejection_rate, 0.0, 1.0)
    
    df = pd.DataFrame({
        'True_Hurst': true_hurst,
        'Estimated_Hurst': true_hurst + np.random.normal(0, 0.01, n_samples),
        'Log_N_eff': log_n_eff,
        'Max_ACF_Lag1': np.random.uniform(0.1, 0.8, n_samples),  # Should be excluded
        'Spectral_Density_Peak_Ratio': np.random.uniform(0.5, 3.0, n_samples),  # Should be excluded
        'Rejection_Rate': rejection_rate
    })
    
    return df

@pytest.fixture
def invalid_predictors_data():
    """Create data with excluded predictors to test validation."""
    np.random.seed(42)
    n_samples = 100
    
    df = pd.DataFrame({
        'Max_ACF_Lag1': np.random.uniform(0.1, 0.8, n_samples),
        'Spectral_Density_Peak_Ratio': np.random.uniform(0.5, 3.0, n_samples),
        'Rejection_Rate': np.random.uniform(0.0, 1.0, n_samples)
    })
    
    return df

class TestRegressionConstraints:
    """Test suite for regression model constraints."""
    
    def test_excluded_predictors_constant(self):
        """Test that excluded predictors are properly defined."""
        assert 'Max_ACF_Lag1' in REGRESSION_EXCLUDED_PREDICTORS
        assert 'Spectral_Density_Peak_Ratio' in REGRESSION_EXCLUDED_PREDICTORS
        assert len(REGRESSION_EXCLUDED_PREDICTORS) >= 2
    
    def test_required_predictors_constant(self):
        """Test that required predictors are properly defined."""
        # At minimum, we need H and log(N_eff) with interaction
        assert any('Hurst' in p for p in REGRESSION_REQUIRED_PREDICTORS)
        assert any('N_eff' in p for p in REGRESSION_REQUIRED_PREDICTORS)
    
    def test_validate_predictors_rejects_max_acf(self):
        """Test that validation fails when Max_ACF_Lag1 is included."""
        # Create a dataframe with Max_ACF_Lag1
        df = pd.DataFrame({
            'Max_ACF_Lag1': [0.5],
            'Rejection_Rate': [0.1]
        })
        
        # This should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            validate_predictors(df, target_col='Rejection_Rate')
        
        assert 'Max_ACF_Lag1' in str(exc_info.value)
        assert 'excluded' in str(exc_info.value).lower()
    
    def test_validate_predictors_rejects_spectral_density(self):
        """Test that validation fails when Spectral_Density_Peak_Ratio is included."""
        df = pd.DataFrame({
            'Spectral_Density_Peak_Ratio': [2.0],
            'Rejection_Rate': [0.1]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_predictors(df, target_col='Rejection_Rate')
        
        assert 'Spectral_Density_Peak_Ratio' in str(exc_info.value)
        assert 'excluded' in str(exc_info.value).lower()
    
    def test_validate_predictors_passes_valid_model(self, sample_regression_data):
        """Test that validation passes with valid predictors."""
        # This should not raise any exception
        try:
            validate_predictors(sample_regression_data, target_col='Rejection_Rate')
        except ValueError as e:
            pytest.fail(f"Validation failed unexpectedly: {e}")
    
    def test_fit_regression_model_excludes_max_acf(self, sample_regression_data):
        """Test that the fitted model does not include Max_ACF_Lag1."""
        # Fit the model
        result = fit_regression_model(
            df=sample_regression_data,
            target_col='Rejection_Rate'
        )
        
        # Check that Max_ACF_Lag1 is not in the model coefficients
        assert 'Max_ACF_Lag1' not in result['coefficients'].index
        assert 'Max_ACF_Lag1' not in result['model'].params.index
    
    def test_fit_regression_model_excludes_spectral_density(self, sample_regression_data):
        """Test that the fitted model does not include Spectral_Density_Peak_Ratio."""
        result = fit_regression_model(
            df=sample_regression_data,
            target_col='Rejection_Rate'
        )
        
        assert 'Spectral_Density_Peak_Ratio' not in result['coefficients'].index
        assert 'Spectral_Density_Peak_Ratio' not in result['model'].params.index
    
    def test_fit_regression_model_includes_hurst(self, sample_regression_data):
        """Test that the fitted model includes Hurst exponent."""
        result = fit_regression_model(
            df=sample_regression_data,
            target_col='Rejection_Rate'
        )
        
        # Check for either True_Hurst or Estimated_Hurst
        has_hurst = (
            'True_Hurst' in result['coefficients'].index or
            'Estimated_Hurst' in result['coefficients'].index
        )
        assert has_hurst, "Model must include Hurst exponent predictor"
    
    def test_fit_regression_model_includes_log_n_eff(self, sample_regression_data):
        """Test that the fitted model includes log(N_eff)."""
        result = fit_regression_model(
            df=sample_regression_data,
            target_col='Rejection_Rate'
        )
        
        assert 'Log_N_eff' in result['coefficients'].index
    
    def test_fit_regression_model_includes_interaction(self, sample_regression_data):
        """Test that the fitted model includes interaction term."""
        result = fit_regression_model(
            df=sample_regression_data,
            target_col='Rejection_Rate'
        )
        
        # Check for interaction term (H * log(N_eff))
        has_interaction = any(
            'interaction' in str(idx).lower() or 
            ('Hurst' in str(idx) and 'N_eff' in str(idx))
            for idx in result['coefficients'].index
        )
        assert has_interaction, "Model must include interaction term between H and log(N_eff)"
    
    def test_calculate_vif_returns_values(self, sample_regression_data):
        """Test that VIF calculation returns reasonable values."""
        # Prepare predictors (excluding target and excluded ones)
        predictors = [
            'True_Hurst', 
            'Log_N_eff', 
            'Max_ACF_Lag1',  # This will be filtered out
            'Spectral_Density_Peak_Ratio'  # This will be filtered out
        ]
        
        vif_results = calculate_vif(sample_regression_data, predictors)
        
        # VIF should be a dictionary with numeric values
        assert isinstance(vif_results, dict)
        assert len(vif_results) > 0
        for var, vif in vif_results.items():
            assert isinstance(vif, (int, float))
            assert vif >= 1.0  # VIF is always >= 1
    
    def test_regression_output_structure(self, sample_regression_data):
        """Test that regression output has required structure."""
        result = fit_regression_model(
            df=sample_regression_data,
            target_col='Rejection_Rate'
        )
        
        # Check required keys
        required_keys = ['model', 'coefficients', 'p_values', 'r_squared', 'vif', 'summary']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        # Check model type
        assert result['model'] is not None
        assert result['coefficients'] is not None
        assert len(result['coefficients']) > 0
    
    def test_regression_fails_on_missing_required_predictors(self):
        """Test that regression fails when required predictors are missing."""
        df = pd.DataFrame({
            'Rejection_Rate': [0.1, 0.2, 0.3],
            'Some_Other_Var': [1.0, 2.0, 3.0]
        })
        
        with pytest.raises(ValueError) as exc_info:
            fit_regression_model(df=df, target_col='Rejection_Rate')
        
        assert 'required' in str(exc_info.value).lower() or 'missing' in str(exc_info.value).lower()
    
    def test_regression_handles_multicollinearity_warning(self, sample_regression_data):
        """Test that regression handles potential multicollinearity."""
        # Create data with high correlation between predictors
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = x1 + np.random.normal(0, 0.1, n)  # Highly correlated
        
        df = pd.DataFrame({
            'True_Hurst': x1,
            'Log_N_eff': x2,
            'Rejection_Rate': 0.05 + 0.1 * x1 + 0.1 * x2 + np.random.normal(0, 0.01, n)
        })
        
        # Should still run but may have high VIF
        result = fit_regression_model(df=df, target_col='Rejection_Rate')
        
        # Check that VIF is calculated
        assert 'vif' in result
        assert len(result['vif']) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])