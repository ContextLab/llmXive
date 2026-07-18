"""
Statistical analysis module for gene essentiality correlation.

Implements:
- Spearman's rank correlation
- Fisher's z-transformation (for US2)
- Null model generation (for US1 null models)
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

class StatisticsError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

def calculate_spearman_correlation(
    centrality_values: List[float],
    essentiality_labels: List[int]
) -> Tuple[float, float]:
    """
    Calculate Spearman's rank correlation coefficient between centrality and essentiality.
    
    Args:
        centrality_values: List of centrality scores (float).
        essentiality_labels: List of binary essentiality labels (0 or 1).
    
    Returns:
        Tuple of (rho, p_value).
    
    Raises:
        StatisticsError: If inputs are invalid or calculation fails.
    """
    if len(centrality_values) != len(essentiality_labels):
        raise StatisticsError(
            f"Length mismatch: centrality ({len(centrality_values)}) != labels ({len(essentiality_labels)})"
        )
    
    if len(centrality_values) < 2:
        logger.warning("Insufficient data points for correlation calculation.")
        return np.nan, np.nan
    
    try:
        # Convert to numpy arrays for stability
        x = np.array(centrality_values, dtype=float)
        y = np.array(essentiality_labels, dtype=float)
        
        # Handle constant arrays (which cause division by zero in scipy)
        if np.all(x == x[0]) or np.all(y == y[0]):
            logger.warning("Constant array detected; correlation is undefined.")
            return np.nan, np.nan
        
        rho, p_value = stats.spearmanr(x, y)
        return float(rho), float(p_value)
    
    except Exception as e:
        logger.error(f"Error calculating Spearman correlation: {e}")
        raise StatisticsError(f"Correlation calculation failed: {e}")

def fisher_z_transform(r: float) -> float:
    """
    Apply Fisher's z-transformation to a correlation coefficient.
    Used for comparing correlations across organisms (US2).
    
    Args:
        r: Pearson/Spearman correlation coefficient (-1 < r < 1).
    
    Returns:
        Transformed z-value.
    """
    if not -1.0 < r < 1.0:
        logger.warning(f"Correlation {r} is out of range for Fisher Z transform. Clipping.")
        r = np.clip(r, -0.9999, 0.9999)
    
    return 0.5 * np.log((1 + r) / (1 - r))

def fisher_z_to_r(z: float) -> float:
    """
    Inverse Fisher's z-transformation.
    
    Args:
        z: Fisher z-value.
    
    Returns:
        Correlation coefficient.
    """
    return np.tanh(z)

def generate_null_distribution_permutation(
    centrality_values: List[float],
    essentiality_labels: List[int],
    n_permutations: int = 1000
) -> List[float]:
    """
    Generate a null distribution of correlations by permuting labels.
    
    Args:
        centrality_values: Original centrality scores.
        essentiality_labels: Original labels.
        n_permutations: Number of shuffles.
    
    Returns:
        List of correlation coefficients from permuted data.
    """
    x = np.array(centrality_values)
    y = np.array(essentiality_labels)
    
    null_dist = []
    for _ in range(n_permutations):
        np.random.shuffle(y)
        rho, _ = stats.spearmanr(x, y)
        null_dist.append(rho)
    
    return null_dist

def calculate_empirical_p_value(
    observed_rho: float,
    null_distribution: List[float]
) -> float:
    """
    Calculate empirical p-value by comparing observed statistic to null distribution.
    
    Args:
        observed_rho: The observed correlation coefficient.
        null_distribution: List of null correlation coefficients.
    
    Returns:
        Empirical p-value.
    """
    if not null_distribution:
        raise StatisticsError("Null distribution is empty.")
    
    null_array = np.array(null_distribution)
    # Two-tailed test
    count = np.sum(np.abs(null_array) >= np.abs(observed_rho))
    return count / len(null_distribution)

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values.
    
    Returns:
        List of adjusted p-values.
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    adjusted = np.zeros(n)
    for i, p in enumerate(sorted_p):
        # BH formula: p * n / rank
        # Rank is i+1 (1-indexed)
        adjusted[sorted_indices[i]] = min(p * n / (i + 1), 1.0)
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i+1])
    
    return adjusted.tolist()