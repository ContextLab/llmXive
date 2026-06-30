"""
Statistical tests module for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements:
- Paired t-test (scipy.stats.ttest_rel)
- Wilcoxon signed-rank test with effect size and 95% CI (PRIMARY outcome)
- Bootstrap confidence intervals

References:
- FR-007, FR-014, FR-011
- Claim c_7c3d210d: Wilcoxon effect size methodology
- Claim c_55db4237: Explicit count requirement
- Wikipedia: P-value (https://en.wikipedia.org/wiki/P-value)
- Wikipedia: Bootstrapping (statistics) (https://en.wikipedia.org/wiki/Bootstrapping_(statistics))
"""

import numpy as np
from scipy import stats
from typing import Tuple, List, Union, Optional, Dict, Any
import logging
import warnings
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Default significance threshold (alpha) per Wikipedia P-value definition
DEFAULT_ALPHA = 0.05

def paired_ttest(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Perform a paired t-test comparing two conditions.

    Uses scipy.stats.ttest_rel for dependent samples.

    Args:
        condition_a: First condition measurements (e.g., accuracy scores).
        condition_b: Second condition measurements (paired with condition_a).
        alpha: Significance threshold (default 0.05).

    Returns:
        Dictionary containing:
            - statistic: t-statistic value
            - pvalue: two-tailed p-value
            - significant: boolean indicating if p < alpha
            - alpha: the threshold used
            - n_pairs: number of paired observations

    Raises:
        ValueError: If arrays are not the same length or have fewer than 2 elements.
        RuntimeWarning: If variance is zero (perfect correlation).
    """
    a = np.asarray(condition_a)
    b = np.asarray(condition_b)

    if len(a) != len(b):
        raise ValueError(f"Condition arrays must have same length: {len(a)} vs {len(b)}")
    if len(a) < 2:
        raise ValueError(f"At least 2 paired observations required, got {len(a)}")

    logger.debug(f"Paired t-test: n={len(a)}, alpha={alpha}")

    # Perform paired t-test
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        t_stat, p_val = stats.ttest_rel(a, b)

        if w:
            for warning in w:
                logger.warning(f"Statistical warning during t-test: {warning.message}")

    significant = p_val < alpha

    result = {
        "test_name": "paired_ttest",
        "statistic": float(t_stat),
        "pvalue": float(p_val),
        "significant": significant,
        "alpha": alpha,
        "n_pairs": len(a),
        "mean_diff": float(np.mean(a - b)),
        "std_diff": float(np.std(a - b, ddof=1)) if len(a) > 1 else 0.0
    }

    logger.info(
        f"T-test result: t={t_stat:.4f}, p={p_val:.4f}, "
        f"significant={significant} (alpha={alpha})"
    )

    return result

def wilcoxon_effect_size(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test and compute effect size (r).

    This is the PRIMARY outcome metric for the benchmark.

    Formula for effect size r:
        r = Z / sqrt(N)
    where:
        Z = standardized test statistic from Wilcoxon
        N = number of non-zero difference pairs

    Reference:
        Claim c_7c3d210d: Wilcoxon signed-rank with effect size methodology
        Cohen's conventions: 0.1=small, 0.3=medium, 0.5=large

    Args:
        condition_a: First condition measurements.
        condition_b: Second condition measurements (paired).
        alpha: Significance threshold (default 0.05).

    Returns:
        Dictionary containing:
            - statistic: Wilcoxon W statistic
            - pvalue: two-tailed p-value
            - z_score: standardized Z score
            - effect_size_r: r = Z / sqrt(N)
            - effect_size_interpretation: "small", "medium", "large", or "negligible"
            - significant: boolean indicating if p < alpha
            - n_pairs: number of paired observations
            - n_nonzero: number of non-zero differences

    Raises:
        ValueError: If arrays are not same length or have fewer than 2 elements.
    """
    a = np.asarray(condition_a)
    b = np.asarray(condition_b)

    if len(a) != len(b):
        raise ValueError(f"Condition arrays must have same length: {len(a)} vs {len(b)}")
    if len(a) < 2:
        raise ValueError(f"At least 2 paired observations required, got {len(a)}")

    # Compute differences
    diffs = a - b
    nonzero_mask = diffs != 0
    n_nonzero = np.sum(nonzero_mask)

    if n_nonzero < 2:
        logger.warning("Fewer than 2 non-zero differences; Wilcoxon may be unreliable")
        # Return zero effect size if insufficient data
        return {
            "test_name": "wilcoxon_effect_size",
            "statistic": 0.0,
            "pvalue": 1.0,
            "z_score": 0.0,
            "effect_size_r": 0.0,
            "effect_size_interpretation": "insufficient_data",
            "significant": False,
            "n_pairs": len(a),
            "n_nonzero": int(n_nonzero),
            "alpha": alpha,
            "warning": "Insufficient non-zero differences for reliable effect size"
        }

    logger.debug(f"Wilcoxon: n_total={len(a)}, n_nonzero={n_nonzero}, alpha={alpha}")

    # Perform Wilcoxon signed-rank test
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        # Use exact=False for larger samples to get Z-score approximation
        w_stat, p_val = stats.wilcoxon(a, b, zero_method='wilcox', correction=True)

        # Get Z-score if available (scipy returns it for larger samples or with method='approx')
        try:
            # For scipy >= 1.9, we can compute Z manually if not returned
            # Wilcoxon Z = (W - mean_W) / std_W
            # mean_W = n*(n+1)/4, std_W = sqrt(n*(n+1)*(2n+1)/24)
            n = n_nonzero
            mean_w = n * (n + 1) / 4
            std_w = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
            z_score = (w_stat - mean_w) / std_w if std_w > 0 else 0.0
        except Exception as e:
            logger.warning(f"Could not compute Z-score manually: {e}")
            z_score = 0.0

        if w:
            for warning in w:
                logger.warning(f"Statistical warning during Wilcoxon: {warning.message}")

    # Compute effect size r = Z / sqrt(N)
    effect_size_r = z_score / np.sqrt(n_nonzero) if n_nonzero > 0 else 0.0

    # Interpret effect size (Cohen's conventions for r)
    abs_r = abs(effect_size_r)
    if abs_r < 0.1:
        interpretation = "negligible"
    elif abs_r < 0.3:
        interpretation = "small"
    elif abs_r < 0.5:
        interpretation = "medium"
    else:
        interpretation = "large"

    significant = p_val < alpha

    result = {
        "test_name": "wilcoxon_effect_size",
        "statistic": float(w_stat),
        "pvalue": float(p_val),
        "z_score": float(z_score),
        "effect_size_r": float(effect_size_r),
        "effect_size_interpretation": interpretation,
        "significant": significant,
        "n_pairs": len(a),
        "n_nonzero": int(n_nonzero),
        "alpha": alpha,
        "mean_diff": float(np.mean(diffs)),
        "median_diff": float(np.median(diffs)),
        # Explicit count as required by claim c_55db4237
        "explicit_count": int(n_nonzero)
    }

    logger.info(
        f"Wilcoxon result: W={w_stat:.4f}, p={p_val:.4f}, "
        f"r={effect_size_r:.4f} ({interpretation}), significant={significant}"
    )

    return result

def bootstrap_ci(
    values: Union[List[float], np.ndarray],
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute bootstrap confidence interval for the mean.

    Uses non-parametric bootstrap resampling to estimate the confidence interval.

    Args:
        values: Array of values to compute CI for.
        n_bootstrap: Number of bootstrap samples (default 1000).
        confidence: Confidence level (default 0.95 for 95% CI).
        seed: Random seed for reproducibility (optional).

    Returns:
        Dictionary containing:
            - mean: sample mean
            - ci_lower: lower bound of confidence interval
            - ci_upper: upper bound of confidence interval
            - ci_width: width of confidence interval
            - confidence: confidence level used
            - n_bootstrap: number of bootstrap samples
            - n_samples: number of original samples

    Reference:
        Wikipedia: Bootstrapping (statistics)
        Claim c_e50ac6bc: Bootstrap CI methodology
    """
    values = np.asarray(values)
    n = len(values)

    if n < 2:
        raise ValueError(f"At least 2 samples required for bootstrap, got {n}")

    if seed is not None:
        np.random.seed(seed)

    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    logger.debug(f"Bootstrap CI: n={n}, n_bootstrap={n_bootstrap}, confidence={confidence}")

    # Generate bootstrap samples
    bootstrap_means = []
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample = np.random.choice(values, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))

    bootstrap_means = np.array(bootstrap_means)

    ci_lower = float(np.percentile(bootstrap_means, lower_percentile))
    ci_upper = float(np.percentile(bootstrap_means, upper_percentile))
    ci_width = ci_upper - ci_lower
    sample_mean = float(np.mean(values))

    result = {
        "test_name": "bootstrap_ci",
        "mean": sample_mean,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ci_width": ci_width,
        "confidence": confidence,
        "n_bootstrap": n_bootstrap,
        "n_samples": n,
        "std_bootstrap": float(np.std(bootstrap_means, ddof=1))
    }

    logger.info(
        f"Bootstrap CI: mean={sample_mean:.4f}, "
        f"{confidence*100:.0f}% CI=[{ci_lower:.4f}, {ci_upper:.4f}], "
        f"width={ci_width:.4f}"
    )

    return result

def run_full_statistical_analysis(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = DEFAULT_ALPHA,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a complete statistical analysis comparing two conditions.

    This is the main entry point for statistical evaluation in the benchmark.

    Args:
        condition_a: First condition measurements.
        condition_b: Second condition measurements.
        alpha: Significance threshold (default 0.05).
        n_bootstrap: Number of bootstrap samples for CI.
        confidence: Confidence level for bootstrap CI.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing all statistical test results:
            - paired_ttest: results from paired t-test
            - wilcoxon: results from Wilcoxon signed-rank (PRIMARY)
            - bootstrap_ci_a: bootstrap CI for condition A
            - bootstrap_ci_b: bootstrap CI for condition B
            - summary: high-level summary of findings

    Note:
        The Wilcoxon effect size is treated as the PRIMARY outcome per FR-007.
    """
    logger.info("Starting full statistical analysis")

    # Run individual tests
    ttest_result = paired_ttest(condition_a, condition_b, alpha=alpha)
    wilcoxon_result = wilcoxon_effect_size(condition_a, condition_b, alpha=alpha)
    ci_a = bootstrap_ci(condition_a, n_bootstrap=n_bootstrap, confidence=confidence, seed=seed)
    ci_b = bootstrap_ci(condition_b, n_bootstrap=n_bootstrap, confidence=confidence, seed=seed)

    # Generate summary
    summary = {
        "primary_outcome": "wilcoxon_effect_size",
        "primary_effect_size": wilcoxon_result["effect_size_r"],
        "primary_interpretation": wilcoxon_result["effect_size_interpretation"],
        "ttest_significant": ttest_result["significant"],
        "wilcoxon_significant": wilcoxon_result["significant"],
        "agreement": ttest_result["significant"] == wilcoxon_result["significant"],
        "ci_overlap": not (
            ci_a["ci_upper"] < ci_b["ci_lower"] or ci_b["ci_upper"] < ci_a["ci_lower"]
        ),
        "sample_size": ttest_result["n_pairs"],
        "alpha": alpha,
        "confidence": confidence
    }

    full_result = {
        "paired_ttest": ttest_result,
        "wilcoxon_effect_size": wilcoxon_result,
        "bootstrap_ci_condition_a": ci_a,
        "bootstrap_ci_condition_b": ci_b,
        "summary": summary
    }

    logger.info("Statistical analysis complete")
    return full_result