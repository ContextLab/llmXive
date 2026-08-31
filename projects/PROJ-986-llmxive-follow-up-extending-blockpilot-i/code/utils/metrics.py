import time
import math
from typing import List, Union, Tuple, Callable, Optional
import numpy as np
from scipy import stats

def calculate_latency(func: Callable, *args, **kwargs) -> float:
    """Measure execution time of a function call in seconds."""
    start = time.perf_counter()
    func(*args, **kwargs)
    end = time.perf_counter()
    return end - start

def calculate_mean_latency(latencies: List[float]) -> float:
    """Calculate mean of latency measurements."""
    return float(np.mean(latencies))

def calculate_accuracy(predictions: List[int], ground_truth: List[int]) -> float:
    """Calculate classification accuracy."""
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")
    correct = sum(p == g for p, g in zip(predictions, ground_truth))
    return correct / len(ground_truth)

def calculate_regression_accuracy(predictions: List[float], ground_truth: List[int]) -> float:
    """
    Calculate accuracy for regression-based block size prediction.
    Returns the percentage of predictions within ±1 of ground truth.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")
    close = sum(abs(p - g) <= 1 for p, g in zip(predictions, ground_truth))
    return close / len(ground_truth)

def calculate_mae(predictions: List[float], ground_truth: List[float]) -> float:
    """Calculate Mean Absolute Error."""
    return float(np.mean(np.abs(np.array(predictions) - np.array(ground_truth))))

def calculate_rmse(predictions: List[float], ground_truth: List[float]) -> float:
    """Calculate Root Mean Squared Error."""
    return float(np.sqrt(np.mean((np.array(predictions) - np.array(ground_truth)) ** 2)))

def calculate_correlation(x: List[float], y: List[float], method: str = "pearson") -> float:
    """Calculate correlation coefficient between two lists."""
    if method == "pearson":
        return float(stats.pearsonr(x, y)[0])
    elif method == "spearman":
        return float(stats.spearmanr(x, y)[0])
    else:
        raise ValueError(f"Unknown method: {method}")

def calculate_pcc(x: List[float], y: List[float]) -> float:
    """Calculate Pearson Correlation Coefficient."""
    return calculate_correlation(x, y, "pearson")

def calculate_scc(x: List[float], y: List[float]) -> float:
    """Calculate Spearman Correlation Coefficient."""
    return calculate_correlation(x, y, "spearman")

def calculate_kcc(x: List[float], y: List[float]) -> float:
    """Calculate Kendall Tau Correlation Coefficient."""
    return float(stats.kendalltau(x, y)[0])

def calculate_r_squared(y_true: List[float], y_pred: List[float]) -> float:
    """Calculate R-squared (coefficient of determination)."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return float(1 - (ss_res / ss_tot))
