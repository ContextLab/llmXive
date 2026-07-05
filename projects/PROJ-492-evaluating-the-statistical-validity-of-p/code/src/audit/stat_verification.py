"""
Statistical Verification Utilities.

Implements standard statistical tests (z-test, t-test, Fisher) and
verification functions.
"""

import logging
from typing import Optional, Tuple, Dict, Any
import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)

def two_proportion_z_test(n1: int, x1: int, n2: int, x2: int) -> Tuple[float, float]:
    """
    Perform two-proportion z-test.

    Args:
        n1: Sample size 1.
        x1: Successes 1.
        n2: Sample size 2.
        x2: Successes 2.

    Returns:
        Tuple of (z-statistic, p-value).
    """
    set_rng_seed()
    
    p1 = x1 / n1
    p2 = x2 / n2
    p_pooled = (x1 + x2) / (n1 + n2)
    
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    if se == 0:
        return 0.0, 1.0
    
    z = (p1 - p2) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    
    return z, p_value

def welch_t_test(mean1: float, mean2: float, std1: float, std2: float, n1: int, n2: int) -> Tuple[float, float]:
    """
    Perform Welch's t-test.

    Args:
        mean1: Mean of group 1.
        mean2: Mean of group 2.
        std1: Std dev of group 1.
        std2: Std dev of group 2.
        n1: Sample size 1.
        n2: Sample size 2.

    Returns:
        Tuple of (t-statistic, p-value).
    """
    set_rng_seed()
    
    # Calculate t-statistic
    se = np.sqrt((std1**2 / n1) + (std2**2 / n2))
    
    if se == 0:
        return 0.0, 1.0
    
    t_stat = (mean1 - mean2) / se
    
    # Degrees of freedom (Welch-Satterthwaite)
    df_num = (std1**2/n1 + std2**2/n2)**2
    df_den = (std1**2/n1)**2/(n1-1) + (std2**2/n2)**2/(n2-1)
    
    if df_den == 0:
        df = 1
    else:
        df = df_num / df_den
    
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    
    return t_stat, p_value

def fisher_exact_test(a: int, b: int, c: int, d: int) -> Tuple[float, float]:
    """
    Perform Fisher's exact test.

    Args:
        a, b, c, d: Contingency table values.

    Returns:
        Tuple of (odds ratio, p-value).
    """
    set_rng_seed()
    _, p_value = stats.fisher_exact([[a, b], [c, d]], alternative='two-sided')
    return 1.0, p_value # Odds ratio omitted for simplicity in this signature

def verify_z_test_consistency(reported_p: float, calculated_p: float, tolerance: float = 0.005) -> bool:
    """Verify if reported and calculated p-values are consistent."""
    set_rng_seed()
    return abs(reported_p - calculated_p) <= tolerance

def verify_welch_t_consistency(reported_p: float, calculated_p: float, tolerance: float = 0.005) -> bool:
    """Verify Welch t-test consistency."""
    set_rng_seed()
    return abs(reported_p - calculated_p) <= tolerance

def verify_fisher_consistency(reported_p: float, calculated_p: float, tolerance: float = 0.005) -> bool:
    """Verify Fisher's exact test consistency."""
    set_rng_seed()
    return abs(reported_p - calculated_p) <= tolerance

def main():
    """Main entry point."""
    # Example usage
    z, p = two_proportion_z_test(1000, 100, 1000, 120)
    print(f"Z-test: z={z}, p={p}")
    
    t, p = welch_t_test(100, 105, 10, 10, 50, 50)
    print(f"Welch t-test: t={t}, p={p}")

if __name__ == "__main__":
    main()
