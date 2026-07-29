"""
Statistics utilities for ablation and scaling analysis.

Provides functions for statistical testing (t-tests, KS tests) and
scaling law analysis on experimental results.
"""
import json
import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def load_gradient_norms(file_path: str) -> List[Dict[str, Any]]:
    """
    Load gradient norms from a JSON log file.
    
    Args:
        file_path: Path to the gradient norms JSON file.
        
    Returns:
        List of dictionaries containing gradient norm data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Gradient norms file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    return data


def compare_gradient_stability(
    baseline_path: str,
    microcircuit_path: str
) -> Dict[str, Any]:
    """
    Perform a Kolmogorov-Smirnov test between baseline and microcircuit gradient norms.
    
    This is the definitive verification for SC-002 (Gradient Stability).
    
    Args:
        baseline_path: Path to baseline gradient norms JSON file.
        microcircuit_path: Path to microcircuit gradient norms JSON file.
        
    Returns:
        Dictionary with schema:
        {
            "ks_statistic": float,
            "p_value": float,
            "stable": bool
        }
        where stable is True if p_value > 0.05 (no significant difference).
    """
    baseline_data = load_gradient_norms(baseline_path)
    microcircuit_data = load_gradient_norms(microcircuit_path)
    
    # Extract gradient norms (assuming they are stored in a 'norms' or 'values' key)
    # Adjust key based on actual log format
    baseline_norms = []
    microcircuit_norms = []
    
    for entry in baseline_data:
        if isinstance(entry, dict):
            # Try common keys
            for key in ['norm', 'gradient_norm', 'value', 'norms']:
                if key in entry:
                    baseline_norms.append(entry[key])
                    break
        elif isinstance(entry, (int, float)):
            baseline_norms.append(entry)
    
    for entry in microcircuit_data:
        if isinstance(entry, dict):
            for key in ['norm', 'gradient_norm', 'value', 'norms']:
                if key in entry:
                    microcircuit_norms.append(entry[key])
                    break
        elif isinstance(entry, (int, float)):
            microcircuit_norms.append(entry)
    
    if len(baseline_norms) < 2 or len(microcircuit_norms) < 2:
        raise ValueError("Insufficient data points for statistical comparison")
    
    # Perform two-sample KS test
    ks_statistic, p_value = stats.ks_2samp(baseline_norms, microcircuit_norms)
    
    result = {
        "ks_statistic": float(ks_statistic),
        "p_value": float(p_value),
        "stable": bool(p_value > 0.05)
    }
    
    logger.info(f"Gradient stability KS-test: stat={ks_statistic:.4f}, p={p_value:.4f}, stable={result['stable']}")
    
    return result


def compare_ablation_results(
    ablation_results_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Compute the difference in MAE between full and ablated models using a paired t-test.
    
    Reads ablation results from a JSON file, identifies the 'full' variant and
    compares it against ablated variants using a paired t-test.
    
    Args:
        ablation_results_path: Path to ablation_results.json.
        output_path: Path to write ablation_stats.json output.
        
    Returns:
        Dictionary with schema:
        {
            "full_mae": float,
            "ablated_mae": float,
            "mae_diff": float,
            "p_value": float,
            "significant": bool
        }
        
    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If required data is missing or malformed.
    """
    if not os.path.exists(ablation_results_path):
        raise FileNotFoundError(f"Ablation results file not found: {ablation_results_path}")
    
    with open(ablation_results_path, 'r') as f:
        data = json.load(f)
    
    # Expected schema: {"results": [{"variant": str, "mae": float, "time": float}]}
    if "results" not in data or not isinstance(data["results"], list):
        raise ValueError("Invalid ablation results format: expected 'results' list")
    
    results = data["results"]
    
    # Find full and ablated variants
    full_result = None
    ablated_results = []
    
    for item in results:
        variant_name = item.get("variant", "").lower()
        mae = item.get("mae")
        
        if mae is None:
            raise ValueError(f"Missing MAE value for variant: {variant_name}")
        
        if variant_name == "full":
            full_result = item
        else:
            ablated_results.append(item)
    
    if full_result is None:
        raise ValueError("No 'full' variant found in ablation results")
    
    if len(ablated_results) == 0:
        raise ValueError("No ablated variants found in results")
    
    full_mae = full_result["mae"]
    ablated_maes = [r["mae"] for r in ablated_results]
    
    # Calculate average ablated MAE
    ablated_mae = float(np.mean(ablated_maes))
    mae_diff = full_mae - ablated_mae
    
    # Perform paired t-test if we have multiple ablated runs
    # For paired test, we need matched pairs. If we have multiple ablated variants,
    # we treat them as a sample against the single full value (one-sample t-test)
    # or if we have multiple runs per variant, we could do paired.
    # Here we do a one-sample t-test: is the mean of (full - ablated) significantly different from 0?
    
    differences = [full_mae - mae for mae in ablated_maes]
    
    if len(differences) < 2:
        # Cannot compute t-test with single sample
        # Use the single difference as the result
        p_value = 1.0  # Not significant by default
        logger.warning("Only one ablated variant found; cannot compute t-test. Setting p_value=1.0")
    else:
        # One-sample t-test: test if mean difference is significantly different from 0
        t_stat, p_value = stats.ttest_1samp(differences, 0.0)
    
    result = {
        "full_mae": float(full_mae),
        "ablated_mae": ablated_mae,
        "mae_diff": float(mae_diff),
        "p_value": float(p_value),
        "significant": bool(p_value < 0.05)
    }
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Ablation comparison: full_mae={full_mae:.4f}, ablated_mae={ablated_mae:.4f}, diff={mae_diff:.4f}, p={p_value:.4f}, significant={result['significant']}")
    
    return result


