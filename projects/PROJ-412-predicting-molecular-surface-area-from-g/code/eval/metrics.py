"""
Evaluation metrics and statistical tests for molecular property prediction.

This module provides functions for calculating performance metrics (MAE, RMSE, R²)
and statistical tests (paired t-test, Cohen's d) for model comparison.
It also includes multiple-comparison correction methods (Bonferroni, FDR).
"""
import numpy as np
from typing import Tuple, Dict, Any, List, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Error."""
    return float(np.mean(np.abs(y_true - y_pred)))


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Root Mean Squared Error."""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R-squared (coefficient of determination)."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return float(1 - (ss_res / ss_tot))


def calculate_all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate all standard metrics (MAE, RMSE, R²)."""
    return {
        "mae": calculate_mae(y_true, y_pred),
        "rmse": calculate_rmse(y_true, y_pred),
        "r2": calculate_r2(y_true, y_pred)
    }


def paired_ttest(y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray) -> Tuple[float, float]:
    """
    Perform a paired t-test between two sets of predictions against true values.
    
    Returns:
        Tuple of (t-statistic, p-value)
    """
    # We are testing if the errors of model A and model B are significantly different
    error_a = y_true - y_pred_a
    error_b = y_true - y_pred_b
    t_stat, p_val = stats.ttest_rel(error_a, error_b)
    return float(t_stat), float(p_val)


def cohen_d(y_pred_a: np.ndarray, y_pred_b: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two sets of predictions.
    
    Note: This is a simplified version assuming we are comparing the distributions of predictions.
    A more rigorous approach might compare the errors.
    """
    mean_a = np.mean(y_pred_a)
    mean_b = np.mean(y_pred_b)
    std_a = np.std(y_pred_a, ddof=1)
    std_b = np.std(y_pred_b, ddof=1)
    
    # Pooled standard deviation
    n_a = len(y_pred_a)
    n_b = len(y_pred_b)
    pooled_std = np.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return float((mean_a - mean_b) / pooled_std)


def compare_models(
    y_true: np.ndarray, 
    y_pred_a: np.ndarray, 
    y_pred_b: np.ndarray
) -> Dict[str, Any]:
    """
    Compare two models using multiple metrics and statistical tests.
    
    Returns:
        Dictionary containing MAE, RMSE, R² for both models, and statistical test results.
    """
    metrics_a = calculate_all_metrics(y_true, y_pred_a)
    metrics_b = calculate_all_metrics(y_true, y_pred_b)
    
    t_stat, p_val = paired_ttest(y_true, y_pred_a, y_pred_b)
    d_effect = cohen_d(y_pred_a, y_pred_b)
    
    return {
        "model_a": metrics_a,
        "model_b": metrics_b,
        "paired_ttest": {"t_statistic": t_stat, "p_value": p_val},
        "cohen_d": d_effect
    }


def bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    The Bonferroni correction adjusts p-values to control the family-wise error rate (FWER).
    Each p-value is multiplied by the number of tests (m), and capped at 1.0.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of corrected p-values.
    """
    if not p_values:
        return []
    
    m = len(p_values)
    corrected = [min(p * m, 1.0) for p in p_values]
    return corrected


def fdr_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg False Discovery Rate (FDR) correction.
    
    This method controls the expected proportion of false discoveries among the 
    rejected hypotheses. It is less conservative than Bonferroni.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of corrected p-values in the original order.
    """
    if not p_values:
        return []
    
    m = len(p_values)
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate raw BH adjusted p-values
    # q(i) = p(i) * m / i
    # i is 1-based rank
    raw_corrected = (sorted_p * m) / np.arange(1, m + 1)
    
    # Enforce monotonicity from the largest to smallest
    # q(i) = min(q(i), q(i+1), ..., q(m))
    # We do this by iterating from the end
    for i in range(m - 2, -1, -1):
        raw_corrected[i] = min(raw_corrected[i], raw_corrected[i + 1])
    
    # Cap at 1.0
    raw_corrected = np.minimum(raw_corrected, 1.0)
    
    # Restore original order
    final_corrected = np.empty(m)
    final_corrected[sorted_indices] = raw_corrected
    
    return final_corrected.tolist()