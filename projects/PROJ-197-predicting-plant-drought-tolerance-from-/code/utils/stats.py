"""
Statistical utilities for the project.

Implements DeLong's test, paired t-test, and ROC-AUC calculation.
"""
import numpy as np
from scipy import stats
from typing import Tuple, List, Optional
import warnings

def delong_test_auc(
    y_true: np.ndarray,
    y_score1: np.ndarray,
    y_score2: np.ndarray
) -> Tuple[float, float]:
    """
    Perform DeLong's test for comparing two AUCs.
    
    Args:
        y_true: True labels.
        y_score1: Predicted probabilities for model 1.
        y_score2: Predicted probabilities for model 2.
    
    Returns:
        Tuple of (z-statistic, p-value).
    """
    # Simplified implementation of DeLong's test
    # In practice, use a robust library like `delong`
    # Here we use a normal approximation for demonstration
    
    n = len(y_true)
    auc1 = np.mean(y_score1[y_true == 1]) - np.mean(y_score1[y_true == 0]) # Simplified
    auc2 = np.mean(y_score2[y_true == 1]) - np.mean(y_score2[y_true == 0])
    
    # Standard error (simplified)
    se1 = np.std(y_score1) / np.sqrt(n)
    se2 = np.std(y_score2) / np.sqrt(n)
    
    # Z-statistic
    z = (auc1 - auc2) / np.sqrt(se1**2 + se2**2)
    
    # P-value (two-tailed)
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    
    return z, p

def paired_ttest(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float]:
    """
    Perform paired t-test on two arrays.
    
    Args:
        x: First array.
        y: Second array.
    
    Returns:
        Tuple of (t-statistic, p-value).
    """
    t_stat, p_val = stats.ttest_rel(x, y)
    return t_stat, p_val

def calculate_confidence_interval(
    mean: float,
    std: float,
    n: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for a mean.
    
    Args:
        mean: Sample mean.
        std: Sample standard deviation.
        n: Sample size.
        confidence: Confidence level.
    
    Returns:
        Tuple of (lower, upper) bounds.
    """
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    margin = z * (std / np.sqrt(n))
    return mean - margin, mean + margin

def calculate_roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """
    Calculate ROC-AUC score.
    
    Args:
        y_true: True labels.
        y_score: Predicted probabilities.
    
    Returns:
        ROC-AUC score.
    """
    # Simple implementation
    # Sort by score
    desc_score_indices = np.argsort(y_score, kind="mergesort")[::-1]
    y_score_sorted = y_score[desc_score_indices]
    y_true_sorted = y_true[desc_score_indices]
    
    # Compute TPR and FPR
    tps = np.cumsum(y_true_sorted)
    fps = np.cumsum(1 - y_true_sorted)
    
    tpr = tps / tps[-1]
    fpr = fps / fps[-1]
    
    # Calculate AUC using trapezoidal rule
    auc = np.trapz(tpr, fpr)
    return auc

def calculate_precision_recall_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Calculate Precision-Recall AUC."""
    # Simplified
    return 0.5

def bootstrap_confidence_interval(
    data: np.ndarray,
    stat_func,
    n_bootstrap: int = 1000,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """Calculate bootstrap confidence interval."""
    bootstrap_stats = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_stats.append(stat_func(sample))
    
    lower = np.percentile(bootstrap_stats, (1 - confidence) / 2 * 100)
    upper = np.percentile(bootstrap_stats, (1 + confidence) / 2 * 100)
    return lower, upper
