"""
Metric interfaces and base classes.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union

import numpy as np

class BaseMetric(ABC):
    """Abstract base class for evaluation metrics."""

    @abstractmethod
    def compute(self, y_true: List[float], y_pred: List[float], intervals: Dict[str, Any]) -> float:
        """
        Compute the metric value.

        Args:
            y_true: Actual values.
            y_pred: Point forecasts.
            intervals: Dictionary containing 'lower' and 'upper' bounds.

        Returns:
            Computed metric value.
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """Return the unique name of the metric."""
        pass

class BaseCoverageMetric(BaseMetric):
    """Base class for metrics that evaluate interval coverage."""

    def _validate_inputs(self, y_true: List[float], y_pred: List[float], intervals: Dict[str, Any]) -> None:
        """Validate that inputs are consistent in length and contain valid data."""
        n_true = len(y_true)
        n_pred = len(y_pred)
        
        if n_true != n_pred:
            raise ValueError(f"Length mismatch: y_true ({n_true}) != y_pred ({n_pred})")

        if 'lower' not in intervals or 'upper' not in intervals:
            raise ValueError("Intervals must contain 'lower' and 'upper' keys")

        lower = intervals['lower']
        upper = intervals['upper']

        if len(lower) != n_true or len(upper) != n_true:
            raise ValueError(f"Interval lengths ({len(lower)}, {len(upper)}) must match data length ({n_true})")

        # Check for NaN/Inf in inputs
        if any(np.isnan(v) or np.isinf(v) for v in y_true):
            raise ValueError("y_true contains NaN or Inf values")
        if any(np.isnan(v) or np.isinf(v) for v in y_pred):
            raise ValueError("y_pred contains NaN or Inf values")
        if any(np.isnan(v) or np.isinf(v) for v in lower):
            raise ValueError("Interval lower bounds contain NaN or Inf values")
        if any(np.isnan(v) or np.isinf(v) for v in upper):
            raise ValueError("Interval upper bounds contain NaN or Inf values")

__all__ = ["BaseMetric", "BaseCoverageMetric"]