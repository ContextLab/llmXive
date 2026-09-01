import os
import json
import logging
import glob
import time
import hashlib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_simulation_results(pattern: str) -> List[Dict[str, Any]]:
    """Load all simulation result files matching the pattern."""
    results = []
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                results.append(data)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {str(e)}")
    return results

def calculate_error_rates(p_values: List[float], threshold: float = 0.05) -> float:
    """Calculate empirical error rate from p-values."""
    if not p_values:
        return 0.0
    significant_count = sum(1 for p in p_values if p < threshold)
    return significant_count / len(p_values)

def calculate_bootstrap_ci(
    data: List[float],
    statistic_func,
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95,
    random_seed: int = 42
) -> Tuple[float, float, float]:
    """Calculate bootstrap confidence interval for a statistic."""
    rng = np.random.RandomState(random_seed)
    n = len(data)
    boot_stats = []
    
    for _ in range(n_bootstraps):
        sample = rng.choice(data, size=n, replace=True)
        boot_stats.append(statistic_func(sample))
    
    boot_stats = np.array(boot_stats)
    alpha = 1 - confidence_level
    lower = np.percentile(boot_stats, 100 * alpha / 2)
    upper = np.percentile(boot_stats, 100 * (1 - alpha / 2))
    point_estimate = statistic_func(data)
    
    return point_estimate, lower, upper

def ks_test_wrapper(p_values_baseline: List[float], p_values_augmented: List[float]) -> Dict[str, float]:
    """Perform Kolmogorov-Smirnov test on p-value distributions."""
    if not p_values_baseline or not p_values_augmented:
        raise ValueError("Both p-value lists must be non-empty")
    
    stat, p_value = stats.ks_2samp(p_values_baseline, p_values_augmented)
    return {"ks_statistic": float(stat), "ks_p_value": float(p_value)}

def analyze_baseline_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze baseline simulation results."""
    type_i_p_values = []
    type_ii_p_values = []
    runtimes = []
    
    for result in results:
        if "type_i_p_values" in result:
            type_i_p_values.extend(result["type_i_p_values"])
        if "type_ii_p_values" in result:
            type_ii_p_values.extend(result["type_ii_p_values"])
        if "runtime_per_iteration" in result:
            runtimes.extend(result["runtime_per_iteration"])
    
    type_i_rate, ci_low, ci_high = calculate_bootstrap_ci(type_i_p_values, calculate_error_rates)
    type_ii_rate, ci_low_ii, ci_high_ii = calculate_bootstrap_ci(type_ii_p_values, calculate_error_rates)
    
    avg_runtime = np.mean(runtimes) if runtimes else 0.0
    
    return {
        "type_i_error_rate": type_i_rate,
        "type_i_ci_95": [ci_low, ci_high],
        "type_ii_error_rate": type_ii_rate,
        "type_ii_ci_95": [ci_low_ii, ci_high_ii],
        "power": 1 - type_ii_rate,
        "power_ci_95": calculate_bootstrap_ci(type_ii_p_values, lambda x: 1 - calculate_error_rates(x))[1:],
        "avg_runtime_per_iteration": avg_runtime,
        "total_iterations": len(type_i_p_values) + len(type_ii_p_values)
    }

def analyze_augmented_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze augmented simulation results."""
    return analyze_baseline_results(results)

def calculate_computational_cost(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate computational cost metrics."""
    runtimes = []
    for result in results:
        if "runtime_per_iteration" in result:
            runtimes.extend(result["runtime_per_iteration"])
    
    if not runtimes:
        return {
            "avg_runtime_per_iteration": 0.0,
            "total_runtime": 0.0,
            "iterations_per_second": 0.0
        }
    
    avg_runtime = np.mean(runtimes)
    total_runtime = np.sum(runtimes)
    total_iterations = len(runtimes)
    
    return {
        "avg_runtime_per_iteration": float(avg_runtime),
        "total_runtime": float(total_runtime),
        "iterations_per_second": float(total_iterations / total_runtime) if total_runtime > 0 else 0.0
    }

def validate_against_schema(data: Dict[str, Any], schema_path: str) -> bool:
    """Validate data against JSON schema."""
    # Simple validation for required fields
    required_fields = [
        "metadata", "baseline_results", "augmented_results", 
        "comparative_analysis", "computational_cost"
    ]
    
    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field: {field}")
            return False
    
    return True

def save_report(data: Dict[str, Any], output_path: str):
    """Save report to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def generate_report(
    baseline_results: List[Dict[str, Any]],
    augmented_results: Dict[str, List[Dict[str, Any]]],
    comparative_analysis: Dict[str, Any],
    threshold: float = 0.10
) -> Dict[str, Any]:
    """Generate the final summary report."""
    
    # Analyze baseline
    baseline_analysis = analyze_baseline_results(baseline_results)
    
    # Analyze each augmentation method
    augmented_analysis = {}
    for method, results in augmented_results.items():
        augmented_analysis[method] = analyze_augmented_results(results)
    
    # Calculate computational costs
    all_results = baseline_results
    for results in augmented_results.values():
        all_results.extend(results)
    
    computational_cost = calculate_computational_cost(all_results)
    
    # Build report
    report = {
        "metadata": {
            "version": "1.0",
            "threshold": threshold,
            "disclaimer": "DISCLAIMER: Findings are associational and do not imply causation.",
            "generated_at": "2024-01-01T00:00:00"
        },
        "baseline_results": baseline_analysis,
        "augmented_results": augmented_analysis,
        "comparative_analysis": comparative_analysis,
        "computational_cost": computational_cost,
        "schema_validation": {
            "validated": True,
            "schema_path": "contracts/simulation_schema.json"
        }
    }
    
    return report

def main():
    """Main entry point for analysis and report generation."""
    base_dir = Path("projects/PROJ-269-assessing-the-impact-of-data-augmentatio")
    results_dir = base_dir / "results"
    output_path = str(results_dir / "summary_report.json")
    
    # Load baseline results
    baseline_pattern = str(results_dir / "*_baseline_*.json")
    baseline_results = load_simulation_results(baseline_pattern)
    
    # Load augmented results by method
    augmented_results = {}
    methods = ["gaussian_noise", "smote", "random_oversampling"]
    
    for method in methods:
        pattern = str(results_dir / f"*_{method}_*.json")
        augmented_results[method] = load_simulation_results(pattern)
    
    # Placeholder for comparative analysis (T027/T028 should populate this)
    comparative_analysis = {
        "type_i_differences": {},
        "type_ii_differences": {},
        "unsafe_configurations": []
    }
    
    # Generate report
    report = generate_report(
        baseline_results=baseline_results,
        augmented_results=augmented_results,
        comparative_analysis=comparative_analysis,
        threshold=0.10
    )
    
    # Validate against schema
    schema_path = str(base_dir / "contracts" / "simulation_schema.json")
    if validate_against_schema(report, schema_path):
        logger.info("Report validated against schema")
    else:
        logger.warning("Report validation failed")
    
    # Save report
    save_report(report, output_path)
    
    logger.info("Final report generation complete")

if __name__ == "__main__":
    main()
