"""
T031: Implement bootstrap variance estimation for metric shifts.

This script loads baseline and cleaned metrics, computes the shifts (cleaned - baseline),
and performs bootstrap resampling to estimate the variance and 95% confidence intervals
of these shifts.

Dependency: T012 (baseline_metrics.json), T023 (cleaned_metrics.json)
Output: data/processed/bootstrap_variance_report.json
"""
import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import project utilities and config
from utils import setup_logging, pin_random_seed
from config import get_config

# Setup logging
logger = setup_logging("INFO")
config = get_config()

def load_json(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def compute_metric_shifts(
    baseline_metrics: Dict[str, Any], 
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, List[float]]:
    """
    Compute absolute shifts for p-values, CI widths, and effect sizes.
    
    Returns a dictionary mapping metric names to lists of shifts (one per dataset).
    """
    shifts = {
        "p_value_shift": [],
        "ci_width_shift": [],
        "effect_size_shift": []
    }
    
    # Normalize keys if necessary (handle potential list vs dict structures)
    baseline_list = baseline_metrics.get("results", baseline_metrics.get("datasets", []))
    cleaned_list = cleaned_metrics.get("results", cleaned_metrics.get("datasets", []))
    
    # Ensure we are comparing the same datasets (by name or index if names missing)
    # Assuming order is preserved or matched by name in the pipeline flow
    if len(baseline_list) != len(cleaned_list):
        logger.warning(f"Baseline ({len(baseline_list)}) and Cleaned ({len(cleaned_list)}) dataset counts mismatch. Aligning by index.")
        count = min(len(baseline_list), len(cleaned_list))
    else:
        count = len(baseline_list)
        
    for i in range(count):
        b = baseline_list[i]
        c = cleaned_list[i]
        
        # Extract p-value
        b_p = b.get("p_value")
        c_p = c.get("p_value")
        if b_p is not None and c_p is not None:
            shifts["p_value_shift"].append(c_p - b_p)
        
        # Extract CI width (assuming CI is stored as [lower, upper] or similar)
        b_ci = b.get("ci_bounds") # e.g., [lower, upper]
        c_ci = c.get("ci_bounds")
        if b_ci and c_ci and len(b_ci) == 2 and len(c_ci) == 2:
            b_width = abs(b_ci[1] - b_ci[0])
            c_width = abs(c_ci[1] - c_ci[0])
            shifts["ci_width_shift"].append(c_width - b_width)
        
        # Extract effect size
        b_es = b.get("effect_size")
        c_es = c.get("effect_size")
        if b_es is not None and c_es is not None:
            shifts["effect_size_shift"].append(c_es - b_es)
            
    return shifts

def bootstrap_confidence_interval(
    data: List[float], 
    n_resamples: int, 
    seed: int, 
    confidence: float = 0.95
) -> Tuple[float, float, float]:
    """
    Perform bootstrap resampling to estimate the mean and 95% CI of the data.
    
    Returns: (mean, lower_ci, upper_ci)
    """
    if len(data) == 0:
        return 0.0, 0.0, 0.0
        
    pin_random_seed(seed)
    data_arr = np.array(data)
    n = len(data_arr)
    
    bootstrap_means = []
    for _ in range(n_resamples):
        # Resample with replacement
        resample = np.random.choice(data_arr, size=n, replace=True)
        bootstrap_means.append(np.mean(resample))
        
    bootstrap_means = np.array(bootstrap_means)
    mean_estimate = np.mean(bootstrap_means)
    
    # Calculate percentile-based CI
    alpha = 1.0 - confidence
    lower = np.percentile(bootstrap_means, 100 * (alpha / 2))
    upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    
    return mean_estimate, lower, upper

def determine_bootstrap_iterations(dataset_size: int) -> int:
    """
    Determine number of bootstrap iterations.
    Default: 1000.
    Fallback: 500 if dataset size > 5000 rows.
    """
    if dataset_size > 5000:
        logger.info(f"Dataset size ({dataset_size}) > 5000. Reducing bootstrap iterations to 500.")
        return 500
    return 1000

def run_bootstrap_analysis(
    baseline_path: str, 
    cleaned_path: str, 
    output_path: str
) -> None:
    """
    Main logic to run bootstrap variance estimation.
    """
    logger.info(f"Loading baseline metrics from {baseline_path}")
    baseline_data = load_json(baseline_path)
    
    logger.info(f"Loading cleaned metrics from {cleaned_path}")
    cleaned_data = load_json(cleaned_path)
    
    # Estimate dataset size from the first available record to determine iterations
    # We assume all datasets in the run are roughly similar or we take the max
    # For simplicity, we check the first dataset's row count if available, else default to 1000
    dataset_size = 1000 # Default
    baseline_list = baseline_data.get("results", baseline_data.get("datasets", []))
    if baseline_list and isinstance(baseline_list[0], dict):
        # Try to find a row count field, or estimate from data length if it's a raw slice
        if "row_count" in baseline_list[0]:
            dataset_size = baseline_list[0]["row_count"]
        elif "data" in baseline_list[0] and isinstance(baseline_list[0]["data"], list):
            dataset_size = len(baseline_list[0]["data"])
    
    n_iterations = determine_bootstrap_iterations(dataset_size)
    random_seed = config.get("RANDOM_SEED", 42)
    
    logger.info(f"Running bootstrap analysis with {n_iterations} resamples (seed={random_seed})")
    
    shifts = compute_metric_shifts(baseline_data, cleaned_data)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "bootstrap_iterations": n_iterations,
        "random_seed": random_seed,
        "metrics": {}
    }
    
    for metric_name, shift_values in shifts.items():
        if not shift_values:
            logger.warning(f"No data found for shift calculation: {metric_name}")
            report["metrics"][metric_name] = {
                "shifts": [],
                "bootstrap_mean": None,
                "ci_lower": None,
                "ci_upper": None,
                "variance": None
            }
            continue
            
        mean_val, lower_val, upper_val = bootstrap_confidence_interval(
            shift_values, n_iterations, random_seed
        )
        variance_val = np.var(shift_values, ddof=1) if len(shift_values) > 1 else 0.0
        
        report["metrics"][metric_name] = {
            "shifts": shift_values,
            "bootstrap_mean": round(float(mean_val), 6),
            "ci_lower": round(float(lower_val), 6),
            "ci_upper": round(float(upper_val), 6),
            "variance": round(float(variance_val), 6),
            "sample_size": len(shift_values)
        }
        logger.info(f"Metric {metric_name}: Mean shift={mean_val:.6f}, 95% CI=[{lower_val:.6f}, {upper_val:.6f}]")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Bootstrap variance report saved to {output_path}")

def main():
    """Entry point for the script."""
    # Define paths based on project conventions
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/bootstrap_variance_report.json"
    
    # Check dependencies
    if not os.path.exists(baseline_path):
        logger.error(f"Dependency missing: {baseline_path}. Run T012 first.")
        return
    if not os.path.exists(cleaned_path):
        logger.error(f"Dependency missing: {cleaned_path}. Run T023 first.")
        return
        
    try:
        run_bootstrap_analysis(baseline_path, cleaned_path, output_path)
    except Exception as e:
        logger.error(f"Bootstrap analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()