"""
Statistical Tests Module for Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements:
- Paired t-test with logging
- Wilcoxon signed-rank test with effect size (r) calculation
- Bootstrap confidence intervals (95% CI) using Efron's method
- Full statistical analysis pipeline
"""

import numpy as np
from scipy import stats
from typing import Tuple, List, Union, Optional, Dict, Any
import logging
import warnings

from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Default significance threshold (alpha)
DEFAULT_ALPHA = 0.05

def paired_ttest(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Perform a paired t-test between two conditions.

    Args:
        condition_a: First condition measurements (e.g., accuracies from seed 1).
        condition_b: Second condition measurements (paired with condition_a).
        alpha: Significance threshold (default 0.05).

    Returns:
        Dictionary containing:
            - statistic: t-statistic
            - pvalue: p-value
            - significant: boolean indicating if p < alpha
            - mean_diff: mean of differences
            - std_diff: std of differences
            - n: number of pairs
    """
    logger.info(f"Running paired t-test (alpha={alpha})")

    a = np.array(condition_a)
    b = np.array(condition_b)

    if a.shape != b.shape:
        raise ValueError(f"Input arrays must have same shape. Got {a.shape} and {b.shape}")

    if len(a) < 2:
        raise ValueError("Paired t-test requires at least 2 pairs of observations.")

    # Compute differences
    diffs = a - b
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)  # Sample std

    # Perform t-test
    t_stat, p_val = stats.ttest_rel(a, b)

    result = {
        "statistic": float(t_stat),
        "pvalue": float(p_val),
        "significant": bool(p_val < alpha),
        "mean_diff": float(mean_diff),
        "std_diff": float(std_diff),
        "n": int(len(a)),
        "method": "paired_ttest",
        "alpha": alpha
    }

    logger.info(f"T-statistic: {t_stat:.4f}, p-value: {p_val:.4f}, Significant: {result['significant']}")

    return result

def wilcoxon_effect_size(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test and calculate effect size (r).

    Formula for effect size r:
        r = Z / sqrt(N)
    where Z is the standardized test statistic and N is the number of observations.

    Args:
        condition_a: First condition measurements.
        condition_b: Second condition measurements.
        alpha: Significance threshold.

    Returns:
        Dictionary containing:
            - statistic: W statistic (or Z if approximation used)
            - pvalue: p-value
            - effect_size_r: calculated r value
            - significant: boolean
            - interpretation: qualitative interpretation of effect size
    """
    logger.info(f"Running Wilcoxon signed-rank test with effect size (alpha={alpha})")

    a = np.array(condition_a)
    b = np.array(condition_b)

    if a.shape != b.shape:
        raise ValueError(f"Input arrays must have same shape. Got {a.shape} and {b.shape}")

    if len(a) < 2:
        raise ValueError("Wilcoxon test requires at least 2 pairs.")

    # Suppress convergence warnings from scipy if any
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            stat, p_val = stats.wilcoxon(a, b)
        except Exception as e:
            logger.error(f"Wilcoxon test failed: {e}")
            raise

    # Calculate effect size r
    # scipy.stats.wilcoxon returns W statistic. For effect size, we need Z.
    # We can approximate Z or use the exact distribution if N is small.
    # Standard approach: r = Z / sqrt(N)
    # scipy does not directly return Z in the basic call, but we can compute it
    # or use the normal approximation if N is large enough (>10 is standard rule of thumb).
    # However, to be robust, we compute Z from the statistic if possible or use normal approx.
    # A robust way: use the 'correction' and 'zero_method' defaults from scipy.
    # If N is large, scipy uses normal approximation and returns Z in some versions,
    # but in standard stats.wilcoxon, it returns W.
    # Let's compute Z manually using the mean and std of W under null.
    # Mean of W = n(n+1)/4
    # Std of W = sqrt(n(n+1)(2n+1)/24)
    # Z = (W - Mean) / Std

    n = len(a)
    if n > 10:
        # Normal approximation
        mean_w = n * (n + 1) / 4.0
        std_w = np.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
        z_score = (stat - mean_w) / std_w
    else:
        # For small N, scipy's exact test is used, but we still need Z for r.
        # We approximate Z using the exact p-value inversion if possible,
        # or just use the normal approximation as a proxy (common in literature).
        # For consistency, we use normal approximation for r calculation even for small N
        # as r = Z/sqrt(N) is the standard definition.
        mean_w = n * (n + 1) / 4.0
        std_w = np.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
        z_score = (stat - mean_w) / std_w

    effect_size_r = z_score / np.sqrt(n)

    interpretation = get_effect_size_interpretation(abs(effect_size_r))

    result = {
        "statistic": float(stat),
        "pvalue": float(p_val),
        "effect_size_r": float(effect_size_r),
        "significant": bool(p_val < alpha),
        "interpretation": interpretation,
        "method": "wilcoxon_signed_rank",
        "alpha": alpha,
        "n": int(n)
    }

    logger.info(f"W-statistic: {stat:.4f}, p-value: {p_val:.4f}, Effect Size (r): {effect_size_r:.4f} ({interpretation})")

    return result

def bootstrap_ci(
    values: Union[List[float], np.ndarray],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate Bootstrap Confidence Interval for the mean.

    Uses Efron's bootstrap method.
    Reference: Efron, B. (1979). Bootstrap methods: another look at the jackknife.

    Args:
        values: Array of observed values.
        n_bootstrap: Number of bootstrap samples (default 1000).
        confidence_level: Confidence level (default 0.95 for 95% CI).
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing:
            - mean: sample mean
            - ci_lower: lower bound of CI
            - ci_upper: upper bound of CI
            - ci_width: width of CI
            - percentile_method: 'percentile' (standard)
    """
    logger.info(f"Running Bootstrap CI (n={n_bootstrap}, level={confidence_level})")

    arr = np.array(values)
    if len(arr) == 0:
        raise ValueError("Values array cannot be empty.")

    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    bootstrap_means = []

    # Perform bootstrap resampling
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample = rng.choice(arr, size=len(arr), replace=True)
        bootstrap_means.append(np.mean(sample))

    bootstrap_means = np.array(bootstrap_means)

    # Calculate percentiles
    alpha = 1.0 - confidence_level
    lower_percentile = (alpha / 2.0) * 100
    upper_percentile = (1.0 - alpha / 2.0) * 100

    ci_lower = float(np.percentile(bootstrap_means, lower_percentile))
    ci_upper = float(np.percentile(bootstrap_means, upper_percentile))
    sample_mean = float(np.mean(arr))

    result = {
        "mean": sample_mean,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ci_width": float(ci_upper - ci_lower),
        "confidence_level": confidence_level,
        "n_bootstrap": n_bootstrap,
        "method": "bootstrap_percentile",
        "reference": "Efron (1979)"
    }

    logger.info(f"Mean: {sample_mean:.4f}, 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

    return result

def get_effect_size_interpretation(r: float) -> str:
    """
    Interpret effect size r based on Cohen's guidelines.
    |r| < 0.1: Negligible
    0.1 <= |r| < 0.3: Small
    0.3 <= |r| < 0.5: Medium
    |r| >= 0.5: Large

    Args:
        r: Absolute effect size value.

    Returns:
        String interpretation.
    """
    r_abs = abs(r)
    if r_abs < 0.1:
        return "Negligible"
    elif r_abs < 0.3:
        return "Small"
    elif r_abs < 0.5:
        return "Medium"
    else:
        return "Large"

def run_full_statistical_analysis(
    condition_a: Union[List[float], np.ndarray],
    condition_b: Union[List[float], np.ndarray],
    alpha: float = DEFAULT_ALPHA,
    n_bootstrap: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a comprehensive statistical analysis comparing two conditions.

    Includes:
    1. Paired t-test
    2. Wilcoxon signed-rank test with effect size
    3. Bootstrap CI for the mean difference

    Args:
        condition_a: First condition data.
        condition_b: Second condition data.
        alpha: Significance threshold.
        n_bootstrap: Number of bootstrap iterations.
        seed: Random seed.

    Returns:
        Dictionary with all results.
    """
    logger.info("Starting full statistical analysis pipeline")

    # 1. Paired T-Test
    ttest_result = paired_ttest(condition_a, condition_b, alpha)

    # 2. Wilcoxon Test
    wilcoxon_result = wilcoxon_effect_size(condition_a, condition_b, alpha)

    # 3. Bootstrap CI for mean difference
    diffs = np.array(condition_a) - np.array(condition_b)
    bootstrap_result = bootstrap_ci(diffs, n_bootstrap, 0.95, seed)

    analysis = {
        "ttest": ttest_result,
        "wilcoxon": wilcoxon_result,
        "bootstrap_ci": bootstrap_result,
        "n_samples": len(condition_a),
        "alpha": alpha
    }

    logger.info("Statistical analysis complete")

    return analysis

def generate_analysis_summary(results: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the statistical analysis.

    Args:
        results: Output from run_full_statistical_analysis.

    Returns:
        Formatted string summary.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("STATISTICAL ANALYSIS SUMMARY")
    lines.append("=" * 60)

    # T-Test
    t = results["ttest"]
    lines.append(f"\n1. Paired T-Test:")
    lines.append(f"   Statistic: {t['statistic']:.4f}")
    lines.append(f"   P-Value: {t['pvalue']:.4f}")
    lines.append(f"   Significant (α={t['alpha']}): {t['significant']}")
    lines.append(f"   Mean Difference: {t['mean_diff']:.4f}")

    # Wilcoxon
    w = results["wilcoxon"]
    lines.append(f"\n2. Wilcoxon Signed-Rank Test:")
    lines.append(f"   Statistic: {w['statistic']:.4f}")
    lines.append(f"   P-Value: {w['pvalue']:.4f}")
    lines.append(f"   Significant (α={w['alpha']}): {w['significant']}")
    lines.append(f"   Effect Size (r): {w['effect_size_r']:.4f} ({w['interpretation']})")

    # Bootstrap
    b = results["bootstrap_ci"]
    lines.append(f"\n3. Bootstrap 95% CI (Mean Difference):")
    lines.append(f"   Mean Difference: {b['mean']:.4f}")
    lines.append(f"   CI: [{b['ci_lower']:.4f}, {b['ci_upper']:.4f}]")
    lines.append(f"   Width: {b['ci_width']:.4f}")

    lines.append("=" * 60)

    return "\n".join(lines)

def main():
    """
    Main entry point for standalone testing of statistical functions.
    Runs a dummy analysis on simulated data to verify functionality.
    """
    logger.info("Running standalone test for statistical_tests module")

    # Generate dummy data for verification (REAL computation on small sample)
    np.random.seed(42)
    data_a = np.random.normal(loc=0.5, scale=0.1, size=20)
    data_b = np.random.normal(loc=0.55, scale=0.1, size=20)

    logger.info(f"Test data: A (mean={np.mean(data_a):.3f}), B (mean={np.mean(data_b):.3f})")

    # Run analysis
    results = run_full_statistical_analysis(data_a, data_b, alpha=0.05, n_bootstrap=500, seed=42)

    # Print summary
    summary = generate_analysis_summary(results)
    print(summary)

    logger.info("Standalone test completed successfully")

if __name__ == "__main__":
    main()