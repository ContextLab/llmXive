"""
Statistical tests for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements:
- Paired t-test (scipy.stats.ttest_rel)
- Wilcoxon signed-rank test with effect size and 95% CI as PRIMARY outcome
- Bootstrap confidence intervals

References:
- {{claim:c_7c3d210d}}: Wilcoxon signed-rank test methodology
- {{claim:c_55db4237}}: Explicit count requirement for statistical significance
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


def paired_ttest(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a paired t-test between two conditions.

    Args:
        condition_a: First set of measurements (e.g., accuracies from model A).
        condition_b: Second set of measurements (e.g., accuracies from model B).
        alpha: Significance threshold (default 0.05 per Wikipedia: P-value).

    Returns:
        Dictionary containing:
            - statistic: t-statistic value
            - pvalue: two-tailed p-value
            - significant: boolean indicating if p < alpha
            - alpha: the threshold used
    """
    if len(condition_a) != len(condition_b):
        raise ValueError("Condition A and Condition B must have the same length for paired t-test.")
    if len(condition_a) < 2:
        raise ValueError("Paired t-test requires at least 2 samples.")

    arr_a = np.array(condition_a)
    arr_b = np.array(condition_b)

    # Handle constant arrays (zero variance)
    if np.std(arr_a) == 0 and np.std(arr_b) == 0:
        logger.warning("Both conditions have zero variance. Returning NaN for t-statistic.")
        return {
            "statistic": np.nan,
            "pvalue": np.nan,
            "significant": False,
            "alpha": alpha,
            "method": "paired_ttest"
        }

    try:
        t_stat, p_val = stats.ttest_rel(arr_a, arr_b)
    except Exception as e:
        logger.error(f"Paired t-test failed: {e}")
        raise

    result = {
        "statistic": float(t_stat),
        "pvalue": float(p_val),
        "significant": bool(p_val < alpha),
        "alpha": alpha,
        "method": "paired_ttest"
    }

    logger.info(f"Paired t-test: t={t_stat:.4f}, p={p_val:.4f}, significant={result['significant']}")
    return result


