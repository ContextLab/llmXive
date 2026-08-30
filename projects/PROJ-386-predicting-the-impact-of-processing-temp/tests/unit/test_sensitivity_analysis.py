import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

# We need to mock the dependencies that load files
# Since we are unit testing the logic, we will mock the file loading functions
# and pass in mock data directly to the helper functions.

from code.analysis.diagnostics import (
    get_feature_importance_stability,
    check_confounder_r2_delta
)

@pytest.fixture
def mock_model():
    """Create a simple RF model with known feature importances."""
    # Create a dummy dataset
    X = np.random.rand(100, 5)
    y = np.random.rand(100)
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    return model

@pytest.fixture
def mock_dataframe():
    """Create a mock DataFrame with feature names."""
    return pd.DataFrame({
        'feature_A': np.random.rand(100),
        'feature_B': np.random.rand(100),
        'feature_C': np.random.rand(100),
        'feature_D': np.random.rand(100),
        'feature_E': np.random.rand(100),
    })

@pytest.fixture
def mock_y():
    return np.random.rand(100)

def test_threshold_sweep_stability(mock_model, mock_dataframe, mock_y):
    """Test that stability calculation works correctly."""
    thresholds = [0.0, 0.05, 0.1]
    result = get_feature_importance_stability(mock_model, mock_dataframe, mock_y, thresholds)
    
    assert "threshold_sweep_results" in result
    assert "stable_terms" in result
    assert "stability_pct" in result
    
    # Check that we have results for each threshold
    assert len(result["threshold_sweep_results"]) == len(thresholds)
    
    # Check that stability is a percentage (0-100)
    assert 0.0 <= result["stability_pct"] <= 100.0

def test_confounder_check_no_proxies(mock_model, mock_dataframe, mock_y):
    """Test confounder check when no proxy variables exist."""
    collinearity_report = {"flagged_pairs": []}
    result = check_confounder_r2_delta(mock_model, mock_dataframe, mock_y, collinearity_report)
    
    assert result["status"] == "no_proxies"
    assert "No proxy variables available" in result["message"]
    assert result["r2_delta"] is None

def test_confounder_check_with_proxies(mock_model, mock_y):
    """Test confounder check when proxy variables exist."""
    # Create a DataFrame with a proxy variable
    X_with_proxy = pd.DataFrame({
        'feature_A': np.random.rand(100),
        'feature_B': np.random.rand(100),
        'strain_rate': np.random.rand(100), # Proxy
    })
    
    # Retrain model on this data so it's consistent
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_with_proxy, mock_y)
    
    collinearity_report = {"flagged_pairs": []}
    result = check_confounder_r2_delta(model, X_with_proxy, mock_y, collinearity_report)
    
    assert result["status"] == "completed"
    assert result["r2_delta"] is not None
    assert "strain_rate" in result["proxies_removed"]
    
    # R2 delta should be a reasonable number
    assert isinstance(result["r2_delta"], float)

def test_confounder_check_empty_after_removal(mock_model, mock_y):
    """Test behavior when removing proxies leaves no features."""
    # Create a DataFrame with only a proxy variable
    X_only_proxy = pd.DataFrame({
        'strain_rate': np.random.rand(100),
    })
    
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_only_proxy, mock_y)
    
    collinearity_report = {"flagged_pairs": []}
    result = check_confounder_r2_delta(model, X_only_proxy, mock_y, collinearity_report)
    
    assert result["status"] == "error"
    assert "Removing proxies leaves no features" in result["message"]
    assert result["r2_delta"] is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])