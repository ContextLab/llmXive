"""
Statistical verification utilities for A/B test consistency auditing.

This module implements the core statistical tests required to reconstruct
p-values from A/B test summary statistics and compare them against reported values.
It supports:
- Two-proportion z-test (for binary outcomes)
- Welch's t-test (for continuous outcomes)
- Fisher's Exact Test (for binary outcomes with small sample sizes)

All functions are deterministic when seeded via `src/config.set_rng_seed`.
"""

import logging
from typing import Optional, Tuple, Dict, Any

import numpy as np
from scipy import stats

from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.config import set_rng_seed

logger: logging.Logger = get_default_logger(__name__)


def two_proportion_z_test(
    n1: int,
    x1: float,
    n2: int,
    x2: float
) -> Tuple[float, float]:
    """
    Perform a two-proportion z-test to compare the success rates of two groups.

    Args:
        n1: Sample size of group 1.
        x1: Number of successes in group 1.
        n2: Sample size of group 2.
        x2: Number of successes in group 2.

    Returns:
        A tuple (z_statistic, p_value) for a two-tailed test.
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("Sample sizes must be positive integers.")

    p1 = x1 / n1
    p2 = x2 / n2

    # Pooled proportion under the null hypothesis
    p_pooled = (x1 + x2) / (n1 + n2)
    q_pooled = 1.0 - p_pooled

    # Standard error of the difference
    se = np.sqrt(p_pooled * q_pooled * (1.0 / n1 + 1.0 / n2))

    if se == 0:
        # If pooled proportion is 0 or 1, z is undefined (or 0 if p1==p2)
        if np.isclose(p1, p2):
            return 0.0, 1.0
        # Otherwise, the difference is infinite
        return float('inf'), 0.0

    z = (p1 - p2) / se

    # Two-tailed p-value
    p_value = 2.0 * (1.0 - stats.norm.cdf(abs(z)))

    return z, p_value


def welch_t_test(
    mean1: float,
    mean2: float,
    std1: float,
    std2: float,
    n1: int,
    n2: int
) -> Tuple[float, float]:
    """
    Perform Welch's t-test for comparing means of two independent groups
    with potentially unequal variances.

    Args:
        mean1: Mean of group 1.
        mean2: Mean of group 2.
        std1: Standard deviation of group 1.
        std2: Standard deviation of group 2.
        n1: Sample size of group 1.
        n2: Sample size of group 2.

    Returns:
        A tuple (t_statistic, p_value) for a two-tailed test.
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("Sample sizes must be positive integers.")
    if std1 < 0 or std2 < 0:
        raise ValueError("Standard deviations cannot be negative.")

    # Handle edge case where std is 0 for both groups
    if std1 == 0 and std2 == 0:
        if np.isclose(mean1, mean2):
            return 0.0, 1.0
        return float('inf'), 0.0

    # Welch's t-statistic
    # t = (mean1 - mean2) / sqrt(s1^2/n1 + s2^2/n2)
    denominator = np.sqrt((std1 ** 2 / n1) + (std2 ** 2 / n2))
    if denominator == 0:
        if np.isclose(mean1, mean2):
            return 0.0, 1.0
        return float('inf'), 0.0

    t_stat = (mean1 - mean2) / denominator

    # Welch-Satterthwaite equation for degrees of freedom
    # df = (s1^2/n1 + s2^2/n2)^2 / [ (s1^2/n1)^2/(n1-1) + (s2^2/n2)^2/(n2-1) ]
    num = (std1 ** 2 / n1 + std2 ** 2 / n2) ** 2
    denom = (std1 ** 2 / n1) ** 2 / (n1 - 1) + (std2 ** 2 / n2) ** 2 / (n2 - 1)

    if denom == 0:
        # If denominator is 0, it means one of the groups has n=1 and std=0
        # or similar degenerate case. Use a large df approximation.
        df = float('inf')
    else:
        df = num / denom

    # Two-tailed p-value
    p_value = 2.0 * stats.t.sf(abs(t_stat), df)

    return t_stat, p_value


