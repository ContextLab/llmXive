"""
Simple metric utilities for regression tasks.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

def mae(preds: Sequence[float] | Iterable[float], targets: Sequence[float] | Iterable[float]) -> float:
    """Mean Absolute Error."""
    preds = list(preds)
    targets = list(targets)
    if len(preds) != len(targets):
        raise ValueError("Length mismatch between predictions and targets.")
    return sum(abs(p - t) for p, t in zip(preds, targets)) / len(preds)

def rmse(preds: Sequence[float] | Iterable[float], targets: Sequence[float] | Iterable[float]) -> float:
    """Root Mean Squared Error."""
    preds = list(preds)
    targets = list(targets)
    if len(preds) != len(targets):
        raise ValueError("Length mismatch between predictions and targets.")
    mse = sum((p - t) ** 2 for p, t in zip(preds, targets)) / len(preds)
    return math.sqrt(mse)