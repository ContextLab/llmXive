"""
Statistical testing module for meta-analysis results.

Implements exact binomial test, Shapiro-Wilk, ANOVA, Kruskal-Wallis,
and Bonferroni correction.
"""

import math
from typing import List, Dict, Any, Tuple
import numpy as np
from scipy import stats

from utils.logging import get_logger

logger = get_logger(__name__)


def exact_binomial_test(
    successes: int,
    trials: int,
    p_null: float = 0.95
) -> Dict[str, float]:
    """
    Performs an exact binomial test to check if coverage rate
    deviates significantly from the expected rate (e.g., 0.95).

    Returns:
        Dict with 'p_value' and 'statistic' (proportion).
    """
    if trials == 0:
        return {"p_value": 1.0, "statistic": 0.0}

    observed_rate = successes / trials
    # Two-sided test
    p_value = stats.binomtest(successes, trials, p_null).pvalue

    return {
        "p_value": float(p_value),
        "statistic": float(observed_rate)
    }


def shapiro_wilk_test(data: List[float]) -> Dict[str, float]:
    """
    Performs Shapiro-Wilk test for normality.
    Returns p-value.
    """
    if len(data) < 3:
        return {"p_value": 1.0, "statistic": 1.0}

    try:
        stat, p_val = stats.shapiro(data)
        return {"p_value": float(p_val), "statistic": float(stat)}
    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed: {e}")
        return {"p_value": 1.0, "statistic": 0.0}


def bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> List[Dict[str, float]]:
    """
    Applies Bonferroni correction to a list of p-values.
    Returns list of dicts with original p-value, corrected p-value, and significance.
    """
    n = len(p_values)
    if n == 0:
        return []

    corrected_alpha = alpha / n
    results = []

    for p in p_values:
        corrected_p = min(p * n, 1.0)
        results.append({
            "original_p": float(p),
            "corrected_p": float(corrected_p),
            "is_significant": corrected_p < alpha
        })

    return results


def conditional_statistical_test(
    data_groups: List[List[float]],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Selects the appropriate test (ANOVA or Kruskal-Wallis) based on
    Shapiro-Wilk normality test results.

    Args:
        data_groups: List of lists, where each inner list is a group of data points.
        alpha: Significance level for normality test.

    Returns:
        Dict with 'test_name', 'statistic', 'p_value', 'is_significant'.
    """
    if len(data_groups) < 2:
        return {"error": "Need at least 2 groups"}

    # Flatten for normality check? Or check each group?
    # FR-008: Check normality of residuals or groups.
    # Strategy: Check normality of each group. If any fails, use non-parametric.
    all_normal = True
    for group in data_groups:
        if len(group) >= 3:
            res = shapiro_wilk_test(group)
            if res["p_value"] < alpha:
                all_normal = False
                break

    if all_normal:
        # ANOVA
        try:
            f_stat, p_val = stats.f_oneway(*data_groups)
            return {
                "test_name": "ANOVA",
                "statistic": float(f_stat),
                "p_value": float(p_val),
                "is_significant": p_val < alpha
            }
        except Exception as e:
            logger.warning(f"ANOVA failed, falling back to Kruskal-Wallis: {e}")
            return _run_kruskal_wallis(data_groups, alpha)
    else:
        return _run_kruskal_wallis(data_groups, alpha)


def _run_kruskal_wallis(
    data_groups: List[List[float]],
    alpha: float
) -> Dict[str, Any]:
    """Runs Kruskal-Wallis test."""
    try:
        h_stat, p_val = stats.kruskal(*data_groups)
        return {
            "test_name": "Kruskal-Wallis",
            "statistic": float(h_stat),
            "p_value": float(p_val),
            "is_significant": p_val < alpha
        }
    except Exception as e:
        logger.error(f"Kruskal-Wallis failed: {e}")
        return {"error": str(e)}


def apply_anova(data_groups: List[List[float]], alpha: float = 0.05) -> Dict[str, Any]:
    """Wrapper for explicit ANOVA call."""
    try:
        f_stat, p_val = stats.f_oneway(*data_groups)
        return {
            "test_name": "ANOVA",
            "statistic": float(f_stat),
            "p_value": float(p_val),
            "is_significant": p_val < alpha
        }
    except Exception as e:
        return {"error": str(e)}


def apply_kruskal_wallis(data_groups: List[List[float]], alpha: float = 0.05) -> Dict[str, Any]:
    """Wrapper for explicit Kruskal-Wallis call."""
    try:
        h_stat, p_val = stats.kruskal(*data_groups)
        return {
            "test_name": "Kruskal-Wallis",
            "statistic": float(h_stat),
            "p_value": float(p_val),
            "is_significant": p_val < alpha
        }
    except Exception as e:
        return {"error": str(e)}
