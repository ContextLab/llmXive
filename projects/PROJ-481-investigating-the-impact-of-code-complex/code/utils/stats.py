import numpy as np
from typing import Tuple, List, Dict, Any, Optional
from scipy import stats
from scipy.optimize import minimize_scalar
import warnings

def pearson_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Calculate Pearson correlation coefficient and p-value."""
    r, p = stats.pearsonr(x, y)
    return r, p

def spearman_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Calculate Spearman correlation coefficient and p-value."""
    r, p = stats.spearmanr(x, y)
    return r, p

def segmented_regression(x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Perform segmented regression to find change points."""
    # Placeholder for actual segmented regression logic
    # T026 will implement this with bootstrap CIs
    return {
        'change_point': 0.0,
        'confidence_interval': (0.0, 0.0)
    }

def bootstrap_confidence_interval(data: np.ndarray, n_iterations: int = 1000) -> Tuple[float, float]:
    """Calculate bootstrap confidence interval for a statistic."""
    bootstrapped = []
    for _ in range(n_iterations):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrapped.append(np.mean(sample))
    return np.percentile(bootstrapped, 2.5), np.percentile(bootstrapped, 97.5)

def bootstrap_correlation_ci(x: np.ndarray, y: np.ndarray, n_iterations: int = 1000) -> Tuple[float, float]:
    """Calculate bootstrap confidence interval for correlation."""
    bootstrapped_r = []
    for _ in range(n_iterations):
        indices = np.random.choice(len(x), size=len(x), replace=True)
        r, _ = stats.pearsonr(x[indices], y[indices])
        bootstrapped_r.append(r)
    return np.percentile(bootstrapped_r, 2.5), np.percentile(bootstrapped_r, 97.5)

def bootstrap_regression_ci(x: np.ndarray, y: np.ndarray, n_iterations: int = 1000) -> Tuple[float, float]:
    """Calculate bootstrap confidence interval for regression slope."""
    bootstrapped_slope = []
    for _ in range(n_iterations):
        indices = np.random.choice(len(x), size=len(x), replace=True)
        slope, _, _, _, _ = stats.linregress(x[indices], y[indices])
        bootstrapped_slope.append(slope)
    return np.percentile(bootstrapped_slope, 2.5), np.percentile(bootstrapped_slope, 97.5)
