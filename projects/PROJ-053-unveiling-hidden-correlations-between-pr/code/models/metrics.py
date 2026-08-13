import os
import sys
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

logger = logging.getLogger(__name__)

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return r2_score(y_true, y_pred)

def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return np.sqrt(mean_squared_error(y_true, y_pred))

def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return mean_absolute_error(y_true, y_pred)

def calculate_rmse_percentage_of_range(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    range_val = np.max(y_true) - np.min(y_true)
    if range_val == 0:
        return 0.0
    return (calculate_rmse(y_true, y_pred) / range_val) * 100

def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate standard metrics for a single target.
    """
    return {
        "r2": float(calculate_r2(y_true, y_pred)),
        "rmse": float(calculate_rmse(y_true, y_pred)),
        "mae": float(calculate_mae(y_true, y_pred))
    }

def save_metrics(metrics: Dict[str, Any], filepath: str) -> None:
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {filepath}")

def main():
    """Main entry point."""
    logger.warning("metrics.py main() is not intended for standalone execution.")

if __name__ == "__main__":
    main()
