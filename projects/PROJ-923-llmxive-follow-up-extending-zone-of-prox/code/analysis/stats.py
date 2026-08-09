import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from scipy import stats
from utils.logging import get_logger

logger = get_logger(__name__)

def paired_ttest_aucc(
    baseline_aucc: List[float],
    cap_aucc: List[float]
) -> Dict[str, float]:
    """
    Perform a paired t-test comparing AUCC distributions between baseline and CAP methods.

    Args:
        baseline_aucc: List of AUCC values from baseline simulation runs.
        cap_aucc: List of AUCC values from CAP simulation runs (paired by seed/run).

    Returns:
        Dictionary containing t-statistic, p-value, and confidence interval.
    """
    if len(baseline_aucc) != len(cap_aucc):
        raise ValueError(
            f"Paired t-test requires equal sample sizes. "
            f"Got {len(baseline_aucc)} baseline vs {len(cap_aucc)} CAP."
        )

    if len(baseline_aucc) < 2:
        raise ValueError(
            "Paired t-test requires at least 2 samples per group."
        )

    baseline_arr = np.array(baseline_aucc)
    cap_arr = np.array(cap_aucc)

    t_stat, p_val = stats.ttest_rel(baseline_arr, cap_arr)

    # Calculate 95% confidence interval of the mean difference
    diff = cap_arr - baseline_arr
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    n = len(diff)
    se = std_diff / np.sqrt(n)
    conf_int = stats.t.interval(
        0.95, df=n-1, loc=mean_diff, scale=se
    )

    logger.info(
        f"Paired T-Test Results: t={t_stat:.4f}, p={p_val:.4f}, "
        f"mean_diff={mean_diff:.4f}, CI={conf_int}"
    )

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "mean_difference": float(mean_diff),
        "ci_lower": float(conf_int[0]),
        "ci_upper": float(conf_int[1]),
        "sample_size": n
    }

def independent_ttest_aucc(
    group_a_aucc: List[float],
    group_b_aucc: List[float],
    equal_var: bool = True
) -> Dict[str, float]:
    """
    Perform an independent samples t-test comparing two AUCC distributions.

    Args:
        group_a_aucc: List of AUCC values for group A.
        group_b_aucc: List of AUCC values for group B.
        equal_var: If True, perform Student's t-test; else Welch's t-test.

    Returns:
        Dictionary containing t-statistic, p-value, and confidence interval.
    """
    if len(group_a_aucc) < 2 or len(group_b_aucc) < 2:
        raise ValueError(
            "Independent t-test requires at least 2 samples per group."
        )

    arr_a = np.array(group_a_aucc)
    arr_b = np.array(group_b_aucc)

    if equal_var:
        t_stat, p_val = stats.ttest_ind(arr_a, arr_b, equal_var=True)
    else:
        t_stat, p_val = stats.ttest_ind(arr_a, arr_b, equal_var=False)

    # Calculate 95% CI for difference in means
    mean_a, mean_b = np.mean(arr_a), np.mean(arr_b)
    std_a, std_b = np.std(arr_a, ddof=1), np.std(arr_b, ddof=1)
    n_a, n_b = len(arr_a), len(arr_b)

    # Pooled standard error (for equal variance) or Welch's approximation
    if equal_var:
        pooled_var = ((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2)
        se = np.sqrt(pooled_var * (1/n_a + 1/n_b))
        df = n_a + n_b - 2
    else:
        se = np.sqrt(std_a**2/n_a + std_b**2/n_b)
        # Welch-Satterthwaite equation for degrees of freedom
        df = (std_a**2/n_a + std_b**2/n_b)**2 / (
            (std_a**2/n_a)**2 / (n_a-1) + (std_b**2/n_b)**2 / (n_b-1)
        )

    mean_diff = mean_b - mean_a
    conf_int = stats.t.interval(0.95, df=df, loc=mean_diff, scale=se)

    logger.info(
        f"Independent T-Test Results: t={t_stat:.4f}, p={p_val:.4f}, "
        f"mean_diff={mean_diff:.4f}, CI={conf_int}, df={df:.2f}"
    )

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "mean_difference": float(mean_diff),
        "ci_lower": float(conf_int[0]),
        "ci_upper": float(conf_int[1]),
        "sample_size_a": n_a,
        "sample_size_b": n_b,
        "degrees_of_freedom": float(df),
        "equal_variance_assumed": equal_var
    }

def calculate_effect_size(
    group_a: List[float],
    group_b: List[float],
    method: str = "cohen_d"
) -> float:
    """
    Calculate effect size between two groups.

    Args:
        group_a: List of values for group A.
        group_b: List of values for group B.
        method: Effect size method ("cohen_d" or "hedges_g").

    Returns:
        Effect size value (Cohen's d or Hedges' g).
    """
    arr_a = np.array(group_a)
    arr_b = np.array(group_b)

    n_a, n_b = len(arr_a), len(arr_b)
    mean_a, mean_b = np.mean(arr_a), np.mean(arr_b)
    std_a, std_b = np.std(arr_a, ddof=1), np.std(arr_b, ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))

    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero. Returning 0 effect size.")
        return 0.0

    cohen_d = (mean_b - mean_a) / pooled_std

    if method == "cohen_d":
        return float(cohen_d)
    elif method == "hedges_g":
        # Hedges' g correction factor
        correction = 1 - (3 / (4 * (n_a + n_b) - 9))
        return float(cohen_d * correction)
    else:
        raise ValueError(f"Unknown effect size method: {method}")

