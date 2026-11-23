import os
import json
import logging
import glob
import time
import hashlib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Callable
from scipy import stats
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_THRESHOLD = 0.10
BOOTSTRAP_ITERATIONS = 1000
SEED = 42

def calculate_error_rates(p_values: np.ndarray) -> float:
    """Calculate the proportion of p-values below 0.05."""
    if p_values is None or len(p_values) == 0:
        return 0.0
    return float(np.mean(p_values < 0.05))

def calculate_bootstrap_ci(
    p_values: np.ndarray, 
    statistic_func: Callable[[np.ndarray], float],
    n_iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = SEED
) -> Tuple[float, float, float]:
    """
    Calculate bootstrap confidence interval for a given statistic.
    
    Args:
        p_values: Array of p-values.
        statistic_func: Function to calculate the statistic (e.g., error rate).
        n_iterations: Number of bootstrap iterations.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (statistic, lower_ci, upper_ci).
    """
    if p_values is None or len(p_values) == 0:
        return 0.0, 0.0, 0.0
    
    rng = np.random.default_rng(seed)
    n = len(p_values)
    boot_stats = []
    
    for _ in range(n_iterations):
        sample = rng.choice(p_values, size=n, replace=True)
        boot_stats.append(statistic_func(sample))
    
    boot_stats = np.array(boot_stats)
    point_estimate = statistic_func(p_values)
    lower_ci = float(np.percentile(boot_stats, 2.5))
    upper_ci = float(np.percentile(boot_stats, 97.5))
    
    return point_estimate, lower_ci, upper_ci

def ks_test_wrapper(p_values_baseline: List[float], p_values_augmented: List[float]) -> Dict[str, float]:
    """
    Perform Kolmogorov-Smirnov test on two p-value distributions.
    
    Args:
        p_values_baseline: List of p-values from baseline.
        p_values_augmented: List of p-values from augmented data.
        
    Returns:
        Dictionary with 'statistic' and 'pvalue'.
    """
    if not p_values_baseline or not p_values_augmented:
        return {"statistic": 0.0, "pvalue": 1.0}
    
    stat, pval = stats.ks_2samp(p_values_baseline, p_values_augmented)
    return {"statistic": float(stat), "pvalue": float(pval)}

