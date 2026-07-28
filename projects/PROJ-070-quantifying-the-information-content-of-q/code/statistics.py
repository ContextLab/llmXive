import numpy as np
from scipy import stats
from logging_config import logger

def calculate_correlation(x: np.ndarray, y: np.ndarray) -> tuple:
    """Calculate Pearson correlation coefficient and p-value."""
    r, p = stats.pearsonr(x, y)
    return float(r), float(p)

def calculate_partial_correlation(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> float:
    """
    Calculate partial correlation between x and y, controlling for z (system size N).
    """
    # Using scipy's partial correlation logic via residuals
    # Regress x on z
    res_x = stats.linregress(z, x).resid
    # Regress y on z
    res_y = stats.linregress(z, y).resid
    
    r, p = stats.pearsonr(res_x, res_y)
    logger.info(f"Partial correlation (controlling for N): {r:.4f}, p-value: {p:.4f}")
    return float(r)

def bootstrap_correlation(x: np.ndarray, y: np.ndarray, n_iterations: int = 1000, seed: int = 42) -> np.ndarray:
    """
    Perform bootstrap resampling to generate distribution of correlation coefficients.
    """
    rng = np.random.RandomState(seed)
    n = len(x)
    boot_r = np.zeros(n_iterations)
    
    for i in range(n_iterations):
        idx = rng.choice(n, size=n, replace=True)
        boot_r[i] = np.corrcoef(x[idx], y[idx])[0, 1]
    
    return boot_r

def calculate_confidence_intervals(data: np.ndarray, confidence: float = 0.95) -> tuple:
    """
    Calculate confidence intervals using standard percentile method.
    """
    alpha = 1 - confidence
    lower = np.percentile(data, 100 * alpha / 2)
    upper = np.percentile(data, 100 * (1 - alpha / 2))
    return float(lower), float(upper)
