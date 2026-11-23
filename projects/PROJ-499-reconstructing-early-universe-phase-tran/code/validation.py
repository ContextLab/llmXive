import json
import os
import sys
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from scipy.special import erf

# Import from sibling modules as per API surface
from config import get_config

def validate_inflation_synthetic(
    inference_file: str,
    true_r: float,
    output_file: str
) -> Dict[str, Any]:
    """
    Validate the posterior distribution for the inflationary tensor-to-scalar ratio r.
    
    Metrics (SC-005):
    1. Coverage: true_r must be within [percentile_2.5, percentile_97.5] of the posterior.
    2. Centering: |(mean - true)| / true < 0.10 (10% relative error).
    
    Args:
        inference_file: Path to the JSON file containing inference results (from T025a).
        true_r: The ground truth value of r used to generate the synthetic data.
        output_file: Path where the validation report JSON will be written.
        
    Returns:
        A dictionary containing the validation results and metrics.
    """
    # Load inference results
    if not os.path.exists(inference_file):
        raise FileNotFoundError(f"Inference results file not found: {inference_file}")
        
    with open(inference_file, 'r') as f:
        results = json.load(f)
    
    # Extract posterior samples for 'r'
    # Assuming the structure from run_inference_synthetic: {"samples": {"r": [...]}}
    if "samples" not in results or "r" not in results["samples"]:
        raise ValueError(f"Expected 'samples' -> 'r' in {inference_file}, but keys found: {results.keys()}")
    
    r_samples = np.array(results["samples"]["r"])
    
    if len(r_samples) == 0:
        raise ValueError("Posterior samples for 'r' are empty.")
    
    # Compute statistics
    mean_r = np.mean(r_samples)
    median_r = np.median(r_samples)
    std_r = np.std(r_samples)
    percentile_2_5 = np.percentile(r_samples, 2.5)
    percentile_97_5 = np.percentile(r_samples, 97.5)
    
    # Check Coverage (95% CI)
    covers_true = percentile_2_5 <= true_r <= percentile_97_5
    
    # Check Centering (10% relative error)
    relative_error = abs(mean_r - true_r) / true_r if true_r != 0 else abs(mean_r)
    centered = relative_error < 0.10
    
    # Overall pass/fail
    passed = covers_true and centered
    
    # Construct report
    report = {
        "metric": "SC-005: Inflation Synthetic Validation",
        "parameter": "r",
        "true_value": true_r,
        "posterior_stats": {
            "mean": float(mean_r),
            "median": float(median_r),
            "std": float(std_r),
            "percentile_2.5": float(percentile_2_5),
            "percentile_97.5": float(percentile_97_5)
        },
        "checks": {
            "coverage_95_ci": {
                "passed": covers_true,
                "description": "true_value within [2.5%, 97.5%] percentiles",
                "interval": [float(percentile_2_5), float(percentile_97_5)]
            },
            "centering_10pct": {
                "passed": centered,
                "description": "|(mean - true)| / true < 0.10",
                "relative_error": float(relative_error)
            }
        },
        "overall_passed": passed
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write report to disk
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def validate_pt_synthetic(
    inference_file: str,
    true_E_pt: float,
    output_file: str
) -> Dict[str, Any]:
    """
    Validate the posterior distribution for the Phase Transition energy scale E_PT.
    
    Metrics (SC-005):
    1. Coverage: true_E_pt must be within [percentile_2.5, percentile_97.5] of the posterior.
    2. Centering: |(mean - true)| / true < 0.10 (10% relative error).
    
    Args:
        inference_file: Path to the JSON file containing inference results.
        true_E_pt: The ground truth value of E_PT used to generate the synthetic data.
        output_file: Path where the validation report JSON will be written.
        
    Returns:
        A dictionary containing the validation results and metrics.
    """
    # Load inference results
    if not os.path.exists(inference_file):
        raise FileNotFoundError(f"Inference results file not found: {inference_file}")
        
    with open(inference_file, 'r') as f:
        results = json.load(f)
    
    # Extract posterior samples for 'E_PT'
    if "samples" not in results or "E_PT" not in results["samples"]:
        raise ValueError(f"Expected 'samples' -> 'E_PT' in {inference_file}, but keys found: {results.keys()}")
    
    e_pt_samples = np.array(results["samples"]["E_PT"])
    
    if len(e_pt_samples) == 0:
        raise ValueError("Posterior samples for 'E_PT' are empty.")
    
    # Compute statistics
    mean_e = np.mean(e_pt_samples)
    median_e = np.median(e_pt_samples)
    std_e = np.std(e_pt_samples)
    percentile_2_5 = np.percentile(e_pt_samples, 2.5)
    percentile_97_5 = np.percentile(e_pt_samples, 97.5)
    
    # Check Coverage (95% CI)
    covers_true = percentile_2_5 <= true_E_pt <= percentile_97_5
    
    # Check Centering (10% relative error)
    relative_error = abs(mean_e - true_E_pt) / true_E_pt if true_E_pt != 0 else abs(mean_e)
    centered = relative_error < 0.10
    
    # Overall pass/fail
    passed = covers_true and centered
    
    # Construct report
    report = {
        "metric": "SC-005: Phase Transition Synthetic Validation",
        "parameter": "E_PT",
        "true_value": true_E_pt,
        "posterior_stats": {
            "mean": float(mean_e),
            "median": float(median_e),
            "std": float(std_e),
            "percentile_2.5": float(percentile_2_5),
            "percentile_97.5": float(percentile_97_5)
        },
        "checks": {
            "coverage_95_ci": {
                "passed": covers_true,
                "description": "true_value within [2.5%, 97.5%] percentiles",
                "interval": [float(percentile_2_5), float(percentile_97_5)]
            },
            "centering_10pct": {
                "passed": centered,
                "description": "|(mean - true)| / true < 0.10",
                "relative_error": float(relative_error)
            }
        },
        "overall_passed": passed
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write report to disk
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def validate_bayes_factor_synthetic(
    model_comparison_file: str,
    true_model: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Validate that the Bayes factor correctly distinguishes between models.
    
    Requirement: K > 10 for the correct model distinction.
    
    Args:
        model_comparison_file: Path to the JSON file containing model comparison results.
        true_model: The ground truth model name (e.g., 'inflation', 'pt', 'null').
        output_file: Path where the validation report JSON will be written.
        
    Returns:
        A dictionary containing the validation results.
    """
    if not os.path.exists(model_comparison_file):
        raise FileNotFoundError(f"Model comparison file not found: {model_comparison_file}")
        
    with open(model_comparison_file, 'r') as f:
        results = json.load(f)
    
    # Assuming structure: {"bayes_factors": {"inflation_vs_pt": K_val, ...}}
    # We need to verify that the Bayes factor favoring the true model is > 10.
    # This is a simplified check; in reality, one would check specific pairwise comparisons.
    
    bayes_factors = results.get("bayes_factors", {})
    
    # Determine if the correct model was favored with K > 10
    # This logic depends on the specific keys in model_comparison_file.
    # For now, we assume a key like f"{true_model}_vs_null" exists and should be > 10.
    key_to_check = f"{true_model}_vs_null"
    k_value = bayes_factors.get(key_to_check, 0.0)
    
    passed = k_value > 10.0
    
    report = {
        "metric": "Bayes Factor Synthetic Validation",
        "true_model": true_model,
        "bayes_factors": bayes_factors,
        "check": {
            "description": f"Bayes factor for {true_model} vs Null > 10",
            "key_checked": key_to_check,
            "k_value": k_value,
            "threshold": 10.0,
            "passed": passed
        },
        "overall_passed": passed
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write report to disk
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """
    Main entry point to run validation on synthetic data.
    Reads configuration to find paths and true values.
    """
    config = get_config()
    
    # Paths from config or defaults
    # Inflation validation
    inf_file = config.get("INFERENCE_INFLATION_FILE", "data/synthetic/inference_results_inflation.json")
    true_r = config.get("TRUE_R", 0.01)
    out_inf = config.get("VALIDATION_REPORT_INFLATION", "data/validation/validation_report_inflation.json")
    
    # PT validation
    pt_file = config.get("INFERENCE_PT_FILE", "data/synthetic/inference_results_pt.json")
    true_e_pt = config.get("TRUE_E_PT", 1e15)
    out_pt = config.get("VALIDATION_REPORT_PT", "data/validation/validation_report_pt.json")
    
    # Bayes Factor validation
    bf_file = config.get("MODEL_COMPARISON_FILE", "data/derived/model_comparison_results.json")
    true_model = config.get("TRUE_MODEL", "inflation")
    out_bf = config.get("BAYES_FACTOR_VALIDATION", "data/validation/bayes_factor_validation.json")
    
    print("Running inflation synthetic validation...")
    try:
        report_inf = validate_inflation_synthetic(inf_file, true_r, out_inf)
        print(f"Inflation validation passed: {report_inf['overall_passed']}")
    except Exception as e:
        print(f"Inflation validation failed: {e}")
        
    print("Running PT synthetic validation...")
    try:
        report_pt = validate_pt_synthetic(pt_file, true_e_pt, out_pt)
        print(f"PT validation passed: {report_pt['overall_passed']}")
    except Exception as e:
        print(f"PT validation failed: {e}")
        
    print("Running Bayes factor validation...")
    try:
        report_bf = validate_bayes_factor_synthetic(bf_file, true_model, out_bf)
        print(f"Bayes factor validation passed: {report_bf['overall_passed']}")
    except Exception as e:
        print(f"Bayes factor validation failed: {e}")

if __name__ == "__main__":
    main()
