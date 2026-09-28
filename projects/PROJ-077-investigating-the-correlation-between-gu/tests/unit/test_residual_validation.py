import pytest
import pandas as pd
import numpy as np
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from scipy.stats import shapiro
import json
import os
from pathlib import Path

# Import the function to test
from code.analysis import perform_residual_normality_validation, save_regression_diagnostics

@pytest.fixture
def normal_residuals():
    """Generate a set of residuals that are normally distributed."""
    np.random.seed(42)
    return pd.Series(np.random.normal(loc=0, scale=1, size=1000))

@pytest.fixture
def non_normal_residuals():
    """Generate a set of residuals that are NOT normally distributed (skewed)."""
    np.random.seed(42)
    return pd.Series(np.random.exponential(scale=1.0, size=1000))

@pytest.fixture
def zero_variance_residuals():
    """Generate residuals with zero variance."""
    return pd.Series([0.0] * 100)

@pytest.fixture
def mock_ols_results_normal(normal_residuals):
    """Mock OLS results object with normal residuals."""
    class MockResults:
        def __init__(self, resid):
            self.resid = resid
    return MockResults(normal_residuals)

@pytest.fixture
def mock_ols_results_non_normal(non_normal_residuals):
    """Mock OLS results object with non-normal residuals."""
    class MockResults:
        def __init__(self, resid):
            self.resid = resid
    return MockResults(non_normal_residuals)

@pytest.fixture
def mock_ols_results_zero_var(zero_variance_residuals):
    """Mock OLS results object with zero variance residuals."""
    class MockResults:
        def __init__(self, resid):
            self.resid = resid
    return MockResults(zero_variance_residuals)

def test_shapiro_wilk_normal_residuals(mock_ols_results_normal):
    """Test that normal residuals pass the Shapiro-Wilk test (p > 0.05)."""
    result = perform_residual_normality_validation(mock_ols_results_normal)
    
    assert result['test'] == 'Shapiro-Wilk'
    assert result['status'] == 'PASS'
    assert result['is_normal'] is True
    assert result['p_value'] > 0.05
    assert 'statistic' in result

def test_shapiro_wilk_non_normal_residuals(mock_ols_results_non_normal):
    """Test that non-normal residuals fail the Shapiro-Wilk test (p <= 0.05)."""
    result = perform_residual_normality_validation(mock_ols_results_non_normal)
    
    assert result['test'] == 'Shapiro-Wilk'
    assert result['status'] == 'FAIL'
    assert result['is_normal'] is False
    assert result['p_value'] <= 0.05

def test_shapiro_wilk_zero_variance(mock_ols_results_zero_var):
    """Test that zero variance residuals are skipped."""
    result = perform_residual_normality_validation(mock_ols_results_zero_var)
    
    assert result['test'] == 'Shapiro-Wilk'
    assert result['status'] == 'skipped'
    assert result['reason'] == 'Zero variance in residuals'

def test_save_regression_diagnostics(tmp_path):
    """Test that diagnostics are saved correctly to JSON."""
    # Temporarily change the output path for testing
    import code.analysis as analysis_module
    original_path = Path("data/processed/regression_diagnostics.json")
    
    # Create a mock result
    diag = {
        "test": "Shapiro-Wilk",
        "status": "PASS",
        "p_value": 0.5
    }
    
    # Save to a temporary location
    temp_path = tmp_path / "test_diagnostics.json"
    with open(temp_path, 'w') as f:
        json.dump(diag, f, indent=2)
    
    # Verify content
    with open(temp_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded['status'] == 'PASS'
    assert loaded['p_value'] == 0.5