def calculate_scaling_exponent(
    scaling_results_path: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fit a power-law model to scaling performance data.
    
    Fits: log(MAE) = exponent * log(Parameters) + intercept
    
    Args:
        scaling_results_path: Path to scaling_results.json.
        output_path: Optional path to write scaling_exponent.json.
        
    Returns:
        Dictionary with schema:
        {
            "exponent": float,
            "r_squared": float,
            "interpretation": str
        }
    """
    if not os.path.exists(scaling_results_path):
        raise FileNotFoundError(f"Scaling results file not found: {scaling_results_path}")
    
    with open(scaling_results_path, 'r') as f:
        data = json.load(f)
    
    # Expected schema: {"variants": [{"columns": str, "params": int, "mae": float, "time": float}]}
    if "variants" not in data or not isinstance(data["variants"], list):
        raise ValueError("Invalid scaling results format: expected 'variants' list")
    
    variants = data["variants"]
    
    params_list = []
    mae_list = []
    
    for item in variants:
        params = item.get("params")
        mae = item.get("mae")
        
        if params is None or mae is None:
            raise ValueError(f"Missing params or mae in variant: {item}")
        
        params_list.append(float(params))
        mae_list.append(float(mae))
    
    if len(params_list) < 2:
        raise ValueError("Need at least 2 data points to fit scaling law")
    
    # Log-transform
    log_params = np.log(params_list)
    log_mae = np.log(mae_list)
    
    # Fit linear model
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_params, log_mae)
    
    exponent = float(slope)
    r_squared = float(r_value ** 2)
    
    # Interpretation
    if abs(exponent) < 0.1:
        interpretation = "near-zero scaling (performance independent of size)"
    elif exponent > 0:
        interpretation = "superlinear scaling (worse with size)"
    else:
        # exponent is negative
        if abs(exponent) < 0.5:
            interpretation = "sublinear scaling (slow improvement with size)"
        elif abs(exponent) < 1.0:
            interpretation = "near-linear scaling"
        else:
            interpretation = "superlinear improvement (faster than linear)"
    
    result = {
        "exponent": exponent,
        "r_squared": r_squared,
        "intercept": float(intercept),
        "p_value": float(p_value),
        "interpretation": interpretation
    }
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
    
    logger.info(f"Scaling exponent: {exponent:.4f}, R²={r_squared:.4f}, interpretation={interpretation}")
    
    return result


def main():
    """CLI entry point for statistics utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Statistics utilities for ablation and scaling analysis")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # compare_ablation_results command
    ablation_parser = subparsers.add_parser("compare_ablation", help="Compare ablation results")
    ablation_parser.add_argument("--input", required=True, help="Path to ablation_results.json")
    ablation_parser.add_argument("--output", required=True, help="Path to write ablation_stats.json")
    
    # compare_gradient_stability command
    gradient_parser = subparsers.add_parser("compare_gradients", help="Compare gradient stability")
    gradient_parser.add_argument("--baseline", required=True, help="Path to baseline gradient norms")
    gradient_parser.add_argument("--microcircuit", required=True, help="Path to microcircuit gradient norms")
    gradient_parser.add_argument("--output", required=True, help="Path to write gradient_stability.json")
    
    # calculate_scaling_exponent command
    scaling_parser = subparsers.add_parser("scaling_exponent", help="Calculate scaling exponent")
    scaling_parser.add_argument("--input", required=True, help="Path to scaling_results.json")
    scaling_parser.add_argument("--output", help="Path to write scaling_exponent.json (optional)")
    
    args = parser.parse_args()
    
    if args.command == "compare_ablation":
        result = compare_ablation_results(args.input, args.output)
        print(json.dumps(result, indent=2))
    
    elif args.command == "compare_gradients":
        result = compare_gradient_stability(args.baseline, args.microcircuit)
        # Write to output file
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(json.dumps(result, indent=2))
    
    elif args.command == "scaling_exponent":
        result = calculate_scaling_exponent(args.input, args.output)
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