def fisher_exact_test(
    n1: int,
    x1: float,
    n2: int,
    x2: float
) -> Tuple[float, float]:
    """
    Perform Fisher's Exact Test for 2x2 contingency tables.
    This is often used for binary outcomes with small sample sizes.

    Args:
        n1: Total sample size of group 1.
        x1: Number of successes in group 1.
        n2: Total sample size of group 2.
        x2: Number of successes in group 2.

    Returns:
        A tuple (odds_ratio, p_value) for a two-sided test.
        Note: Scipy's fisher_exact returns the odds ratio and the p-value.
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("Sample sizes must be positive integers.")
    if x1 < 0 or x2 < 0 or x1 > n1 or x2 > n2:
        raise ValueError("Success counts must be between 0 and sample size.")

    # Construct the 2x2 contingency table
    # [[x1, n1-x1], [x2, n2-x2]]
    # Group 1: Successes = x1, Failures = n1 - x1
    # Group 2: Successes = x2, Failures = n2 - x2
    table = [[int(round(x1)), int(round(n1 - x1))],
             [int(round(x2)), int(round(n2 - x2))]]

    # scipy.stats.fisher_exact returns (odds_ratio, p_value)
    # By default, alternative='two-sided'
    odds_ratio, p_value = stats.fisher_exact(table, alternative='two-sided')

    return odds_ratio, p_value


def verify_z_test_consistency(
    n1: int,
    x1: float,
    n2: int,
    x2: float,
    reported_p: float,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Verify consistency between reported p-value and calculated z-test p-value.

    Args:
        n1, x1, n2, x2: Sample sizes and success counts.
        reported_p: The p-value reported in the A/B test summary.
        threshold: The maximum absolute difference allowed for consistency.

    Returns:
        A dictionary containing the calculated z, calculated p, reported p,
        difference, and a boolean indicating consistency.
    """
    set_rng_seed() # Ensure deterministic behavior if needed internally
    z, calc_p = two_proportion_z_test(n1, x1, n2, x2)

    diff = abs(calc_p - reported_p)
    is_consistent = diff <= threshold

    return {
        "test_type": "z_test",
        "calculated_z": z,
        "calculated_p": calc_p,
        "reported_p": reported_p,
        "absolute_difference": diff,
        "is_consistent": is_consistent
    }


def verify_welch_t_consistency(
    mean1: float,
    mean2: float,
    std1: float,
    std2: float,
    n1: int,
    n2: int,
    reported_p: float,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Verify consistency between reported p-value and calculated Welch's t-test p-value.

    Args:
        mean1, mean2: Group means.
        std1, std2: Group standard deviations.
        n1, n2: Sample sizes.
        reported_p: The p-value reported in the A/B test summary.
        threshold: The maximum absolute difference allowed for consistency.

    Returns:
        A dictionary containing the calculated t, calculated p, reported p,
        difference, and a boolean indicating consistency.
    """
    set_rng_seed()
    t, calc_p = welch_t_test(mean1, mean2, std1, std2, n1, n2)

    diff = abs(calc_p - reported_p)
    is_consistent = diff <= threshold

    return {
        "test_type": "welch_t_test",
        "calculated_t": t,
        "calculated_p": calc_p,
        "reported_p": reported_p,
        "absolute_difference": diff,
        "is_consistent": is_consistent
    }


def verify_fisher_consistency(
    n1: int,
    x1: float,
    n2: int,
    x2: float,
    reported_p: float,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Verify consistency between reported p-value and calculated Fisher's exact test p-value.

    Args:
        n1, x1, n2, x2: Sample sizes and success counts.
        reported_p: The p-value reported in the A/B test summary.
        threshold: The maximum absolute difference allowed for consistency.

    Returns:
        A dictionary containing the calculated odds ratio, calculated p, reported p,
        difference, and a boolean indicating consistency.
    """
    set_rng_seed()
    odds_ratio, calc_p = fisher_exact_test(n1, x1, n2, x2)

    diff = abs(calc_p - reported_p)
    is_consistent = diff <= threshold

    return {
        "test_type": "fisher_exact",
        "calculated_odds_ratio": odds_ratio,
        "calculated_p": calc_p,
        "reported_p": reported_p,
        "absolute_difference": diff,
        "is_consistent": is_consistent
    }
