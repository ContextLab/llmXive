"""
Unit tests for the regression model selector (T063).
"""

from __future__ import annotations

import pandas as pd
import pytest

from analysis.select_regression import select_regression

@pytest.fixture
def confounders_df():
    """Simple confounder matrix used across tests."""
    return pd.DataFrame(
        {
            "age": [30, 45, 22, 38],
            "gender": [0, 1, 0, 1],  # 0 = female, 1 = male (example)
            "baseline_severity": [2.1, 3.5, 1.8, 2.9],
            "prior_therapy": [0, 1, 0, 1],
        }
    )

def test_binary_outcome_selection(confounders_df):
    y = pd.Series([0, 1, 0, 1])
    model_type, model = select_regression(y, confounders_df)
    assert model_type == "logistic"
    # LogisticRegression from scikit‑learn has predict_proba method
    assert hasattr(model, "predict_proba")

def test_proportion_outcome_selection(confounders_df):
    y = pd.Series([0.2, 0.55, 0.73, 0.41])
    model_type, model = select_regression(y, confounders_df)
    assert model_type == "beta"
    # statsmodels GLM results have 'family' attribute
    assert hasattr(model, "family")
    assert model.family.__class__.__name__ == "Beta"

def test_continuous_outcome_selection(confounders_df):
    y = pd.Series([10.5, 12.3, 9.8, 15.2])
    model_type, model = select_regression(y, confounders_df)
    assert model_type == "ols"
    # statsmodels OLS results have 'params' attribute
    assert hasattr(model, "params")
    # Ensure at least one coefficient (intercept) is present
    assert len(model.params) >= 1

def test_invalid_beta_values_raise():
    # Values at the boundary should raise an error for beta regression
    y = pd.Series([0.0, 0.5, 0.7, 1.0])
    X = pd.DataFrame(
        {
            "age": [30, 40, 25, 35],
            "gender": [0, 1, 0, 1],
            "baseline_severity": [2, 3, 1, 2],
            "prior_therapy": [0, 0, 1, 1],
        }
    )
    with pytest.raises(ValueError, match="Beta regression requires outcomes strictly between 0 and 1"):
        select_regression(y, X)