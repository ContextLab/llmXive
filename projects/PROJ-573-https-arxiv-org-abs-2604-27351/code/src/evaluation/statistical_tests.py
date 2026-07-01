"""
Statistical tests for benchmark evaluation.

Implements paired t-test, Wilcoxon signed-rank test with effect size,
and bootstrap confidence intervals as specified in FR-007, FR-014, FR-011.

Primary outcome: Wilcoxon effect size with 95% CI.
"""
import numpy as np
from scipy import stats
from typing import Tuple, List, Union, Optional, Dict, Any
import logging
import warnings
from src.utils.logging import get_logger

logger = get_logger(__name__)

def paired_ttest(
    condition_a: Union[np.ndarray, List[float]],
    condition_b: Union[np.ndarray, List[float]],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a paired t-test between two conditions.
    
    Args:
        condition_a: First condition measurements (paired).
        condition_b: Second condition measurements (paired).
        alpha: Significance threshold (default 0.05).
    
    Returns:
        Dictionary with t-statistic, p-value, and significance flag.
    """
    arr_a = np.array(condition_a)
    arr_b = np.array(condition_b)
    
    if arr_a.shape != arr_b.shape:
        raise ValueError("Condition arrays must have the same shape for paired test")
    
    if len(arr_a) < 2:
        raise ValueError("Paired t-test requires at least 2 samples per condition")
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        t_stat, p_val = stats.ttest_rel(arr_a, arr_b)
    
    result = {
        "test": "paired_ttest",
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "significant": bool(p_val < alpha),
        "alpha": alpha,
        "n_samples": len(arr_a)
    }
    
    logger.info(f"Paired t-test: t={t_stat:.4f}, p={p_val:.4f}, significant={p_val < alpha}")
    
    return result

def wilcoxon_effect_size(
    condition_a: Union[np.ndarray, List[float]],
    condition_b: Union[np.ndarray, List[float]]
) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test and compute effect size (r).
    
    Effect size r = Z / sqrt(N), where Z is the standardized test statistic
    and N is the number of non-zero differences.
    
    Args:
        condition_a: First condition measurements (paired).
        condition_b: Second condition measurements (paired).
    
    Returns:
        Dictionary with W-statistic, p-value, effect size r, and interpretation.
    """
    arr_a = np.array(condition_a)
    arr_b = np.array(condition_b)
    
    if arr_a.shape != arr_b.shape:
        raise ValueError("Condition arrays must have the same shape for paired test")
    
    if len(arr_a) < 2:
        raise ValueError("Wilcoxon test requires at least 2 samples per condition")
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stat, p_val = stats.wilcoxon(arr_a, arr_b)
    
    # Compute effect size r = Z / sqrt(N)
    # scipy.stats.wilcoxon returns the W statistic, but we need Z for effect size
    # We can approximate Z from the W statistic or use the normal approximation
    n = len(arr_a)
    differences = arr_a - arr_b
    non_zero_diff = differences[differences != 0]
    n_eff = len(non_zero_diff)
    
    if n_eff < 2:
        logger.warning("Insufficient non-zero differences for effect size calculation")
        return {
            "test": "wilcoxon",
            "w_statistic": float(stat),
            "p_value": float(p_val),
            "effect_size_r": None,
            "interpretation": "insufficient_data",
            "n_effective": n_eff
        }
    
    # Approximate Z using normal approximation for Wilcoxon
    # Mean and std of W under null hypothesis
    mean_w = n_eff * (n_eff + 1) / 4
    std_w = np.sqrt(n_eff * (n_eff + 1) * (2 * n_eff + 1) / 24)
    
    if std_w == 0:
        z_score = 0.0
    else:
        z_score = (stat - mean_w) / std_w
    
    effect_size_r = abs(z_score) / np.sqrt(n_eff)
    
    interpretation = get_effect_size_interpretation(effect_size_r)
    
    result = {
        "test": "wilcoxon",
        "w_statistic": float(stat),
        "p_value": float(p_val),
        "effect_size_r": float(effect_size_r),
        "interpretation": interpretation,
        "n_effective": n_eff,
        "z_score": float(z_score)
    }
    
    logger.info(f"Wilcoxon test: W={stat:.4f}, p={p_val:.4f}, r={effect_size_r:.4f} ({interpretation})")
    
    return result

def bootstrap_ci(
    values: Union[np.ndarray, List[float]],
    n_bootstrap: int = 10000,
    confidence_level: float = 0.95,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute bootstrap confidence interval for the mean.
    
    Uses the percentile method as described in Efron & Tibshirani (1993).
    
    Args:
        values: Array of values to compute CI for.
        n_bootstrap: Number of bootstrap resamples (default 10000).
        confidence_level: Confidence level (default 0.95 for 95% CI).
        seed: Random seed for reproducibility (optional).
    
    Returns:
        Dictionary with mean, ci_lower, ci_upper, and bootstrap statistics.
    """
    arr = np.array(values)
    
    if len(arr) < 2:
        raise ValueError("Bootstrap CI requires at least 2 samples")
    
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()
    
    n = len(arr)
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        resample = rng.choice(arr, size=n, replace=True)
        bootstrap_means.append(np.mean(resample))
    
    bootstrap_means = np.array(bootstrap_means)
    
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    
    mean_val = np.mean(arr)
    std_val = np.std(arr, ddof=1)
    
    result = {
        "mean": float(mean_val),
        "std": float(std_val),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "confidence_level": confidence_level,
        "n_bootstrap": n_bootstrap,
        "n_samples": n,
        "ci_width": float(ci_upper - ci_lower)
    }
    
    logger.info(f"Bootstrap CI (95%): mean={mean_val:.4f}, CI=[{ci_lower:.4f}, {ci_upper:.4f}]")
    
    return result

def get_effect_size_interpretation(r: float) -> str:
    """
    Interpret Cohen's r effect size.
    
    Thresholds (Cohen, 1988):
    - 0.1: small
    - 0.3: medium
    - 0.5: large
    
    Args:
        r: Effect size value.
    
    Returns:
        String interpretation of the effect size.
    """
    if r is None:
        return "undefined"
    
    r_abs = abs(r)
    
    if r_abs < 0.1:
        return "negligible"
    elif r_abs < 0.3:
        return "small"
    elif r_abs < 0.5:
        return "medium"
    else:
        return "large"

def run_full_statistical_analysis(
    condition_a: Union[np.ndarray, List[float]],
    condition_b: Union[np.ndarray, List[float]],
    alpha: float = 0.05,
    n_bootstrap: int = 10000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run complete statistical analysis comparing two conditions.
    
    Includes:
    1. Paired t-test
    2. Wilcoxon signed-rank test with effect size
    3. Bootstrap CI for the difference in means
    
    Primary outcome: Wilcoxon effect size with 95% CI.
    
    Args:
        condition_a: First condition measurements.
        condition_b: Second condition measurements.
        alpha: Significance threshold.
        n_bootstrap: Number of bootstrap resamples.
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary containing all statistical results.
    """
    arr_a = np.array(condition_a)
    arr_b = np.array(condition_b)
    
    # Compute differences for bootstrap
    differences = arr_a - arr_b
    
    result = {
        "paired_ttest": paired_ttest(condition_a, condition_b, alpha),
        "wilcoxon": wilcoxon_effect_size(condition_a, condition_b),
        "bootstrap_ci_difference": bootstrap_ci(
            differences, 
            n_bootstrap=n_bootstrap, 
            confidence_level=0.95,
            seed=seed
        ),
        "summary": {
            "n_samples": len(arr_a),
            "mean_a": float(np.mean(arr_a)),
            "mean_b": float(np.mean(arr_b)),
            "mean_difference": float(np.mean(differences)),
            "std_difference": float(np.std(differences, ddof=1))
        }
    }
    
    # Determine primary outcome (Wilcoxon effect size)
    wilcoxon_result = result["wilcoxon"]
    if wilcoxon_result.get("effect_size_r") is not None:
        result["primary_outcome"] = {
            "type": "wilcoxon_effect_size",
            "value": wilcoxon_result["effect_size_r"],
            "interpretation": wilcoxon_result["interpretation"],
            "ci": result["bootstrap_ci_difference"]
        }
    
    logger.info("Full statistical analysis complete")
    
    return result

def generate_analysis_summary(
    analysis_results: List[Dict[str, Any]],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Generate a summary of multiple statistical analyses.
    
    Args:
        analysis_results: List of analysis result dictionaries from run_full_statistical_analysis.
        alpha: Significance threshold.
    
    Returns:
        Dictionary with aggregate statistics and summary findings.
    """
    if not analysis_results:
        return {
            "n_analyses": 0,
            "message": "No analyses provided"
        }
    
    n_analyses = len(analysis_results)
    significant_count = 0
    effect_sizes = []
    
    for result in analysis_results:
        # Count significant results (using Wilcoxon p-value)
        wilcoxon = result.get("wilcoxon", {})
        if wilcoxon.get("p_value", 1.0) < alpha:
            significant_count += 1
        
        # Collect effect sizes
        effect_size = wilcoxon.get("effect_size_r")
        if effect_size is not None:
            effect_sizes.append(effect_size)
    
    # Aggregate statistics
    avg_effect_size = np.mean(effect_sizes) if effect_sizes else None
    std_effect_size = np.std(effect_sizes, ddof=1) if len(effect_sizes) > 1 else None
    
    summary = {
        "n_analyses": n_analyses,
        "significant_count": significant_count,
        "significance_rate": significant_count / n_analyses if n_analyses > 0 else 0,
        "avg_effect_size": float(avg_effect_size) if avg_effect_size is not None else None,
        "std_effect_size": float(std_effect_size) if std_effect_size is not None else None,
        "alpha": alpha,
        "interpretation": get_effect_size_interpretation(avg_effect_size) if avg_effect_size is not None else None
    }
    
    logger.info(f"Analysis summary: {significant_count}/{n_analyses} significant, avg r={avg_effect_size:.4f}")
    
    return summary

def main():
    """
    Example usage of statistical tests module.
    
    Runs a demonstration with sample data to verify functionality.
    """
    logger.info("Running statistical tests demonstration")
    
    # Generate sample data (for demonstration only - real data should come from experiments)
    np.random.seed(42)
    n_samples = 50
    
    # Simulate paired measurements (e.g., heterogeneous vs unified mode)
    condition_a = np.random.normal(loc=0.75, scale=0.1, size=n_samples)
    condition_b = np.random.normal(loc=0.78, scale=0.1, size=n_samples)
    
    # Run full analysis
    results = run_full_statistical_analysis(
        condition_a, 
        condition_b, 
        alpha=0.05,
        n_bootstrap=1000,
        seed=42
    )
    
    print("\n" + "="*60)
    print("STATISTICAL ANALYSIS RESULTS")
    print("="*60)
    
    print(f"\nSample size: {results['summary']['n_samples']}")
    print(f"Mean A: {results['summary']['mean_a']:.4f}")
    print(f"Mean B: {results['summary']['mean_b']:.4f}")
    print(f"Mean difference: {results['summary']['mean_difference']:.4f}")
    
    print("\n--- Paired T-Test ---")
    print(f"t-statistic: {results['paired_ttest']['t_statistic']:.4f}")
    print(f"p-value: {results['paired_ttest']['p_value']:.4f}")
    print(f"Significant (α=0.05): {results['paired_ttest']['significant']}")
    
    print("\n--- Wilcoxon Signed-Rank Test ---")
    print(f"W-statistic: {results['wilcoxon']['w_statistic']:.4f}")
    print(f"p-value: {results['wilcoxon']['p_value']:.4f}")
    print(f"Effect size (r): {results['wilcoxon']['effect_size_r']:.4f}")
    print(f"Interpretation: {results['wilcoxon']['interpretation']}")
    
    print("\n--- Bootstrap 95% CI (Difference) ---")
    print(f"CI Lower: {results['bootstrap_ci_difference']['ci_lower']:.4f}")
    print(f"CI Upper: {results['bootstrap_ci_difference']['ci_upper']:.4f}")
    print(f"CI Width: {results['bootstrap_ci_difference']['ci_width']:.4f}")
    
    print("\n--- PRIMARY OUTCOME ---")
    if "primary_outcome" in results:
        po = results["primary_outcome"]
        print(f"Type: {po['type']}")
        print(f"Value: {po['value']:.4f}")
        print(f"Interpretation: {po['interpretation']}")
        print(f"95% CI: [{po['ci']['ci_lower']:.4f}, {po['ci']['ci_upper']:.4f}]")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()