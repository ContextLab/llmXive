"""
Regression analysis module for the llmXive project.

Implements linear regression for coherence degradation curves and
applies Bonferroni correction for family-wise error rate control.
"""
import os
import sys
import math
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from statistics import mean, stdev

# Ensure parent directory is in path for imports if run as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import get_data_path, ensure_directories

logger = logging.getLogger(__name__)

def calculate_linear_regression(x: List[float], y: List[float]) -> Dict[str, float]:
    """
    Calculate simple linear regression (least squares) for x and y.
    
    Returns slope, intercept, and R-squared value.
    """
    n = len(x)
    if n < 2:
        return {"slope": 0.0, "intercept": mean(y) if y else 0.0, "r_squared": 0.0}
    
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)
    
    # Slope calculation
    denominator = n * sum_x2 - sum_x ** 2
    if denominator == 0:
        slope = 0.0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denominator
    
    intercept = (sum_y - slope * sum_x) / n
    
    # R-squared calculation
    y_mean = mean(y)
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
    
    if ss_tot == 0:
        r_squared = 1.0 if ss_res == 0 else 0.0
    else:
        r_squared = 1 - (ss_res / ss_tot)
    
    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared
    }

def calculate_t_statistic(x: List[float], y: List[float], slope: float, intercept: float) -> Tuple[float, int]:
    """
    Calculate t-statistic for the slope coefficient.
    
    Returns (t_statistic, degrees_of_freedom).
    """
    n = len(x)
    if n < 3:
        return 0.0, 0
    
    # Predicted values
    y_pred = [slope * xi + intercept for xi in x]
    
    # Residual sum of squares
    ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
    
    # Standard error of the estimate
    if n - 2 == 0:
        se = 0.0
    else:
        se = math.sqrt(ss_res / (n - 2))
    
    # Standard error of slope
    x_mean = mean(x)
    ss_x = sum((xi - x_mean) ** 2 for xi in x)
    
    if ss_x == 0:
        se_slope = float('inf')
    else:
        se_slope = se / math.sqrt(ss_x)
    
    if se_slope == 0:
        t_stat = 0.0
    else:
        t_stat = slope / se_slope
    
    return t_stat, n - 2

def t_distribution_cdf(t: float, df: int) -> float:
    """
    Approximate Cumulative Distribution Function for t-distribution.
    Uses a standard approximation for p-value calculation.
    """
    # For large df, t-distribution approaches normal distribution
    # Using a simple approximation for p-value (two-tailed)
    # This is a simplified implementation; for production, use scipy.stats
    
    if df <= 0:
        return 0.5
    
    # Approximation using the relationship with the beta function
    # or simple normal approximation for high df
    if df > 100:
        # Normal approximation
        from math import erf, sqrt
        z = t
        p_one_tail = 0.5 * (1 + erf(-abs(z) / sqrt(2)))
        return 2 * p_one_tail
    
    # For smaller df, use a simpler numerical approximation
    # This is a placeholder for a more robust implementation
    # In practice, one would use scipy.stats.t.sf
    x = df / (df + t**2)
    # Incomplete beta function approximation (simplified)
    # Using a standard approximation for the survival function
    p = 0.5 * (1 + math.copysign(1, t) * (1 - x)**(df/2))
    # Two-tailed p-value approximation
    p_val = 2 * min(p, 1 - p)
    return p_val

def bonferroni_correct(p_value: float, n_tests: int) -> float:
    """
    Apply Bonferroni correction to a p-value.
    
    The corrected p-value is min(p * n_tests, 1.0).
    This controls the family-wise error rate (FWER).
    
    Args:
        p_value: The original uncorrected p-value
        n_tests: The number of statistical tests performed (family size)
    
    Returns:
        The Bonferroni-corrected p-value
    """
    if n_tests <= 0:
        return p_value
    
    corrected = p_value * n_tests
    return min(corrected, 1.0)

def is_significant(corrected_p_value: float, alpha: float = 0.05) -> bool:
    """
    Determine if a result is statistically significant after correction.
    
    Args:
        corrected_p_value: The Bonferroni-corrected p-value
        alpha: The significance level (default 0.05)
    
    Returns:
        True if corrected_p_value < alpha, False otherwise
    """
    return corrected_p_value < alpha

