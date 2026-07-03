import pytest
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.regression import (
    check_normality,
    check_homoscedasticity,
    check_collinearity,
    validate_model_assumptions,
    run_assumption_validation
)

@pytest.fixture
def sample_data():
    """Create sample data for testing assumption validation."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        "pre_self_esteem": np.random.normal(50, 10, n),
        "avatar_condition": np.random.choice([0, 1], n),
        "comparison_tendency": np.random.normal(3, 1, n),
        "post_self_esteem": np.random.normal(52, 10, n)
    })
    return data

@pytest.fixture
def fitted_model(sample_data):
    """Fit a simple OLS model for testing."""
    formula = "post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency"
    model = ols(formula, data=sample_data).fit()
    return model

def test_shapiro_wilk_normal_pass(fitted_model):
    """Test Shapiro-Wilk test on normally distributed residuals."""
    residuals = pd.Series(fitted_model.resid)
    result = check_normality(residuals)
    
    assert result["test"] == "Shapiro-Wilk"
    assert "statistic" in result
    assert "p_value" in result
    assert result["passed"] in [True, False]
    assert result["message"] is not None

def test_shapiro_wilk_insufficient_data():
    """Test Shapiro-Wilk with insufficient data."""
    residuals = pd.Series([1.0, 2.0])
    result = check_normality(residuals)
    
    assert result["passed"] == False
    assert "Insufficient data" in result["message"]

def test_breusch_pagan_homoscedasticity(fitted_model):
    """Test Breusch-Pagan test for homoscedasticity."""
    residuals = pd.Series(fitted_model.resid)
    predicted = pd.Series(fitted_model.fittedvalues)
    
    result = check_homoscedasticity(fitted_model, residuals, predicted)
    
    assert result["test"] == "Breusch-Pagan"
    assert "statistic" in result
    assert "p_value" in result
    assert result["passed"] in [True, False]
    assert result["message"] is not None

def test_vif_collinearity_low(fitted_model):
    """Test VIF calculation with low collinearity."""
    result = check_collinearity(fitted_model)
    
    assert "results" in result
    assert "max_vif" in result
    assert "threshold" in result
    assert result["threshold"] == 5.0
    assert isinstance(result["results"], list)
    assert len(result["results"]) > 0
    
    for item in result["results"]:
        assert "feature" in item
        assert "vif" in item
        assert "high_collinearity" in item

def test_vif_collinearity_high():
    """Test VIF detection with high collinearity."""
    np.random.seed(42)
    n = 50
    # Create highly correlated features
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.99 + np.random.normal(0, 0.1, n)  # Highly correlated
    y = x1 + x2 + np.random.normal(0, 0.1, n)
    
    data = pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2
    })
    
    model = ols("y ~ x1 + x2", data=data).fit()
    result = check_collinearity(model)
    
    # At least one feature should have high VIF
    high_vif_count = sum(1 for r in result["results"] if r["high_collinearity"])
    assert high_vif_count >= 1

def test_validate_model_assumptions(fitted_model):
    """Test full model assumption validation."""
    residuals = pd.Series(fitted_model.resid)
    predicted = pd.Series(fitted_model.fittedvalues)
    
    results = validate_model_assumptions(fitted_model, residuals, predicted)
    
    assert "normality" in results
    assert "homoscedasticity" in results
    assert "collinearity" in results
    assert "all_assumptions_met" in results
    assert "warnings" in results
    assert isinstance(results["warnings"], list)

def test_run_assumption_validation(fitted_model, sample_data):
    """Test the full assumption validation pipeline."""
    results = run_assumption_validation(sample_data, fitted_model)
    
    assert "normality" in results
    assert "homoscedasticity" in results
    assert "collinearity" in results
    assert "all_assumptions_met" in results

def test_assumption_validation_integration(fitted_model):
    """Integration test ensuring all components work together."""
    residuals = pd.Series(fitted_model.resid)
    predicted = pd.Series(fitted_model.fittedvalues)
    
    # Run all tests
    norm = check_normality(residuals)
    homo = check_homoscedasticity(fitted_model, residuals, predicted)
    coll = check_collinearity(fitted_model)
    full = validate_model_assumptions(fitted_model, residuals, predicted)
    
    # Verify consistency
    assert full["normality"]["test"] == norm["test"]
    assert full["homoscedasticity"]["test"] == homo["test"]
    assert "results" in full["collinearity"]
    assert full["all_assumptions_met"] == (norm["passed"] and homo["passed"] and coll["passed"])
