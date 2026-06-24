"""
Training utilities for the Random Forest baseline model.

The primary entry point is ``train_random_forest`` which fits a
``RandomForestRegressor`` on the supplied data and returns the trained
model together with common regression metrics (MAE and RMSE).

This module is deliberately lightweight – it does not perform any I/O
itself; callers are expected to provide NumPy arrays or Pandas objects.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from typing import Dict, Any

__all__ = ["train_random_forest"]


def train_random_forest(
    X: np.ndarray | Any,
    y: np.ndarray | Any,
    *,
    random_state: int = 0,
    n_estimators: int = 100,
) -> Dict[str, Any]:
    """
    Fit a Random Forest regressor and compute MAE / RMSE on the training data.

    Parameters
    ----------
    X : array‑like
        Feature matrix of shape (n_samples, n_features).
    y : array‑like
        Target vector of shape (n_samples,).
    random_state : int, optional
        Seed for reproducibility. Default is ``0``.
    n_estimators : int, optional
        Number of trees in the forest. Default is ``100``.

    Returns
    -------
    dict
        Dictionary containing the trained model (key ``model``) and the
        computed metrics (keys ``mae`` and ``rmse``).
    """
    # Convert inputs to NumPy arrays if they are not already
    X_arr = np.asarray(X)
    y_arr = np.asarray(y)

    # Initialise and train the model
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=1,  # respect the 2‑CPU‑core constraint elsewhere in the project
    )
    model.fit(X_arr, y_arr)

    # Predict on the training set (integration test uses the same data)
    y_pred = model.predict(X_arr)

    # Compute metrics
    mae = mean_absolute_error(y_arr, y_pred)
    rmse = mean_squared_error(y_arr, y_pred, squared=False)

    return {"model": model, "mae": mae, "rmse": rmse}
