"""
Metric utilities for regression tasks.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

def mae(y_true: Sequence[float] | Iterable[float], y_pred: Sequence[float] | Iterable[float]) -> float:
    """Mean Absolute Error."""
    y_true = list(y_true)
    y_pred = list(y_pred)
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    return sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)

def rmse(y_true: Sequence[float] | Iterable[float], y_pred: Sequence[float] | Iterable[float]) -> float:
    """Root Mean Squared Error."""
    y_true = list(y_true)
    y_pred = list(y_pred)
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    mse = sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true)
    return math.sqrt(mse)