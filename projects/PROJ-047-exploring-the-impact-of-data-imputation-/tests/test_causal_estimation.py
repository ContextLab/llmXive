"""
Tests for causal estimation functions (IPW and PSM).
"""
import pytest
import pandas as pd
import numpy as np
from code.analysis.causal_estimation import estimate_ate_ipw, estimate_ate_psm
from code.analysis.entities import CausalEstimate


@pytest.fixture
def sample_data():
    """Create a simple dataset for testing."""
    np.random.seed(42)
    n = 100
    # Generate covariates
    X1 = np.random.normal(0, 1, n)
    X2 = np.random.normal(0, 1, n)
    # Propensity score
    propensity = 1 / (1 + np.exp(-(0.5 * X1 + 0.3 * X2)))
    # Treatment assignment
    T = (np.random.uniform(0, 1, n) < propensity).astype(int)
    # Outcome with true ATE = 2.0
    Y = 1.0 + 2.0 * T + 0.5 * X1 + 0.3 * X2 + np.random.normal(0, 0.5, n)

    return pd.DataFrame({
        'treatment': T,
        'outcome': Y,
        'X1': X1,
        'X2': X2
    })


def test_ipw_returns_valid_float(sample_data):
    """Test that IPW returns valid float ATE."""
    result = estimate_ate_ipw(
        sample_data,
        treatment_col='treatment',
        outcome_col='outcome',
        covariate_cols=['X1', 'X2']
    )

    assert isinstance(result, CausalEstimate)
    assert isinstance(result.ate, float)
    assert isinstance(result.standard_error, float)
    assert isinstance(result.ci_lower, float)
    assert isinstance(result.ci_upper, float)
    assert not np.isnan(result.ate)
    assert result.standard_error > 0


def test_psm_returns_valid_float(sample_data):
    """Test that PSM returns valid float ATE."""
    result = estimate_ate_psm(
        sample_data,
        treatment_col='treatment',
        outcome_col='outcome',
        covariate_cols=['X1', 'X2']
    )

    assert isinstance(result, CausalEstimate)
    assert isinstance(result.ate, float)
    assert isinstance(result.standard_error, float)
    assert isinstance(result.ci_lower, float)
    assert isinstance(result.ci_upper, float)
    assert not np.isnan(result.ate)
    assert result.standard_error > 0


def test_ipw_ci_contains_ate(sample_data):
    """Test that the CI bounds are reasonable (lower < ate < upper)."""
    result = estimate_ate_ipw(
        sample_data,
        treatment_col='treatment',
        outcome_col='outcome',
        covariate_cols=['X1', 'X2']
    )

    assert result.ci_lower < result.ate < result.ci_upper


def test_psm_ci_contains_ate(sample_data):
    """Test that the CI bounds are reasonable (lower < ate < upper)."""
    result = estimate_ate_psm(
        sample_data,
        treatment_col='treatment',
        outcome_col='outcome',
        covariate_cols=['X1', 'X2']
    )

    assert result.ci_lower < result.ate < result.ci_upper


def test_ipw_with_no_covariates(sample_data):
    """Test IPW works with no covariates."""
    result = estimate_ate_ipw(
        sample_data,
        treatment_col='treatment',
        outcome_col='outcome',
        covariate_cols=[]
    )

    assert isinstance(result, CausalEstimate)
    assert not np.isnan(result.ate)


def test_psm_with_no_covariates(sample_data):
    """Test PSM works with no covariates."""
    result = estimate_ate_psm(
        sample_data,
        treatment_col='treatment',
        outcome_col='outcome',
        covariate_cols=[]
    )

    assert isinstance(result, CausalEstimate)
    assert not np.isnan(result.ate)


def test_ipw_raises_on_nan(sample_data):
    """Test that IPW raises ValueError on NaN data."""
    data_with_nan = sample_data.copy()
    data_with_nan.loc[0, 'treatment'] = np.nan

    with pytest.raises(ValueError, match="NaN"):
        estimate_ate_ipw(
            data_with_nan,
            treatment_col='treatment',
            outcome_col='outcome',
            covariate_cols=['X1', 'X2']
        )


def test_psm_raises_on_nan(sample_data):
    """Test that PSM raises ValueError on NaN data."""
    data_with_nan = sample_data.copy()
    data_with_nan.loc[0, 'outcome'] = np.nan

    with pytest.raises(ValueError, match="NaN"):
        estimate_ate_psm(
            data_with_nan,
            treatment_col='treatment',
            outcome_col='outcome',
            covariate_cols=['X1', 'X2']
        )