import json
import os
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats as scipy_stats
import logging

from src.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def perform_significance_test(
    metric_a: List[float],
    metric_b: List[float],
    test_name: str = "metric_comparison"
) -> Dict[str, Any]:
    """
    Perform statistical significance testing on paired metric differences.
    
    1. Run Shapiro-Wilk test for normality on the differences.
    2. If p > 0.05 (normal), run Paired T-test.
    3. If p <= 0.05 (non-normal), run Wilcoxon signed-rank test.
    
    Returns a dictionary with test results.
    """
    if len(metric_a) != len(metric_b):
        raise ValueError("Input lists must be of equal length for paired tests.")
    
    if len(metric_a) < 2:
        raise ValueError("At least 2 samples are required for significance testing.")

    differences = np.array(metric_a) - np.array(metric_b)
    
    # 1. Normality Test (Shapiro-Wilk)
    try:
        shapiro_stat, shapiro_p = scipy_stats.shapiro(differences)
    except ValueError as e:
        # Happens if sample size is too large for Shapiro-Wilk in some scipy versions
        # Fallback to treating as non-normal if we can't check, or assume normal if small
        logger.warning(f"Shapiro-Wilk test failed: {e}. Assuming non-normal distribution.")
        shapiro_p = 0.0 
    
    is_normal = shapiro_p > 0.05
    
    result = {
        "test_name": test_name,
        "sample_size": len(metric_a),
        "mean_difference": float(np.mean(differences)),
        "std_difference": float(np.std(differences)),
        "normality_test": {
            "test": "Shapiro-Wilk",
            "statistic": float(shapiro_stat),
            "p_value": float(shapiro_p),
            "is_normal": is_normal
        }
    }
    
    # 2. Significance Test based on Normality
    if is_normal:
        test_name_used = "Paired T-test"
        t_stat, p_value = scipy_stats.ttest_rel(metric_a, metric_b)
    else:
        test_name_used = "Wilcoxon Signed-Rank Test"
        try:
            w_stat, p_value = scipy_stats.wilcoxon(differences)
        except ValueError:
            # Handle cases where differences are all zero or similar
            p_value = 1.0
            w_stat = 0.0
    
    result["significance_test"] = {
        "test": test_name_used,
        "statistic": float(t_stat if is_normal else w_stat),
        "p_value": float(p_value)
    }
    
    # Determine conclusion
    alpha = 0.05
    is_significant = p_value < alpha
    result["conclusion"] = "significant" if is_significant else "not_significant"
    result["alpha"] = alpha
    
    return result

def execute_significance_test(
    results_dir: str = "results",
    comparison_file: str = "metrics_comparison.json"
) -> str:
    """
    Execute the significance test on the metric differences provided by T025b.
    Reads from results/metrics_comparison.json and writes to results/statistical_significance.json.
    
    SC-001 Requirement: Record p-values, confidence intervals, and conclusion.
    """
    input_path = os.path.join(results_dir, comparison_file)
    output_path = os.path.join(results_dir, "statistical_significance.json")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Comparison file not found: {input_path}. "
                                "Run T025b first to generate metrics_comparison.json.")
    
    with open(input_path, 'r') as f:
        comparison_data = json.load(f)
    
    # Expect structure: { "metrics": { "precision": { "greedy": [...], "prorl": [...] }, ... } }
    # Or a flattened list of differences if T025b aggregated differently.
    # We assume T025b produced a structure where we can extract paired lists.
    
    results_summary = {
        "timestamp": str(np.datetime64('now')),
        "tests_performed": []
    }
    
    metrics_to_test = ["precision", "recall", "diversity", "coverage"]
    
    for metric_name in metrics_to_test:
        if metric_name not in comparison_data.get("metrics", {}):
            logger.warning(f"Metric {metric_name} not found in comparison data, skipping.")
            continue
        
        metric_data = comparison_data["metrics"][metric_name]
        greedy_vals = metric_data.get("greedy", [])
        prorl_vals = metric_data.get("prorl", [])
        
        if not greedy_vals or not prorl_vals:
            logger.warning(f"No data for {metric_name}, skipping test.")
            continue
        
        try:
            test_result = perform_significance_test(
                metric_a=greedy_vals,
                metric_b=prorl_vals,
                test_name=f"{metric_name}_comparison"
            )
            
            # Add confidence interval (95%) for the mean difference if T-test
            if test_result["significance_test"]["test"] == "Paired T-test":
                diffs = np.array(greedy_vals) - np.array(prorl_vals)
                mean_diff = np.mean(diffs)
                std_err = scipy_stats.sem(diffs)
                # 95% CI
                ci_low, ci_high = scipy_stats.t.interval(0.95, len(diffs)-1, loc=mean_diff, scale=std_err)
                test_result["confidence_interval_95"] = {
                    "lower": float(ci_low),
                    "upper": float(ci_high)
                }
            else:
                # For Wilcoxon, we can't easily compute a parametric CI, 
                # but we can report the median difference
                diffs = np.array(greedy_vals) - np.array(prorl_vals)
                test_result["median_difference"] = float(np.median(diffs))
            
            results_summary["tests_performed"].append(test_result)
            
        except Exception as e:
            logger.error(f"Failed to run test for {metric_name}: {e}")
            results_summary["tests_performed"].append({
                "metric": metric_name,
                "error": str(e)
            })
    
    # Ensure output directory exists
    os.makedirs(results_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    logger.info(f"Statistical significance results written to {output_path}")
    return output_path

def run_sensitivity_analysis(
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Placeholder for T029 implementation.
    Sweeps decision cutoffs (path length, similarity threshold).
    """
    if config is None:
        config = get_config()
    
    # Implementation logic for T029 would go here
    # For T028b, we just ensure the function exists and is callable
    return []

def aggregate_sensitivity_report(
    analysis_results: List[Dict[str, Any]],
    output_path: str = "results/sensitivity_report.json"
) -> str:
    """
    Placeholder for T029b implementation.
    Aggregates sweep results.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"status": "pending", "results": analysis_results}, f, indent=2)
    return output_path