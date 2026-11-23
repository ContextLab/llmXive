import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from scipy import stats as scipy_stats
from utils.logging import get_logger, info, debug, warning, error

logger = get_logger(__name__)

def calculate_paired_ttest(
    baseline_values: List[float],
    cap_values: List[float]
) -> Dict[str, float]:
    """
    Perform a paired t-test between baseline and CAP results.

    Args:
        baseline_values: List of metric values (e.g., AUCC) from baseline runs.
        cap_values: List of metric values from CAP runs.

    Returns:
        Dictionary containing 't_statistic' and 'p_value'.
    """
    if len(baseline_values) != len(cap_values):
        error("Baseline and CAP value lists must have equal length for paired t-test.")
        raise ValueError("Input lists must have equal length.")

    if len(baseline_values) < 2:
        warning("Less than 2 samples provided; t-test may be unreliable.")

    t_stat, p_val = scipy_stats.ttest_rel(baseline_values, cap_values)

    result = {
        "t_statistic": float(t_stat),
        "p_value": float(p_val)
    }

    debug(f"Paired t-test result: t={t_stat:.4f}, p={p_val:.4f}")
    return result

def calculate_effect_size(
    baseline_values: List[float],
    cap_values: List[float]
) -> Dict[str, float]:
    """
    Calculate Cohen's d effect size for the difference between two groups.

    Args:
        baseline_values: List of metric values from baseline runs.
        cap_values: List of metric values from CAP runs.

    Returns:
        Dictionary containing 'cohen_d' and 'mean_difference'.
    """
    if len(baseline_values) != len(cap_values):
        error("Baseline and CAP value lists must have equal length.")
        raise ValueError("Input lists must have equal length.")

    baseline_arr = np.array(baseline_values)
    cap_arr = np.array(cap_values)

    mean_diff = np.mean(cap_arr) - np.mean(baseline_arr)

    # Pooled standard deviation
    n1, n2 = len(baseline_arr), len(cap_arr)
    var1 = np.var(baseline_arr, ddof=1)
    var2 = np.var(cap_arr, ddof=1)

    if n1 + n2 - 2 == 0:
        pooled_std = 0.0
    else:
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        pooled_std = np.sqrt(pooled_var)

    cohen_d = mean_diff / pooled_std if pooled_std > 0 else 0.0

    result = {
        "cohen_d": float(cohen_d),
        "mean_difference": float(mean_diff)
    }

    debug(f"Effect size (Cohen's d): {cohen_d:.4f}")
    return result

def bootstrap_confidence_interval(
    values: List[float],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate bootstrap confidence interval for a metric distribution.

    Args:
        values: List of metric values.
        n_bootstrap: Number of bootstrap samples.
        confidence_level: Confidence level (e.g., 0.95).
        seed: Optional random seed for reproducibility.

    Returns:
        Dictionary containing 'mean', 'std', 'ci_lower', and 'ci_upper'.
    """
    if seed is not None:
        np.random.seed(seed)

    values_arr = np.array(values)
    n = len(values_arr)
    bootstrap_means = []

    for _ in range(n_bootstrap):
        sample = np.random.choice(values_arr, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))

    bootstrap_means = np.array(bootstrap_means)
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))

    result = {
        "mean": float(np.mean(values_arr)),
        "std": float(np.std(values_arr)),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper)
    }

    debug(f"Bootstrap CI ({confidence_level*100}%): [{ci_lower:.4f}, {ci_upper:.4f}]")
    return result

def check_catastrophic_forgetting(
    baseline_final_acc: List[float],
    cap_final_acc: List[float],
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Check for catastrophic forgetting by comparing final accuracy on held-out data
    between baseline and CAP models.

    Catastrophic forgetting is indicated if the CAP model's final accuracy is
    significantly lower than the baseline's final accuracy, beyond a specified threshold.

    Args:
        baseline_final_acc: List of final accuracy values from baseline runs.
        cap_final_acc: List of final accuracy values from CAP runs.
        threshold: Minimum acceptable drop in accuracy to be considered catastrophic.

    Returns:
        Dictionary containing:
            - 'mean_baseline': Mean final accuracy of baseline.
            - 'mean_cap': Mean final accuracy of CAP.
            - 'accuracy_drop': Mean baseline - Mean CAP.
            - 'is_forgetting': Boolean indicating if drop exceeds threshold.
            - 't_statistic': T-statistic from paired t-test.
            - 'p_value': P-value from paired t-test.
            - 'statistically_significant': Boolean indicating if p < 0.05.
    """
    if len(baseline_final_acc) != len(cap_final_acc):
        error("Baseline and CAP final accuracy lists must have equal length.")
        raise ValueError("Input lists must have equal length.")

    if len(baseline_final_acc) == 0:
        warning("No data provided for catastrophic forgetting check.")
        return {
            "mean_baseline": 0.0,
            "mean_cap": 0.0,
            "accuracy_drop": 0.0,
            "is_forgetting": False,
            "t_statistic": 0.0,
            "p_value": 1.0,
            "statistically_significant": False
        }

    baseline_arr = np.array(baseline_final_acc)
    cap_arr = np.array(cap_final_acc)

    mean_baseline = float(np.mean(baseline_arr))
    mean_cap = float(np.mean(cap_arr))
    accuracy_drop = mean_baseline - mean_cap

    # Perform paired t-test to check if the drop is statistically significant
    t_stat, p_val = scipy_stats.ttest_rel(baseline_arr, cap_arr)

    is_forgetting = accuracy_drop > threshold
    statistically_significant = p_val < 0.05

    result = {
        "mean_baseline": mean_baseline,
        "mean_cap": mean_cap,
        "accuracy_drop": accuracy_drop,
        "is_forgetting": is_forgetting,
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "statistically_significant": statistically_significant
    }

    if is_forgetting:
        warning(f"Catastrophic forgetting detected: accuracy drop of {accuracy_drop:.4f} exceeds threshold {threshold}.")
    else:
        debug(f"No catastrophic forgetting detected: accuracy drop of {accuracy_drop:.4f} (threshold: {threshold}).")

    return result