def confidence_interval_mean(
    data: List[float],
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate the confidence interval for the mean of a dataset.

    Args:
        data: List of numerical values.
        confidence: Confidence level (0 to 1).

    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    arr = np.array(data)
    n = len(arr)
    mean = np.mean(arr)
    std_err = np.std(arr, ddof=1) / np.sqrt(n)

    ci = stats.t.interval(confidence, df=n-1, loc=mean, scale=std_err)
    return float(ci[0]), float(ci[1])

def check_normality(
    data: List[float],
    alpha: float = 0.05
) -> Dict[str, Union[bool, float]]:
    """
    Check if data follows a normal distribution using Shapiro-Wilk test.

    Args:
        data: List of numerical values.
        alpha: Significance level for the test.

    Returns:
        Dictionary with 'is_normal' boolean and 'p_value'.
    """
    if len(data) < 3:
        logger.warning("Shapiro-Wilk test requires at least 3 samples.")
        return {"is_normal": True, "p_value": 1.0, "statistic": 0.0}

    stat, p_val = stats.shapiro(data)
    is_normal = p_val > alpha

    logger.info(
        f"Normality Test: Shapiro-Wilk statistic={stat:.4f}, p={p_val:.4f}, "
        f"normal={is_normal}"
    )

    return {
        "is_normal": bool(is_normal),
        "p_value": float(p_val),
        "statistic": float(stat)
    }

def summarize_aucc_distribution(
    aucc_values: List[float]
) -> Dict[str, float]:
    """
    Generate summary statistics for an AUCC distribution.

    Args:
        aucc_values: List of AUCC values.

    Returns:
        Dictionary with mean, std, min, max, and median.
    """
    arr = np.array(aucc_values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr, ddof=1)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr)),
        "count": len(arr)
    }

def check_catastrophic_forgetting(
    baseline_final_acc: List[float],
    cap_final_acc: List[float],
    threshold: float = 0.05
) -> Dict[str, Union[bool, float, Dict[str, float]]]:
    """
    Check for catastrophic forgetting by comparing final accuracy on held-out data
    between baseline and CAP methods.

    Catastrophic forgetting is flagged if the CAP method shows a statistically
    significant drop in final accuracy compared to the baseline, exceeding the
    specified threshold.

    Args:
        baseline_final_acc: List of final accuracy values from baseline runs.
        cap_final_acc: List of final accuracy values from CAP runs.
        threshold: Minimum absolute difference to consider as significant forgetting.

    Returns:
        Dictionary containing:
            - 'has_forgetting': Boolean indicating if catastrophic forgetting detected.
            - 'mean_baseline_acc': Mean accuracy of baseline.
            - 'mean_cap_acc': Mean accuracy of CAP.
            - 'accuracy_drop': Absolute drop in accuracy (baseline - cap).
            - 'p_value': P-value from independent t-test.
            - 'effect_size': Cohen's d of the drop.
    """
    if len(baseline_final_acc) < 2 or len(cap_final_acc) < 2:
        raise ValueError(
            "Catastrophic forgetting check requires at least 2 samples per group."
        )

    baseline_arr = np.array(baseline_final_acc)
    cap_arr = np.array(cap_final_acc)

    mean_baseline = np.mean(baseline_arr)
    mean_cap = np.mean(cap_arr)
    accuracy_drop = mean_baseline - mean_cap

    # Perform independent t-test to see if the drop is statistically significant
    try:
        _, p_val = stats.ttest_ind(baseline_arr, cap_arr, equal_var=False)
    except Exception as e:
        logger.error(f"Error performing t-test for forgetting check: {e}")
        p_val = 1.0

    # Calculate effect size
    effect_size = calculate_effect_size(baseline_final_acc, cap_final_acc, method="cohen_d")

    # Determine if catastrophic forgetting occurred
    # Criteria: Significant drop (p < 0.05) AND drop magnitude > threshold
    is_significant = p_val < 0.05
    exceeds_threshold = accuracy_drop > threshold
    has_forgetting = is_significant and exceeds_threshold

    logger.info(
        f"Catastrophic Forgetting Check: "
        f"Baseline Acc={mean_baseline:.4f}, CAP Acc={mean_cap:.4f}, "
        f"Drop={accuracy_drop:.4f}, p={p_val:.4f}, "
        f"Threshold={threshold}, Detected={has_forgetting}"
    )

    return {
        "has_forgetting": bool(has_forgetting),
        "is_statistically_significant": bool(is_significant),
        "exceeds_threshold": bool(exceeds_threshold),
        "mean_baseline_acc": float(mean_baseline),
        "mean_cap_acc": float(mean_cap),
        "accuracy_drop": float(accuracy_drop),
        "p_value": float(p_val),
        "effect_size": float(effect_size),
        "threshold_used": float(threshold)
    }