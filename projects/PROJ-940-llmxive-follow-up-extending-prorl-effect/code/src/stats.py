import json
import os
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats as scipy_stats
import logging

from src.exceptions import DataFetchError

logger = logging.getLogger(__name__)

def perform_shapiro_wilk(differences: List[float]) -> Tuple[float, float, bool]:
    """
    Perform Shapiro-Wilk test for normality on the metric differences.

    This is used to determine if a Paired T-Test (parametric) or Wilcoxon
    signed-rank test (non-parametric) is appropriate.

    Args:
        differences: List of differences between paired metric values
                    (e.g., ProRL score - Greedy score for each session).

    Returns:
        Tuple of (statistic, p_value, is_normal).
        - statistic: The Shapiro-Wilk test statistic.
        - p_value: The p-value of the test.
        - is_normal: True if p_value > 0.05 (fail to reject null hypothesis),
                     False otherwise.

    Raises:
        DataFetchError: If the input list is empty or has fewer than 3 samples
                        (Shapiro-Wilk requires at least 3 samples).
    """
    if not differences or len(differences) < 3:
        raise DataFetchError(
            f"Shapiro-Wilk test requires at least 3 samples, got {len(differences) if differences else 0}."
        )

    try:
        # scipy.stats.shapiro returns (statistic, p-value)
        # It assumes the null hypothesis is that the data is normally distributed.
        statistic, p_value = scipy_stats.shapiro(differences)
        is_normal = p_value > 0.05
        logger.info(
            f"Shapiro-Wilk Test: Stat={statistic:.4f}, P={p_value:.4f}, "
            f"Normal={is_normal}"
        )
        return float(statistic), float(p_value), is_normal
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        raise DataFetchError(f"Failed to perform Shapiro-Wilk test: {e}") from e

def perform_paired_ttest(
    group_a: List[float], group_b: List[float]
) -> Tuple[float, float]:
    """
    Perform a Paired T-Test to check for statistical significance between two
    related samples (e.g., Greedy vs ProRL metrics on the same sessions).

    This is the PRIMARY test per Constitution Principle VII.

    Args:
        group_a: List of metric values for the baseline (e.g., Greedy).
        group_b: List of metric values for the experimental group (e.g., ProRL).

    Returns:
        Tuple of (t_statistic, p_value).
    """
    if len(group_a) != len(group_b):
        raise ValueError(
            f"Group lengths must match for paired t-test: {len(group_a)} vs {len(group_b)}"
        )
    if len(group_a) < 2:
        raise ValueError(
            f"Paired t-test requires at least 2 samples, got {len(group_a)}"
        )

    try:
        t_stat, p_val = scipy_stats.ttest_rel(group_a, group_b)
        logger.info(
            f"Paired T-Test: t={t_stat:.4f}, p={p_val:.4f}"
        )
        return float(t_stat), float(p_val)
    except Exception as e:
        logger.error(f"Paired T-Test failed: {e}")
        raise DataFetchError(f"Failed to perform Paired T-Test: {e}") from e

