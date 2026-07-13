import numpy as np
from scipy import stats
from typing import Tuple, Union

def pearson_r(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Pearson correlation coefficient."""
    return stats.pearsonr(y_true, y_pred)[0]

def r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R-squared score."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot)

def pearson_pvalue(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate p-value for Pearson correlation."""
    return stats.pearsonr(y_true, y_pred)[1]

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Calculate all metrics."""
    return {
        "pearson_r": float(pearson_r(y_true, y_pred)),
        "r_squared": float(r_squared(y_true, y_pred)),
        "p_value": float(pearson_pvalue(y_true, y_pred))
    }
