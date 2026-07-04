import logging
from typing import Optional, Tuple, Dict, Any
import numpy as np
from scipy import stats
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.config import set_rng_seed

logger = get_default_logger(__name__)

def two_proportion_z_test(
    n1: int,
    x1: int,
    n2: int,
    x2: int
) -> Tuple[float, float]:
    """
    Perform a two-proportion z-test.
    
    Args:
        n1: Sample size of group 1
        x1: Number of successes in group 1
        n2: Sample size of group 2
        x2: Number of successes in group 2
        
    Returns:
        Tuple of (z-statistic, p-value)
    """
    p1 = x1 / n1
    p2 = x2 / n2
    p_pooled = (x1 + x2) / (n1 + n2)
    
    if p_pooled == 0 or p_pooled == 1:
        return 0.0, 1.0
        
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    if se == 0:
        return 0.0, 1.0
        
    z_stat = (p1 - p2) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    return z_stat, p_value

def welch_t_test(
    mean1: float,
    mean2: float,
    std1: float,
    std2: float,
    n1: int,
    n2: int
) -> Tuple[float, float]:
    """
    Perform Welch's t-test (unpaired, unequal variances).
    
    Args:
        mean1: Mean of group 1
        mean2: Mean of group 2
        std1: Standard deviation of group 1
        std2: Standard deviation of group 2
        n1: Sample size of group 1
        n2: Sample size of group 2
        
    Returns:
        Tuple of (t-statistic, p-value)
    """
    # Calculate Welch's t-statistic
    se_diff = np.sqrt((std1**2 / n1) + (std2**2 / n2))
    if se_diff == 0:
        return 0.0, 1.0
        
    t_stat = (mean1 - mean2) / se_diff
    
    # Calculate degrees of freedom (Welch-Satterthwaite equation)
    numerator = (std1**2 / n1 + std2**2 / n2)**2
    denominator = (std1**2 / n1)**2 / (n1 - 1) + (std2**2 / n2)**2 / (n2 - 1)
    
    if denominator == 0:
        df = n1 + n2 - 2
    else:
        df = numerator / denominator
        
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    
    return t_stat, p_value

def fisher_exact_test(
    x1: int,
    n1_minus_x1: int,
    x2: int,
    n2_minus_x2: int
) -> Tuple[float, float]:
    """
    Perform Fisher's exact test for 2x2 contingency tables.
    
    Args:
        x1: Successes in group 1
        n1_minus_x1: Failures in group 1
        x2: Successes in group 2
        n2_minus_x2: Failures in group 2
        
    Returns:
        Tuple of (odds ratio, two-sided p-value)
    """
    try:
        table = [[x1, n1_minus_x1], [x2, n2_minus_x2]]
        odds_ratio, p_value = stats.fisher_exact(table, alternative='two-sided')
        return float(odds_ratio), float(p_value)
    except Exception as e:
        logger.warning(f"Fisher exact test failed: {e}")
        return 1.0, 1.0

def verify_z_test_consistency(
    n1: int,
    x1: int,
    n2: int,
    x2: int,
    reported_p_value: float,
    tolerance: float = 0.005
) -> Dict[str, Any]:
    """
    Verify that a reported p-value matches the z-test calculation.
    
    Args:
        n1, x1, n2, x2: Data for two proportion groups
        reported_p_value: The p-value reported in the summary
        tolerance: Maximum acceptable difference
        
    Returns:
        Dictionary with verification results
    """
    set_rng_seed(42)
    _, calculated_p = two_proportion_z_test(n1, x1, n2, x2)
    
    diff = abs(calculated_p - reported_p_value)
    is_consistent = diff <= tolerance
    
    return {
        "test_type": "z-test",
        "reported_p": reported_p_value,
        "calculated_p": calculated_p,
        "difference": diff,
        "is_consistent": is_consistent,
        "tolerance": tolerance
    }

def verify_welch_t_consistency(
    mean1: float,
    mean2: float,
    std1: float,
    std2: float,
    n1: int,
    n2: int,
    reported_p_value: float,
    tolerance: float = 0.005
) -> Dict[str, Any]:
    """
    Verify that a reported p-value matches the Welch t-test calculation.
    
    Args:
        mean1, mean2, std1, std2, n1, n2: Data for two continuous groups
        reported_p_value: The p-value reported in the summary
        tolerance: Maximum acceptable difference
        
    Returns:
        Dictionary with verification results
    """
    set_rng_seed(42)
    _, calculated_p = welch_t_test(mean1, mean2, std1, std2, n1, n2)
    
    diff = abs(calculated_p - reported_p_value)
    is_consistent = diff <= tolerance
    
    return {
        "test_type": "welch-t",
        "reported_p": reported_p_value,
        "calculated_p": calculated_p,
        "difference": diff,
        "is_consistent": is_consistent,
        "tolerance": tolerance
    }

def verify_fisher_consistency(
    x1: int,
    n1_minus_x1: int,
    x2: int,
    n2_minus_x2: int,
    reported_p_value: float,
    tolerance: float = 0.005
) -> Dict[str, Any]:
    """
    Verify that a reported p-value matches Fisher's exact test calculation.
    
    Args:
        x1, n1_minus_x1, x2, n2_minus_x2: Data for 2x2 contingency table
        reported_p_value: The p-value reported in the summary
        tolerance: Maximum acceptable difference
        
    Returns:
        Dictionary with verification results
    """
    set_rng_seed(42)
    _, calculated_p = fisher_exact_test(x1, n1_minus_x1, x2, n2_minus_x2)
    
    diff = abs(calculated_p - reported_p_value)
    is_consistent = diff <= tolerance
    
    return {
        "test_type": "fisher",
        "reported_p": reported_p_value,
        "calculated_p": calculated_p,
        "difference": diff,
        "is_consistent": is_consistent,
        "tolerance": tolerance
    }
