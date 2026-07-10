import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Mock imports to avoid heavy dependencies in unit tests if needed,
# but here we test the logic of the functions directly if possible.
# Since shap and sklearn are heavy, we might mock them or run a small integration-like unit test.
# Given the constraint "Python must compile", we assume sklearn/shap are installed.

from visualize import (
    extract_lasso_coefficients, 
    plot_lasso_coefficients,
    plot_shap_summary,
    plot_feature_importance_from_shap
)
from sklearn.linear_model import Lasso
from sklearn.ensemble import RandomForestRegressor
import shap

@pytest.fixture
def mock_lasso_model():
    """Create a simple Lasso model with known coefficients."""
    np.random.seed(42)
    X = np.random.randn(100, 10)
    y = 2 * X[:, 0] + 3 * X[:, 1] + np.random.randn(100) * 0.1
    model = Lasso(alpha=0.1, fit_intercept=True)
    model.fit(X, y)
    return model

@pytest.fixture
def mock_rf_model():
    """Create a simple RandomForest model."""
    np.random.seed(42)
    X = np.random.randn(100, 10)
    y = X[:, 0] + X[:, 1] + np.random.randn(100) * 0.1
    model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=3)
    model.fit(X, y)
    return model

@pytest.fixture
def mock_feature_names():
    return [f"feat_{i}" for i in range(10)]

def test_extract_lasso_coefficients(mock_lasso_model, mock_feature_names):
    """Test that Lasso coefficients are extracted and sorted correctly."""
    df = extract_lasso_coefficients(mock_lasso_model, mock_feature_names)
    
    assert isinstance(df, pd.DataFrame)
    assert 'feature' in df.columns
    assert 'coefficient' in df.columns
    assert 'abs_coefficient' in df.columns
    assert len(df) == 10
    
    # Check sorting
    assert df['abs_coefficient'].is_monotonic_decreasing

def test_plot_lasso_coefficients(mock_lasso_model, mock_feature_names, tmp_path):
    """Test that Lasso coefficient plot is generated."""
    df = extract_lasso_coefficients(mock_lasso_model, mock_feature_names)
    output_path = tmp_path / "lasso_test.png"
    
    # This should not raise an error and should create the file
    plot_lasso_coefficients(df, output_path, max_features=5)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_plot_shap_summary(mock_rf_model, tmp_path):
    """Test SHAP summary plot generation."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(50, 10), columns=[f"feat_{i}" for i in range(10)])
    
    # Calculate SHAP values manually for the test to ensure we have valid data
    explainer = shap.TreeExplainer(mock_rf_model)
    shap_values = explainer.shap_values(X)
    
    shap_data = {
        "shap_values": shap_values,
        "X_sample": X,
        "feature_names": X.columns.tolist()
    }
    
    output_path = tmp_path / "shap_summary_test.png"
    
    # Should not raise
    plot_shap_summary(shap_data, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_plot_feature_importance_from_shap(mock_rf_model, tmp_path):
    """Test SHAP importance plot generation."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(50, 10), columns=[f"feat_{i}" for i in range(10)])
    
    explainer = shap.TreeExplainer(mock_rf_model)
    shap_values = explainer.shap_values(X)
    
    shap_data = {
        "shap_values": shap_values,
        "X_sample": X,
        "feature_names": X.columns.tolist()
    }
    
    output_path = tmp_path / "shap_importance_test.png"
    
    # Should not raise
    plot_feature_importance_from_shap(shap_data, output_path, max_features=5)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0