def analyze_baseline_results(baseline_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze baseline simulation results (Type I and Type II errors).
    
    Args:
        baseline_results: Dictionary containing p-value distributions for null and alt conditions.
        
    Returns:
        Dictionary with error rates and confidence intervals.
    """
    # Extract p-values
    null_p_values = np.array(baseline_results.get('p_values_null', []))
    alt_p_values = np.array(baseline_results.get('p_values_alt', []))
    
    # Calculate Type I error (null condition)
    type_i_rate, ci_low_i, ci_high_i = calculate_bootstrap_ci(
        null_p_values, 
        calculate_error_rates
    )
    
    # Calculate Type II error (alt condition)
    type_ii_rate, ci_low_ii, ci_high_ii = calculate_bootstrap_ci(
        alt_p_values, 
        calculate_error_rates
    )
    
    return {
        "type_i_error": type_i_rate,
        "type_i_ci": [ci_low_i, ci_high_i],
        "type_ii_error": type_ii_rate,
        "type_ii_ci": [ci_low_ii, ci_high_ii],
        "n_null_samples": len(null_p_values),
        "n_alt_samples": len(alt_p_values)
    }

def analyze_augmented_results(
    augmented_results: Dict[str, Any], 
    baseline_analysis: Dict[str, Any],
    threshold: float = DEFAULT_THRESHOLD
) -> Dict[str, Any]:
    """
    Analyze augmented simulation results and compare with baseline.
    
    Args:
        augmented_results: Dictionary containing p-value distributions.
        baseline_analysis: Pre-calculated baseline analysis.
        threshold: Safety threshold for Type I error.
        
    Returns:
        Dictionary with comparative analysis.
    """
    # Analyze augmented data
    aug_analysis = analyze_baseline_results(augmented_results)
    
    # Calculate differences
    diff_type_i = aug_analysis["type_i_error"] - baseline_analysis["type_i_error"]
    diff_type_ii = aug_analysis["type_ii_error"] - baseline_analysis["type_ii_error"]
    
    # Safety check
    is_unsafe = aug_analysis["type_i_error"] > threshold
    
    # KS Test
    ks_result = ks_test_wrapper(
        augmented_results.get('p_values_null', []),
        augmented_results.get('p_values_alt', [])
    )
    
    return {
        **aug_analysis,
        "difference_type_i": diff_type_i,
        "difference_type_ii": diff_type_ii,
        "is_unsafe": is_unsafe,
        "threshold": threshold,
        "ks_test": ks_result
    }

def calculate_computational_cost(iteration_times: List[float]) -> Dict[str, float]:
    """Calculate average and total computational cost."""
    if not iteration_times:
        return {"avg_time": 0.0, "total_time": 0.0}
    return {
        "avg_time": float(np.mean(iteration_times)),
        "total_time": float(np.sum(iteration_times))
    }

def validate_against_schema(data: Dict[str, Any], schema_path: str) -> bool:
    """Validate data against a JSON schema (placeholder for jsonschema validation)."""
    # In a real implementation, use jsonschema library
    if not data:
        return False
    # Basic structural check
    required_keys = ["type_i_error", "type_ii_error"]
    return all(k in data for k in required_keys)

def save_report(report: Dict[str, Any], output_path: str) -> None:
    """Save report to JSON file."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def generate_sensitivity_analysis(
    results_dir: str = "results",
    baseline_threshold: float = DEFAULT_THRESHOLD,
    alternative_thresholds: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on safety thresholds.
    
    Re-runs comparative analysis with alternative thresholds to demonstrate
    robustness of "unsafe" classification near the boundary.
    
    Args:
        results_dir: Directory containing result JSON files.
        baseline_threshold: The primary safety threshold (default 0.10).
        alternative_thresholds: List of alternative thresholds to test.
        
    Returns:
        Dictionary containing sensitivity analysis results.
    """
    if alternative_thresholds is None:
        alternative_thresholds = [0.05, 0.08, 0.12, 0.15]
    
    logger.info(f"Starting sensitivity analysis with thresholds: {alternative_thresholds}")
    
    # Load all result files
    pattern = os.path.join(results_dir, "*.json")
    result_files = glob.glob(pattern)
    
    if not result_files:
        logger.warning(f"No result files found in {results_dir}")
        return {"error": "No result files found", "thresholds_tested": alternative_thresholds}
    
    sensitivity_data = {
        "baseline_threshold": baseline_threshold,
        "thresholds_tested": alternative_thresholds,
        "configurations": []
    }
    
    for file_path in result_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Skip files that don't have necessary analysis data
            if 'type_i_error' not in data:
                continue
            
            config_name = os.path.basename(file_path)
            type_i_error = data.get('type_i_error', 0.0)
            
            # Analyze across thresholds
            threshold_violations = {}
            for thresh in alternative_thresholds:
                is_violation = type_i_error > thresh
                threshold_violations[str(thresh)] = {
                    "violation": is_violation,
                    "margin": type_i_error - thresh
                }
            
            # Check stability near baseline
            near_baseline = []
            for thresh in [baseline_threshold - 0.02, baseline_threshold + 0.02]:
                if thresh in [float(t) for t in alternative_thresholds]:
                    near_baseline.append(threshold_violations.get(str(thresh)))
            
            sensitivity_data["configurations"].append({
                "file": config_name,
                "type_i_error": type_i_error,
                "threshold_violations": threshold_violations,
                "near_baseline_stability": near_baseline
            })
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Skipping {file_path} due to error: {e}")
            continue
    
    # Summary statistics
    unstable_configs = 0
    for config in sensitivity_data["configurations"]:
        violations = list(config["threshold_violations"].values())
        # Check if classification flips near the baseline threshold
        if len(violations) >= 2:
            # Simple heuristic: if any violation status changes in the tested range
            violation_flags = [v["violation"] for v in violations]
            if any(v != violation_flags[0] for v in violation_flags):
                unstable_configs += 1
    
    sensitivity_data["summary"] = {
        "total_configurations": len(sensitivity_data["configurations"]),
        "unstable_classifications": unstable_configs,
        "stability_rate": 1.0 - (unstable_configs / len(sensitivity_data["configurations"])) if sensitivity_data["configurations"] else 1.0
    }
    
    return sensitivity_data

def generate_report(
    results_dir: str = "results",
    schema_path: str = "contracts/simulation_schema.json",
    output_path: str = "results/summary_report.json",
    sensitivity_thresholds: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Generate the final summary report including sensitivity analysis.
    
    Args:
        results_dir: Directory containing result JSON files.
        schema_path: Path to the validation schema.
        output_path: Path to save the final report.
        sensitivity_thresholds: List of thresholds for sensitivity analysis.
        
    Returns:
        The generated report dictionary.
    """
    logger.info("Generating summary report...")
    
    # 1. Load and aggregate all results
    pattern = os.path.join(results_dir, "*.json")
    result_files = glob.glob(pattern)
    
    all_results = []
    for file_path in result_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            if 'type_i_error' in data: # Basic filter
                all_results.append(data)
        except Exception as e:
            logger.warning(f"Could not load {file_path}: {e}")
    
    if not all_results:
        logger.error("No valid result data found to aggregate.")
        return {"error": "No valid data found"}
    
    # 2. Calculate aggregate statistics
    avg_type_i = float(np.mean([r['type_i_error'] for r in all_results]))
    avg_type_ii = float(np.mean([r['type_ii_error'] for r in all_results]))
    
    # 3. Perform Sensitivity Analysis (T041)
    sensitivity_result = generate_sensitivity_analysis(
        results_dir=results_dir,
        baseline_threshold=DEFAULT_THRESHOLD,
        alternative_thresholds=sensitivity_thresholds
    )
    
    report = {
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "version": "1.0",
            "description": "Summary report with sensitivity analysis"
        },
        "aggregate_metrics": {
            "average_type_i_error": avg_type_i,
            "average_type_ii_error": avg_type_ii,
            "power": 1.0 - avg_type_ii
        },
        "safety_threshold": DEFAULT_THRESHOLD,
        "sensitivity_analysis": sensitivity_result,
        "configurations_count": len(all_results)
    }
    
    # Validate and save
    if schema_path and os.path.exists(schema_path):
        if not validate_against_schema(report, schema_path):
            logger.warning("Report validation failed against schema.")
    
    save_report(report, output_path)
    return report

def main():
    """Main entry point for analysis."""
    import argparse
    parser = argparse.ArgumentParser(description="Analyze simulation results")
    parser.add_argument("--validate", action="store_true", help="Run validation and generate report")
    parser.add_argument("--results-dir", default="results", help="Directory with result files")
    parser.add_argument("--output", default="results/summary_report.json", help="Output report path")
    args = parser.parse_args()
    
    if args.validate:
        report = generate_report(
            results_dir=args.results_dir,
            output_path=args.output
        )
        print(json.dumps(report, indent=2))
    else:
        logger.info("No action specified. Use --validate to generate report.")

if __name__ == "__main__":
    main()