"""
Metric utilities used by the training scripts.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

def mae(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Mean Absolute Error."""
    if len(y_true) == 0:
        raise ValueError('Empty input to mae')
    return sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)

def rmse(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Root Mean Squared Error."""
    if len(y_true) == 0:
        raise ValueError('Empty input to rmse')
    mse = sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true)
    return math.sqrt(mse)