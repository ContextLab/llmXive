"""
Primary model training module.

Trains an L1‑regularized logistic regression model using scikit‑learn.
The function returns the fitted model and the number of iterations performed.
It also enforces that the training completes within 100 iterations and that
the resulting model has at least one non‑zero coefficient, as required by
task T020.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression

def train_primary(X: np.ndarray, y: np.ndarray) -> Tuple[LogisticRegression, int]:
    """
    Train a logistic regression model with L1 regularisation.

    Parameters
    ----------
    X: np.ndarray
        Feature matrix (shape: n_samples, n_features).
    y: np.ndarray
        Binary target vector (shape: n_samples,).

    Returns
    -------
    model: LogisticRegression
        Fitted logistic regression model.
    n_iter: int
        Number of iterations taken by the solver (should be ≤ 100).

    Raises
    ------
    AssertionError
        If the solver exceeds 100 iterations or if the fitted model
        contains only zero coefficients.
    """
    # Using saga solver which supports L1 penalty.
    model = LogisticRegression(
        penalty="l1",
        solver="saga",
        max_iter=100,
        C=1.0,
        random_state=42,
    )
    model.fit(X, y)

    # ``n_iter_`` is an array (one entry per class); we take the maximum.
    n_iter = int(model.n_iter_.max()) if hasattr(model, "n_iter_") else 0

    # Enforce the iteration limit required by the task.
    assert n_iter <= 100, f"Training exceeded 100 iterations (got {n_iter})."

    # Ensure at least one coefficient is non‑zero (within a tolerance).
    coef = model.coef_
    non_zero = np.any(np.abs(coef) > 1e-8)
    assert non_zero, "All model coefficients are zero; expected at least one non‑zero."

    return model, n_iter