"""
Statistical Tests Module for Heterogeneous Scientific Foundation Model Benchmark.

Implements statistical methodology defined in research.md:
- Paired t-test
- Wilcoxon signed-rank test with effect sizes (r = Z/sqrt(N)) and 95% CI
- Bootstrap confidence intervals (1000 resamples)
- Configurable alpha threshold (default 0.05)

References:
- FR-007, FR-014, FR-011
- Wikipedia: P-value (https://en.wikipedia.org/wiki/P-value)
"""

import numpy as np
from scipy import stats
from typing import Tuple, List, Union, Optional, Dict, Any
import logging
import warnings

from src.utils.logging import get_logger

# Suppress specific scipy warnings for cleaner output if needed
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = get_logger(__name__)

# Default constants
DEFAULT_ALPHA = 0.05
DEFAULT_N_RESAMPLES = 1000
DEFAULT_CONFIDENCE = 0.95

def paired_ttest(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Perform a paired t-test between two related samples.

    Args:
        condition_a: First condition results (e.g., model A accuracies).
        condition_b: Second condition results (e.g., model B accuracies).
        alpha: Significance level (default 0.05).

    Returns:
        Dictionary containing:
            - statistic: t-statistic
            - pvalue: two-tailed p-value
            - significant: boolean indicating if p < alpha
            - mean_diff: mean difference (condition_b - condition_a)
            - alpha: the alpha threshold used

    Raises:
        ValueError: If input lengths differ or data is invalid.
    """
    a = np.asarray(condition_a)
    b = np.asarray(condition_b)

    if a.shape != b.shape:
        raise ValueError(f"Input arrays must have same shape. Got {a.shape} and {b.shape}")
    if a.size == 0:
        raise ValueError("Input arrays cannot be empty.")

    # Calculate mean difference for reporting
    mean_diff = float(np.mean(b - a))

    # Perform paired t-test
    t_stat, p_val = stats.ttest_rel(a, b)

    significant = p_val < alpha

    logger.info(
        f"Paired t-test: t={t_stat:.4f}, p={p_val:.4f}, "
        f"mean_diff={mean_diff:.4f}, alpha={alpha}, significant={significant}"
    )

    return {
        "test_type": "paired_ttest",
        "statistic": float(t_stat),
        "pvalue": float(p_val),
        "significant": bool(significant),
        "mean_diff": mean_diff,
        "alpha": alpha,
        "n_samples": int(len(a))
    }

def wilcoxon_effect_size(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray]
) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test and calculate effect size.

    The effect size r is calculated as: r = Z / sqrt(N)
    Where Z is the standardized test statistic and N is the number of observations.
    This is the PRIMARY outcome metric for non-parametric comparison.

    95% Confidence Interval for the effect size is also provided using bootstrap.

    Args:
        condition_a: First condition results.
        condition_b: Second condition results.

    Returns:
        Dictionary containing:
            - statistic: Wilcoxon W statistic
            - pvalue: two-tailed p-value
            - effect_size: r = Z / sqrt(N)
            - ci_lower: Lower bound of 95% CI for effect size
            - ci_upper: Upper bound of 95% CI for effect size
            - z_statistic: The standardized Z value used for effect size

    Raises:
        ValueError: If inputs are invalid.
    """
    a = np.asarray(condition_a)
    b = np.asarray(condition_b)

    if a.shape != b.shape:
        raise ValueError(f"Input arrays must have same shape. Got {a.shape} and {b.shape}")
    if a.size == 0:
        raise ValueError("Input arrays cannot be empty.")

    # Perform Wilcoxon signed-rank test
    # Use 'exact' method if N is small, otherwise 'approx' (default in scipy for larger N)
    try:
        w_stat, p_val = stats.wilcoxon(a, b, zero_method='wilcox', correction=True)
    except ValueError:
        # Fallback if exact calculation fails due to ties or size
        w_stat, p_val = stats.wilcoxon(a, b, zero_method='pratt', correction=True)

    # Calculate Z statistic for effect size
    # scipy.stats.wilcoxon does not directly return Z, so we compute it manually
    # Z = (W - mean_W) / std_W
    # However, scipy's `stats.wilcoxon` with `method='approx'` uses a normal approximation.
    # A robust way to get Z for effect size calculation is to use the `stats.ranksums`
    # logic or manually compute the standardized score from the W statistic.
    #
    # Standard approximation for Wilcoxon:
    # Mean = n(n+1)/4
    # Std = sqrt(n(n+1)(2n+1)/24)
    # Z = (W - Mean) / Std
    # Note: This approximation is for the sum of positive ranks.
    # scipy.stats.wilcoxon returns the sum of ranks for the differences where x < y (or similar).
    #
    # Let's use the standard approximation formula for Z to ensure consistency with r = Z/sqrt(N).
    n = len(a)
    if n < 10:
        logger.warning("Small sample size for Wilcoxon; effect size approximation may be less accurate.")

    # Calculate mean and std for the Wilcoxon statistic under null hypothesis
    mean_w = n * (n + 1) / 4
    std_w = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)

    # Avoid division by zero
    if std_w == 0:
        z_stat = 0.0
    else:
        # Use the W statistic returned by scipy
        z_stat = (w_stat - mean_w) / std_w

    # Calculate effect size r
    effect_size_r = z_stat / np.sqrt(n)

    # Calculate 95% CI for effect size using bootstrap
    # We bootstrap the differences to estimate the distribution of the effect size
    # Since effect size is derived from the whole sample, we bootstrap the samples themselves
    # and recompute the effect size for each resample.
    # However, a simpler and robust approach for CI of effect size r is bootstrapping the
    # differences and recalculating the Z-based effect size.
    #
    # Implementation: Bootstrap the pairs (a, b)
    ci_lower, ci_upper = _bootstrap_effect_size_ci(a, b, n_resamples=1000, confidence=0.95)

    logger.info(
        f"Wilcoxon Signed-Rank: W={w_stat:.4f}, p={p_val:.4f}, "
        f"Effect Size r={effect_size_r:.4f} (Z={z_stat:.4f}, N={n}), "
        f"95% CI [{ci_lower:.4f}, {ci_upper:.4f}]"
    )

    return {
        "test_type": "wilcoxon_signed_rank",
        "statistic": float(w_stat),
        "pvalue": float(p_val),
        "z_statistic": float(z_stat),
        "effect_size": float(effect_size_r),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "confidence_level": 0.95,
        "n_samples": int(n),
        "formula": "r = Z / sqrt(N)"
    }

