import numpy as np
from typing import List, Tuple
from scipy import stats

def pearson_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    r, p = stats.pearsonr(x, y)
    return r, p

def spearman_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    r, p = stats.spearmanr(x, y)
    return r, p

def bootstrap_confidence_interval(x: np.ndarray, y: np.ndarray, n_bootstraps: int = 1000, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval for correlation using bootstrapping.
    """
    n = len(x)
    correlations = []
    for _ in range(n_bootstraps):
        indices = np.random.choice(n, size=n, replace=True)
        r, _ = stats.pearsonr(x[indices], y[indices])
        correlations.append(r)
    
    lower = np.percentile(correlations, (1 - confidence) / 2 * 100)
    upper = np.percentile(correlations, (1 + confidence) / 2 * 100)
    return lower, upper
