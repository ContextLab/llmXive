"""
Unit tests for confidence interval calculation logic.
"""

import pytest
import numpy as np
import pandas as pd
import statsmodels.api as sm
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.confidence_intervals import (
    calculate_prediction_intervals,
    calculate_confidence_intervals_mean,
    add_confidence_intervals_to_results
)


@pytest.fixture
def sample_ols_model():
    """Create a simple OLS model for testing."""
    np.random.seed(42)
    n = 100
    X = np.random.randn(n, 2)
    X = sm.add_constant(X)
    y = 2 * X[:, 0] + 3 * X[:, 1] + 1 + np.random.randn(n) * 0.5

    model = sm.OLS(y, X)
    results = model.fit()
    return results


@pytest.fixture
def sample_X_new():
    """Generate new feature data for prediction."""
    np.random.seed(123)
    return np.random.randn(10, 2)


def test_prediction_intervals_width(sample_ols_model, sample_X_new):
    """Test that prediction intervals are wider than confidence intervals."""
    pi_lower, pi_upper = calculate_prediction_intervals(sample_ols_model, sample_X_new)
    ci_lower, ci_upper = calculate_confidence_intervals_mean(sample_ols_model, sample_X_new)

    pi_width = pi_upper - pi_lower
    ci_width = ci_upper - ci_lower

    # Prediction intervals must be strictly wider than confidence intervals
    assert np.all(pi_width > ci_width), "Prediction intervals should be wider than confidence intervals."
    assert np.all(pi_width > 0), "Interval widths must be positive."


def test_confidence_intervals_symmetry(sample_ols_model, sample_X_new):
    """Test that confidence intervals are symmetric around the prediction."""
    y_hat = sample_ols_model.predict(sample_X_new)
    ci_lower, ci_upper = calculate_confidence_intervals_mean(sample_ols_model, sample_X_new)

    mid_point = (ci_lower + ci_upper) / 2
    assert np.allclose(mid_point, y_hat), "Confidence interval mid-point should equal prediction."


def test_add_confidence_intervals_to_results(sample_ols_model, sample_X_new):
    """Test adding intervals to a DataFrame."""
    # Create a mock DataFrame
    feature_names = ['const', 'var1', 'var2']
    df = pd.DataFrame(sample_X_new, columns=['var1', 'var2'])
    df['const'] = 1.0
    df['segregation_energy'] = sample_ols_model.predict(sample_X_new)

    df_out = add_confidence_intervals_to_results(
        df,
        sample_ols_model,
        feature_names,
        interval_type='prediction',
        alpha=0.05
    )

    assert 'prediction_lower' in df_out.columns
    assert 'prediction_upper' in df_out.columns
    assert len(df_out) == len(df)
    assert np.all(df_out['prediction_lower'] < df_out['prediction_upper'])