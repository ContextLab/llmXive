"""
Alternative model training module.

Trains a Random Forest classifier, computes its ROC‑AUC on the training data,
and validates that the performance is within a configurable tolerance of the
primary Logistic Regression model's ROC‑AUC.

The primary model is trained on the same data using :func:`train_primary`
from ``code/modeling/train_primary.py``. If the difference between the two
AUC scores exceeds the tolerance (default 0.05), an :class:`AssertionError`
is raised.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

# Import the primary‑model trainer for on‑the‑fly comparison.
from modeling.train_primary import train_primary

def train_alternative(
    X: np.ndarray,
    y: np.ndarray,
    *,
    n_estimators: int = 200,
    max_depth: int = 10,
    random_state: int = 0,
    n_jobs: int = -1,
    tolerance: float = 0.05,
) -> Tuple[RandomForestClassifier, float]:
    """
    Train a Random Forest classifier and assert its ROC‑AUC is close to that
    of the primary Logistic Regression model.

    Parameters
    ----------
    X : np.ndarray
        Feature matrix.
    y : np.ndarray
        Binary target vector.
    n_estimators : int, optional
        Number of trees in the forest. Default is 200 (a “sufficient” number).
    max_depth : int, optional
        Maximum depth of each tree. Default is 10.
    random_state : int, optional
        Seed for reproducibility. Default is 0.
    n_jobs : int, optional
        Parallelism for tree building. ``-1`` uses all processors.
    tolerance : float, optional
        Maximum allowed absolute difference between the alternative model's
        ROC‑AUC and the primary model's ROC‑AUC. Default is 0.05.

    Returns
    -------
    model : RandomForestClassifier
        The fitted Random Forest model.
    auc : float
        ROC‑AUC of the alternative model evaluated on the training data.

    Raises
    ------
    AssertionError
        If the absolute difference between the alternative and primary AUC
        exceeds ``tolerance``.
    """
    # ------------------------------------------------------------------
    # 1. Fit the alternative Random Forest model.
    # ------------------------------------------------------------------
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=n_jobs,
    )
    model.fit(X, y)

    # Predict probabilities for the positive class.
    probas = model.predict_proba(X)[:, 1]
    alt_auc = roc_auc_score(y, probas)

    # ------------------------------------------------------------------
    # 2. Compute primary model ROC‑AUC on the same data for comparison.
    # ------------------------------------------------------------------
    _, primary_auc = train_primary(X, y)

    # ------------------------------------------------------------------
    # 3. Validate the performance gap.
    # ------------------------------------------------------------------
    diff = abs(alt_auc - primary_auc)
    if diff > tolerance:
        raise AssertionError(
            f"Alternative model ROC‑AUC ({alt_auc:.4f}) differs from primary "
            f"model ROC‑AUC ({primary_auc:.4f}) by {diff:.4f}, which exceeds "
            f"the allowed tolerance of {tolerance:.4f}."
        )

    return model, alt_auc