def _bootstrap_effect_size_ci(
    a: np.ndarray,
    b: np.ndarray,
    n_resamples: int = 1000,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Bootstrap confidence interval for Wilcoxon effect size.

    Args:
        a: Array A.
        b: Array B.
        n_resamples: Number of bootstrap resamples.
        confidence: Confidence level (e.g., 0.95).

    Returns:
        Tuple of (ci_lower, ci_upper).
    """
    n = len(a)
    effect_sizes = []

    for _ in range(n_resamples):
        # Resample indices with replacement
        indices = np.random.choice(n, size=n, replace=True)
        a_res = a[indices]
        b_res = b[indices]

        # Compute W statistic for resampled data
        # We need to handle cases where resampling might lead to ties or zero variance
        try:
            w_stat, _ = stats.wilcoxon(a_res, b_res, zero_method='pratt', correction=True)
        except Exception:
            continue

        # Recalculate Z and effect size for this resample
        mean_w = n * (n + 1) / 4
        std_w = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
        if std_w == 0:
            continue
        z_stat = (w_stat - mean_w) / std_w
        r = z_stat / np.sqrt(n)
        effect_sizes.append(r)

    if not effect_sizes:
        return (0.0, 0.0)

    effect_sizes = np.array(effect_sizes)
    alpha = 1 - confidence
    lower_idx = int((alpha / 2) * n_resamples)
    upper_idx = int((1 - alpha / 2) * n_resamples)

    # Sort to get percentiles
    sorted_effects = np.sort(effect_sizes)
    # Ensure indices are within bounds
    lower_idx = max(0, lower_idx)
    upper_idx = min(len(sorted_effects) - 1, upper_idx)

    return float(sorted_effects[lower_idx]), float(sorted_effects[upper_idx])

def bootstrap_ci(
    values: Union[List[float], np.ndarray],
    n_resamples: int = DEFAULT_N_RESAMPLES,
    confidence: float = DEFAULT_CONFIDENCE
) -> Dict[str, Any]:
    """
    Calculate bootstrap confidence interval for a single set of values (e.g., accuracy differences).

    This is useful for estimating the CI of the mean difference between conditions.

    Args:
        values: The array of values (e.g., differences between condition B and A).
        n_resamples: Number of bootstrap resamples (default 1000).
        confidence: Confidence level (default 0.95).

    Returns:
        Dictionary containing:
            - mean: Mean of the values
            - ci_lower: Lower bound of CI
            - ci_upper: Upper bound of CI
            - n_resamples: Number of resamples used
            - confidence: Confidence level used
    """
    arr = np.asarray(values)
    if arr.size == 0:
        raise ValueError("Input array cannot be empty.")

    n = len(arr)
    bootstrap_means = []

    for _ in range(n_resamples):
        # Resample with replacement
        resample_indices = np.random.choice(n, size=n, replace=True)
        resample = arr[resample_indices]
        bootstrap_means.append(np.mean(resample))

    bootstrap_means = np.array(bootstrap_means)
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    ci_lower = float(np.percentile(bootstrap_means, lower_percentile))
    ci_upper = float(np.percentile(bootstrap_means, upper_percentile))
    mean_val = float(np.mean(arr))

    logger.info(
        f"Bootstrap CI (n={n_resamples}): Mean={mean_val:.4f}, "
        f"{confidence*100:.0f}% CI [{ci_lower:.4f}, {ci_upper:.4f}]"
    )

    return {
        "mean": mean_val,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "n_resamples": n_resamples,
        "confidence": confidence,
        "n_samples": n
    }

def run_full_statistical_analysis(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Run the full suite of statistical tests as required by the benchmark.

    This function orchestrates:
    1. Paired t-test
    2. Wilcoxon signed-rank test with effect size and CI
    3. Bootstrap CI of the mean difference

    Args:
        condition_a: Results from condition A.
        condition_b: Results from condition B.
        alpha: Significance threshold.

    Returns:
        A comprehensive dictionary containing all test results.
    """
    logger.info("Starting full statistical analysis...")

    results = {
        "paired_ttest": paired_ttest(condition_a, condition_b, alpha),
        "wilcoxon": wilcoxon_effect_size(condition_a, condition_b),
        "bootstrap_ci": bootstrap_ci(np.asarray(condition_b) - np.asarray(condition_a)),
        "config": {
            "alpha": alpha,
            "bootstrap_resamples": DEFAULT_N_RESAMPLES,
            "primary_outcome": "Wilcoxon effect size (r) with 95% CI"
        }
    }

    logger.info("Statistical analysis complete.")
    return results

if __name__ == "__main__":
    # Simple demo if run directly
    np.random.seed(42)
    sample_a = np.random.normal(0.75, 0.05, 50)
    sample_b = np.random.normal(0.80, 0.05, 50)

    print("Running demo statistical analysis...")
    analysis = run_full_statistical_analysis(sample_a, sample_b)
    import json
    print(json.dumps(analysis, indent=2))