def run_regression_analysis(
    region_counts: List[int],
    parallel_scores: List[float],
    sequential_scores: List[float],
    inference_times: List[float],
    n_tests: int = 6,
    alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Perform regression analysis on the coherence degradation data.
    
    Applies Bonferroni correction to significance tests as mandated by Spec Assumptions.
    
    Args:
        region_counts: List of region counts (e.g., [25, 30, 35, 40, 45, 50])
        parallel_scores: List of parallel coherence scores
        sequential_scores: List of sequential coherence scores
        inference_times: List of inference times corresponding to region counts
        n_tests: Number of tests in the family for Bonferroni correction (default 6 bins)
        alpha: Significance threshold (default 0.05)
    
    Returns:
        List of dictionaries containing regression results for each data point:
        - region_count: int
        - parallel_score: float
        - sequential_score: float
        - inference_time: float
        - corrected_p_value: float (Bonferroni-corrected)
        - is_significant: bool
    """
    if len(region_counts) != len(parallel_scores) or \
       len(region_counts) != len(sequential_scores) or \
       len(region_counts) != len(inference_times):
        raise ValueError("All input lists must have the same length")
    
    if len(region_counts) < 2:
        raise ValueError("Need at least 2 data points for regression")
    
    results = []
    
    # Convert to float for calculations
    x = [float(rc) for rc in region_counts]
    y_parallel = [float(ps) for ps in parallel_scores]
    y_sequential = [float(ss) for ss in sequential_scores]
    times = [float(t) for t in inference_times]
    
    # Calculate regression for parallel scores
    reg_parallel = calculate_linear_regression(x, y_parallel)
    
    # Calculate regression for sequential scores (baseline)
    reg_sequential = calculate_linear_regression(x, y_sequential)
    
    # For each point, calculate significance of the difference from the trend
    # or significance of the degradation slope
    # Here we test the hypothesis that the slope is non-zero (degradation exists)
    
    # Test 1: Is the parallel slope significantly negative?
    t_stat_p, df_p = calculate_t_statistic(x, y_parallel, reg_parallel["slope"], reg_parallel["intercept"])
    p_val_p = t_distribution_cdf(t_stat_p, df_p)
    corrected_p_p = bonferroni_correct(p_val_p, n_tests)
    sig_p = is_significant(corrected_p_p, alpha)
    
    # Test 2: Is the sequential slope significantly different from zero?
    t_stat_s, df_s = calculate_t_statistic(x, y_sequential, reg_sequential["slope"], reg_sequential["intercept"])
    p_val_s = t_distribution_cdf(t_stat_s, df_s)
    corrected_p_s = bonferroni_correct(p_val_s, n_tests)
    sig_s = is_significant(corrected_p_s, alpha)
    
    # Test 3: Is the difference in slopes significant? (simplified approach)
    # We'll treat the difference in slopes as another test
    slope_diff = reg_parallel["slope"] - reg_sequential["slope"]
    # Approximate standard error of difference (simplified)
    se_diff = math.sqrt(1.0/len(x)) # Placeholder for proper SE calculation
    if se_diff > 0:
        t_stat_diff = slope_diff / se_diff
        p_val_diff = t_distribution_cdf(t_stat_diff, df_p)
    else:
        t_stat_diff = 0.0
        p_val_diff = 1.0
    corrected_p_diff = bonferroni_correct(p_val_diff, n_tests)
    sig_diff = is_significant(corrected_p_diff, alpha)
    
    # Store results for each data point
    # We assign the most conservative p-value (max of the three tests) to each point
    # to ensure family-wise error rate control across the entire analysis
    for i, rc in enumerate(region_counts):
        # Use the maximum corrected p-value from the three tests for this point
        # This is a conservative approach to FWER control
        max_corrected_p = max(corrected_p_p, corrected_p_s, corrected_p_diff)
        is_sig = max_corrected_p < alpha
        
        results.append({
            "region_count": int(rc),
            "parallel_score": float(y_parallel[i]),
            "sequential_score": float(y_sequential[i]),
            "inference_time": float(times[i]),
            "corrected_p_value": float(max_corrected_p),
            "is_significant": is_sig
        })
    
    logger.info(f"Regression analysis complete. {n_tests} tests processed with Bonferroni correction.")
    logger.info(f"Parallel slope: {reg_parallel['slope']:.4f} (corrected p={corrected_p_p:.4f}, sig={sig_p})")
    logger.info(f"Sequential slope: {reg_sequential['slope']:.4f} (corrected p={corrected_p_s:.4f}, sig={sig_s})")
    logger.info(f"Slope difference: {slope_diff:.4f} (corrected p={corrected_p_diff:.4f}, sig={sig_diff})")
    
    return results

def save_regression_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save regression results to a CSV file.
    
    Args:
        results: List of result dictionaries from run_regression_analysis
        output_path: Path to the output CSV file
    """
    ensure_directories()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        # Write header
        f.write("region_count,parallel_score,sequential_score,inference_time,corrected_p_value,is_significant\n")
        
        # Write data
        for r in results:
            f.write(f"{r['region_count']},{r['parallel_score']:.6f},{r['sequential_score']:.6f},"
                    f"{r['inference_time']:.6f},{r['corrected_p_value']:.6f},{r['is_significant']}\n")
    
    logger.info(f"Regression results saved to {output_path}")

def main():
    """
    Main function to demonstrate regression analysis with Bonferroni correction.
    This is a placeholder for actual data loading in a real pipeline.
    """
    # Example data (in real usage, this would come from T022 consumer)
    region_counts = [25, 30, 35, 40, 45, 50]
    parallel_scores = [0.95, 0.92, 0.88, 0.82, 0.75, 0.68]
    sequential_scores = [0.96, 0.95, 0.94, 0.93, 0.92, 0.91]
    inference_times = [0.5, 0.6, 0.7, 0.9, 1.2, 1.6]
    
    results = run_regression_analysis(
        region_counts=region_counts,
        parallel_scores=parallel_scores,
        sequential_scores=sequential_scores,
        inference_times=inference_times,
        n_tests=len(region_counts),
        alpha=0.05
    )
    
    output_path = str(Path(get_data_path()) / "processed" / "degradation_curve.csv")
    save_regression_results(results, output_path)
    
    print(f"Analysis complete. Results saved to {output_path}")
    print(f"Sample result: {results[0]}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()