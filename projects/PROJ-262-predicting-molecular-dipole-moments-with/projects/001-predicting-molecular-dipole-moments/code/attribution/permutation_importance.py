"""
Permutation importance utilities for Random Forest models.

This module provides a thin wrapper around scikit‑learn's
``permutation_importance`` function, exposing a simple API that can be
used by integration tests and downstream pipelines.

The implementation is intentionally lightweight: it trains no models,
performs no I/O, and relies only on NumPy and scikit‑learn, which are
already part of the project's dependency set.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.inspection import permutation_importance
from sklearn.base import BaseEstimator

def compute_permutation_importance(
    model: BaseEstimator,
    X: np.ndarray,
    y: np.ndarray,
    metric: str = "neg_mean_absolute_error",
    n_repeats: int = 5,
    random_state: int = 0,
) -> np.ndarray:
    """
    Compute the mean permutation importance for each feature.

    Parameters
    ----------
    model : BaseEstimator
        A fitted scikit‑learn estimator supporting ``predict``.
    X : np.ndarray
        Feature matrix (shape ``[n_samples, n_features]``).
    y : np.ndarray
        Target vector (shape ``[n_samples]``).
    metric : str, optional
        Scoring metric understood by scikit‑learn (default
        ``"neg_mean_absolute_error"``).
    n_repeats : int, optional
        Number of times to permute a feature. Default is 5.
    random_state : int, optional
        Random seed for reproducibility.

    Returns
    -------
    np.ndarray
        Array of shape ``[n_features]`` containing the mean importance
        values for each feature.
    """
    # scikit‑learn expects ``X`` and ``y`` to be array‑like; we accept
    # NumPy arrays directly.
    result = permutation_importance(
        estimator=model,
        X=X,
        y=y,
        scoring=metric,
        n_repeats=n_repeats,
        random_state=random_state,
    )
    # ``importances_mean`` is a 1‑D array with length equal to the
    # number of features.
    return np.asarray(result.importances_mean)
