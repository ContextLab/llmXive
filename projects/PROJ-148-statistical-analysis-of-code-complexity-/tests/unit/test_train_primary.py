"""
Unit tests for the primary logistic regression training function.
"""

import numpy as np
import pytest

from modeling.train_primary import train_primary

@pytest.fixture
def synthetic_data():
    """Create a tiny synthetic dataset where a linear separator exists."""
    rng = np.random.default_rng(42)
    # Feature 0 is informative, feature 1 is noise.
    X = rng.normal(size=(100, 2))
    X[:, 0] = X[:, 0] * 5  # amplify signal
    y = (X[:, 0] > 0).astype(int)
    return X, y

def test_train_primary_returns_model_and_iteration_count(synthetic_data):
    X, y = synthetic_data
    model, n_iter = train_primary(X, y)

    # Basic type checks.
    from sklearn.linear_model import LogisticRegression
    assert isinstance(model, LogisticRegression)
    assert isinstance(n_iter, int)

    # Iteration count must respect the task constraint.
    assert n_iter <= 100

    # At least one coefficient should be non‑zero.
    assert np.any(np.abs(model.coef_) > 1e-8)