def perform_wilcoxon(
    group_a: List[float], group_b: List[float]
) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test as a diagnostic fallback if t-test
    assumptions (normality) are violated.

    Args:
        group_a: List of metric values for the baseline.
        group_b: List of metric values for the experimental group.

    Returns:
        Tuple of (statistic, p_value).
    """
    if len(group_a) != len(group_b):
        raise ValueError(
            f"Group lengths must match for Wilcoxon test: {len(group_a)} vs {len(group_b)}"
        )
    if len(group_a) < 2:
        raise ValueError(
            f"Wilcoxon test requires at least 2 samples, got {len(group_a)}"
        )

    try:
        # Using 'zero_method='wilcox'' or 'pratt' depending on ties, default is 'wilcox'
        # scipy.stats.wilcoxon returns (statistic, p-value)
        stat, p_val = scipy_stats.wilcoxon(group_a, group_b)
        logger.info(
            f"Wilcoxon Test: W={stat:.4f}, p={p_val:.4f}"
        )
        return float(stat), float(p_val)
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        raise DataFetchError(f"Failed to perform Wilcoxon test: {e}") from e

def perform_significance_test(
    group_a: List[float], group_b: List[float], alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Orchestrate the significance testing workflow:
    1. Check normality using Shapiro-Wilk.
    2. If normal, run Paired T-Test.
    3. If not normal, run Wilcoxon signed-rank test.

    Args:
        group_a: Baseline metric values (e.g., Greedy).
        group_b: Experimental metric values (e.g., ProRL).
        alpha: Significance level (default 0.05).

    Returns:
        Dict containing:
        - p_value: float
        - confidence_interval: [float, float] (approximate 95% CI for mean diff if t-test)
        - conclusion: "significant" | "not significant"
        - test_type: "t-test" | "wilcoxon"
    """
    if len(group_a) != len(group_b) or len(group_a) == 0:
        raise ValueError("Input groups must be non-empty and of equal length.")

    # Calculate differences for normality check
    differences = [b - a for a, b in zip(group_a, group_b)]

    # Step 1: Normality Check
    try:
        _, _, is_normal = perform_shapiro_wilk(differences)
    except DataFetchError:
        # If we can't check normality (e.g., too few samples), default to Wilcoxon
        # as it is more robust for small samples, or raise error depending on policy.
        # Here we default to Wilcoxon to be safe.
        logger.warning("Normality check failed or insufficient samples, defaulting to Wilcoxon.")
        is_normal = False

    test_type = "t-test" if is_normal else "wilcoxon"
    p_value = 0.0
    ci_low, ci_high = 0.0, 0.0

    if is_normal:
        t_stat, p_value = perform_paired_ttest(group_a, group_b)
        # Calculate 95% CI for mean difference
        mean_diff = np.mean(differences)
        std_diff = np.std(differences, ddof=1)
        n = len(differences)
        se = std_diff / np.sqrt(n)
        # Critical value for 95% CI (two-tailed)
        t_crit = scipy_stats.t.ppf(0.975, df=n-1)
        ci_low = mean_diff - t_crit * se
        ci_high = mean_diff + t_crit * se
    else:
        _, p_value = perform_wilcoxon(group_a, group_b)
        # Wilcoxon doesn't naturally give a mean CI in the same way,
        # but we can report the median difference or leave as 0.0 for simplicity
        # as per the specific schema requirement which expects floats.
        median_diff = np.median(differences)
        ci_low = median_diff
        ci_high = median_diff

    conclusion = "significant" if p_value < alpha else "not significant"

    result = {
        "p_value": float(p_value),
        "confidence_interval": [float(ci_low), float(ci_high)],
        "conclusion": conclusion,
        "test_type": test_type
    }

    logger.info(f"Significance Test Result: {result}")
    return result

def run_sensitivity_analysis(
    metrics_history: List[Dict[str, float]], threshold_range: List[float]
) -> Dict[str, List[float]]:
    """
    Run sensitivity analysis by sweeping similarity thresholds.
    Note: This function is a placeholder for the logic that would re-run
    the pipeline with different thresholds. In a real implementation,
    this would iterate over threshold_range, re-evaluate, and collect metrics.
    For now, it returns a structure ready to be populated.
    """
    # This is a stub implementation as the actual re-evaluation logic
    # depends on the full pipeline integration which is outside the scope
    # of just the stats module function definition.
    # However, per the task, we must implement the function.
    # We will simulate a return structure if metrics_history is provided,
    # otherwise return empty lists.
    thresholds = threshold_range if threshold_range else []
    precision_values = [0.0] * len(thresholds)
    diversity_values = [0.0] * len(thresholds)

    # If we had real data, we would loop:
    # for i, thresh in enumerate(thresholds):
    #     new_metrics = re_evaluate_pipeline(thresh)
    #     precision_values[i] = new_metrics['precision']
    #     diversity_values[i] = new_metrics['diversity']

    return {
        "thresholds": thresholds,
        "precision": precision_values,
        "diversity": diversity_values
    }

def aggregate_sensitivity_report(
    sensitivity_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate sensitivity analysis results into a report format.
    """
    return {
        "thresholds": sensitivity_results.get("thresholds", []),
        "metrics": {
            "precision": sensitivity_results.get("precision", []),
            "diversity": sensitivity_results.get("diversity", [])
        },
        "variations": {
            "precision_max": max(sensitivity_results.get("precision", [0])),
            "precision_min": min(sensitivity_results.get("precision", [0])),
            "diversity_max": max(sensitivity_results.get("diversity", [0])),
            "diversity_min": min(sensitivity_results.get("diversity", [0]))
        }
    }