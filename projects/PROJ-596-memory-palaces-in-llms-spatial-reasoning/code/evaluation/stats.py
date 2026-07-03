import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy import stats

# Ensure the logger is configured
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_normality(data: List[float], alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Performs Shapiro-Wilk test for normality.
    
    Args:
        data: List of sample values.
        alpha: Significance level.
        
    Returns:
        Tuple of (is_normal, p_value)
    """
    if len(data) < 3:
        logger.warning("Sample size too small for Shapiro-Wilk test. Assuming normality.")
        return True, 1.0
    
    try:
        stat, p_value = stats.shapiro(data)
        is_normal = p_value > alpha
        logger.info(f"Shapiro-Wilk: W={stat:.4f}, p={p_value:.4f}, Normal={is_normal}")
        return is_normal, p_value
    except Exception as e:
        logger.error(f"Normality check failed: {e}")
        return False, 0.0

def paired_t_test(sample1: List[float], sample2: List[float]) -> Tuple[float, float]:
    """
    Performs a paired two-tailed t-test.
    
    Args:
        sample1: First sample values.
        sample2: Second sample values.
        
    Returns:
        Tuple of (t_statistic, p_value)
    """
    if len(sample1) != len(sample2):
        raise ValueError("Sample sizes must match for paired t-test")
    
    stat, p_value = stats.ttest_rel(sample1, sample2)
    logger.info(f"Paired T-Test: t={stat:.4f}, p={p_value:.4f}")
    return float(stat), float(p_value)

def wilcoxon_signed_rank(sample1: List[float], sample2: List[float]) -> Tuple[float, float]:
    """
    Performs Wilcoxon signed-rank test (non-parametric alternative to paired t-test).
    
    Args:
        sample1: First sample values.
        sample2: Second sample values.
        
    Returns:
        Tuple of (statistic, p_value)
    """
    if len(sample1) != len(sample2):
        raise ValueError("Sample sizes must match for Wilcoxon test")
    
    stat, p_value = stats.wilcoxon(sample1, sample2)
    logger.info(f"Wilcoxon: W={stat:.4f}, p={p_value:.4f}")
    return float(stat), float(p_value)

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Applies Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level.
        
    Returns:
        List of corrected p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    corrected = [min(p * n, 1.0) for p in p_values]
    logger.info(f"Bonferroni corrected p-values: {corrected}")
    return corrected

def holm_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Applies Holm-Bonferroni correction (step-down method).
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level.
        
    Returns:
        List of corrected p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = [p_values[i] for i in sorted_indices]
    
    corrected = []
    for i, p in enumerate(sorted_p):
        # Adjusted p-value
        adj_p = p * (n - i)
        # Ensure monotonicity (step-down)
        if corrected:
            adj_p = max(adj_p, corrected[-1])
        corrected.append(min(adj_p, 1.0))
    
    # Reorder to original indices
    final_corrected = [0.0] * n
    for i, idx in enumerate(sorted_indices):
        final_corrected[idx] = corrected[i]
        
    logger.info(f"Holm-Bonferroni corrected p-values: {final_corrected}")
    return final_corrected

def calculate_cohens_d(sample1: List[float], sample2: List[float]) -> float:
    """
    Calculates Cohen's d effect size for paired samples.
    
    Cohen's d = mean(diff) / std(diff)
    
    Args:
        sample1: First sample values.
        sample2: Second sample values.
        
    Returns:
        Cohen's d value.
    """
    if len(sample1) != len(sample2):
        raise ValueError("Sample sizes must match")
    
    diffs = np.array(sample1) - np.array(sample2)
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)  # Sample standard deviation
    
    if std_diff == 0:
        logger.warning("Standard deviation of differences is zero. Cohen's d is undefined.")
        return 0.0
        
    cohens_d = mean_diff / std_diff
    logger.info(f"Cohen's d: {cohens_d:.4f}")
    return float(cohens_d)

def calculate_cohens_d_ci(sample1: List[float], sample2: List[float], confidence: float = 0.95) -> Tuple[float, Tuple[float, float]]:
    """
    Calculates Cohen's d with 95% confidence interval.
    
    Uses the non-central t-distribution approximation for CI.
    Formula approximates CI based on the standard error of d.
    
    Args:
        sample1: First sample values.
        sample2: Second sample values.
        confidence: Confidence level (e.g., 0.95).
        
    Returns:
        Tuple of (cohens_d, (lower_ci, upper_ci))
    """
    if len(sample1) != len(sample2):
        raise ValueError("Sample sizes must match")
    
    n = len(sample1)
    diffs = np.array(sample1) - np.array(sample2)
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    
    if std_diff == 0:
        logger.warning("Standard deviation of differences is zero. CI cannot be calculated.")
        return 0.0, (0.0, 0.0)
    
    d = mean_diff / std_diff
    
    # Standard error of Cohen's d
    # Approximation: SE_d = sqrt((n / (n-1)) + (d^2 / (2*n)))
    # More precise approximation for paired designs:
    se_d = np.sqrt((n / (n - 1)) + (d**2 / (2 * n)))
    
    # Critical t-value for the confidence interval
    alpha = 1 - confidence
    df = n - 1
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    lower_ci = d - (t_crit * se_d)
    upper_ci = d + (t_crit * se_d)
    
    logger.info(f"Cohen's d: {d:.4f}, 95% CI: [{lower_ci:.4f}, {upper_ci:.4f}]")
    return float(d), (float(lower_ci), float(upper_ci))

def run_statistical_comparison(
    baseline_scores: List[float], 
    spatial_scores: List[float],
    dataset_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Runs a full statistical comparison between baseline and spatial model scores.
    Includes normality check, t-test/Wilcoxon, and effect size calculation.
    
    Args:
        baseline_scores: List of recall scores for the baseline model.
        spatial_scores: List of recall scores for the spatial model.
        dataset_name: Name of the dataset for logging.
        
    Returns:
        Dictionary containing test results.
    """
    result = {
        "dataset": dataset_name,
        "n_samples": len(baseline_scores),
        "baseline_mean": float(np.mean(baseline_scores)),
        "spatial_mean": float(np.mean(spatial_scores)),
        "baseline_std": float(np.std(baseline_scores, ddof=1)) if len(baseline_scores) > 1 else 0.0,
        "spatial_std": float(np.std(spatial_scores, ddof=1)) if len(spatial_scores) > 1 else 0.0,
        "normality_check": {},
        "test_result": {},
        "effect_size": {}
    }
    
    # Check normality of differences
    diffs = np.array(spatial_scores) - np.array(baseline_scores)
    is_normal, p_normality = check_normality(diffs.tolist())
    result["normality_check"] = {
        "is_normal": is_normal,
        "p_value": p_normality
    }
    
    # Select test based on normality
    if is_normal:
        t_stat, p_val = paired_t_test(baseline_scores, spatial_scores)
        test_type = "paired_t_test"
    else:
        w_stat, p_val = wilcoxon_signed_rank(baseline_scores, spatial_scores)
        test_type = "wilcoxon_signed_rank"
        t_stat = w_stat # Store stat in same field for consistency
        
    result["test_result"] = {
        "test_type": test_type,
        "statistic": t_stat,
        "p_value": p_val,
        "significant": p_val < 0.05
    }
    
    # Calculate Effect Size (Cohen's d) with CI
    d, (ci_low, ci_high) = calculate_cohens_d_ci(baseline_scores, spatial_scores)
    result["effect_size"] = {
        "cohens_d": d,
        "confidence_level": 0.95,
        "ci_lower": ci_low,
        "ci_upper": ci_high
    }
    
    logger.info(f"Statistical comparison for {dataset_name} complete.")
    return result

def main():
    """
    Main entry point for standalone execution.
    Demonstrates usage with dummy data if no args provided, 
    or loads data from artifacts if specified.
    """
    # Example usage with dummy data (in real pipeline, this loads from run_summary)
    # This function is primarily for CLI testing or integration into main.py
    print("Statistical Analysis Module Ready.")
    print("Use run_statistical_comparison(baseline_scores, spatial_scores, dataset_name) to run tests.")

if __name__ == "__main__":
    main()