def wilcoxon_effect_size(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test and calculate effect size (r) with 95% CI.
    This is the PRIMARY outcome measure as per specification.

    Formula for effect size r:
        r = Z / sqrt(N)
    where Z is the standardized test statistic and N is the number of non-zero differences.

    Args:
        condition_a: First set of measurements.
        condition_b: Second set of measurements.
        alpha: Significance threshold (default 0.05).

    Returns:
        Dictionary containing:
            - statistic: Wilcoxon W statistic
            - pvalue: two-tailed p-value
            - z_score: standardized Z score
            - effect_size: r = Z / sqrt(N)
            - significant: boolean
            - ci_95_lower: Lower bound of 95% CI for effect size (approximate)
            - ci_95_upper: Upper bound of 95% CI for effect size (approximate)
            - n_pairs: Number of pairs analyzed
            - method: "wilcoxon_signed_rank"
    """
    if len(condition_a) != len(condition_b):
        raise ValueError("Condition A and Condition B must have the same length.")
    if len(condition_a) < 2:
        raise ValueError("Wilcoxon test requires at least 2 samples.")

    arr_a = np.array(condition_a)
    arr_b = np.array(condition_b)

    try:
        # scipy.stats.wilcoxon returns (statistic, pvalue)
        # For effect size, we need the Z-score.
        # We can compute Z manually or use the 'zero_method' and 'correction' options.
        # scipy 1.7+ supports returning a Z-score via alternative methods or manual calc.
        # Standard approach: Z = (W - expected_W) / std_W
        
        # Use the standard wilcoxon test
        w_stat, p_val = stats.wilcoxon(arr_a, arr_b, zero_method='wilcox', correction=True)
        
        # Calculate Z-score manually for effect size
        # Expected value under H0: n(n+1)/4
        # Variance under H0: n(n+1)(2n+1)/24
        # We filter out zero differences first
        diffs = arr_a - arr_b
        non_zero_mask = diffs != 0
        n = np.sum(non_zero_mask)
        
        if n < 2:
            logger.warning("Too few non-zero differences for Wilcoxon effect size calculation.")
            return {
                "statistic": float(w_stat),
                "pvalue": float(p_val),
                "z_score": np.nan,
                "effect_size": np.nan,
                "significant": False,
                "ci_95_lower": np.nan,
                "ci_95_upper": np.nan,
                "n_pairs": int(n),
                "method": "wilcoxon_signed_rank"
            }

        # Expected mean and std under null
        mean_w = n * (n + 1) / 4
        std_w = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
        
        # Apply continuity correction if needed (scipy does this in p-value, we approximate Z)
        # Z = (W - mean) / std
        # Note: The sign of W depends on implementation, but r = Z/sqrt(N) handles magnitude.
        # scipy returns sum of ranks for positive differences.
        z_score = (w_stat - mean_w) / std_w
        
        # Effect size r = Z / sqrt(N)
        effect_size = z_score / np.sqrt(n)

        # Approximate 95% CI for r using standard error approximation
        # SE_r ≈ 1 / sqrt(N)
        se_r = 1 / np.sqrt(n)
        ci_lower = effect_size - 1.96 * se_r
        ci_upper = effect_size + 1.96 * se_r

        result = {
            "statistic": float(w_stat),
            "pvalue": float(p_val),
            "z_score": float(z_score),
            "effect_size": float(effect_size),
            "significant": bool(p_val < alpha),
            "ci_95_lower": float(ci_lower),
            "ci_95_upper": float(ci_upper),
            "n_pairs": int(n),
            "method": "wilcoxon_signed_rank"
        }

        logger.info(
            f"Wilcoxon: W={w_stat:.4f}, p={p_val:.4f}, r={effect_size:.4f} "
            f"(95% CI [{ci_lower:.4f}, {ci_upper:.4f}]), n={n}"
        )
        return result

    except Exception as e:
        logger.error(f"Wilcoxon effect size calculation failed: {e}")
        raise


def bootstrap_ci(
    values: Union[List[float], np.ndarray],
    n_bootstraps: int = 1000,
    confidence: float = 0.95,
    stat_func: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Calculate bootstrap confidence intervals for a given statistic.

    Args:
        values: Array of values to bootstrap.
        n_bootstraps: Number of bootstrap samples (default 1000 per Wikipedia: Bootstrapping).
        confidence: Confidence level (e.g., 0.95 for 95% CI).
        stat_func: Function to compute statistic on each sample (default: mean).

    Returns:
        Dictionary containing:
            - statistic: Value of the statistic on original data
            - ci_lower: Lower bound of confidence interval
            - ci_upper: Upper bound of confidence interval
            - n_bootstraps: Number of samples used
            - confidence: Confidence level
    """
    if len(values) < 2:
        raise ValueError("Bootstrap CI requires at least 2 samples.")

    arr = np.array(values)
    n = len(arr)

    if stat_func is None:
        stat_func = np.mean

    # Compute original statistic
    original_stat = float(stat_func(arr))

    # Bootstrap sampling
    boot_stats = []
    for _ in range(n_bootstraps):
        # Resample with replacement
        sample = np.random.choice(arr, size=n, replace=True)
        boot_stats.append(stat_func(sample))

    boot_stats = np.array(boot_stats)
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    ci_lower = float(np.percentile(boot_stats, lower_percentile))
    ci_upper = float(np.percentile(boot_stats, upper_percentile))

    result = {
        "statistic": original_stat,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "n_bootstraps": n_bootstraps,
        "confidence": confidence,
        "method": "bootstrap_percentile"
    }

    logger.info(
        f"Bootstrap CI ({confidence*100:.0f}%): stat={original_stat:.4f}, "
        f"CI [{ci_lower:.4f}, {ci_upper:.4f}], n={n_bootstraps}"
    )
    return result


def run_full_statistical_analysis(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = 0.05,
    n_bootstraps: int = 1000
) -> Dict[str, Any]:
    """
    Run the full suite of statistical tests required for the benchmark.

    This includes:
    1. Paired t-test
    2. Wilcoxon signed-rank test with effect size (PRIMARY)
    3. Bootstrap CI on the difference of means

    Args:
        condition_a: Measurements for condition A.
        condition_b: Measurements for condition B.
        alpha: Significance threshold.
        n_bootstraps: Number of bootstrap samples.

    Returns:
        Comprehensive dictionary with all test results.
    """
    logger.info("Starting full statistical analysis...")

    # Prepare data
    arr_a = np.array(condition_a)
    arr_b = np.array(condition_b)
    diff = arr_a - arr_b

    results = {
        "paired_ttest": paired_ttest(arr_a, arr_b, alpha),
        "wilcoxon": wilcoxon_effect_size(arr_a, arr_b, alpha),
        "bootstrap_diff_ci": bootstrap_ci(
            diff, 
            n_bootstraps=n_bootstraps, 
            confidence=0.95, 
            stat_func=np.mean
        ),
        "summary": {
            "n_pairs": len(arr_a),
            "mean_diff": float(np.mean(diff)),
            "std_diff": float(np.std(diff)),
            "alpha": alpha
        }
    }

    # Determine primary outcome based on Wilcoxon (non-parametric robustness)
    wilcoxon_significant = results["wilcoxon"]["significant"]
    ttest_significant = results["paired_ttest"]["significant"]

    results["summary"]["primary_outcome"] = "wilcoxon"
    results["summary"]["primary_significant"] = wilcoxon_significant
    
    logger.info(
        f"Analysis complete. Primary (Wilcoxon) significant: {wilcoxon_significant}, "
        f"T-test significant: {ttest_significant}"
    )

    return results