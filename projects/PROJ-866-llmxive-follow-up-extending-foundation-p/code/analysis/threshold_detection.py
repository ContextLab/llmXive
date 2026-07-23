import json
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy.optimize import brentq
from scipy.stats import norm

# Import from existing modules in the project
from analysis.tradeoff_model import load_processed_logs, fit_tradeoff_curve, calculate_safe_threshold
from analysis.multiple_comparison_correction import apply_correction, benjamini_hochberg_correction

def bootstrap_threshold(
    reduction_values: np.ndarray,
    error_values: np.ndarray,
    threshold_pct: float = 1.0,
    n_resamples: int = 1000,
    rng: Optional[np.random.Generator] = None
) -> Tuple[float, float, float]:
    """
    Perform bootstrapping to calculate the 95% confidence interval for the threshold.
    
    Args:
        reduction_values: Array of context reduction percentages
        error_values: Array of error rates corresponding to reduction values
        threshold_pct: The target error threshold (default 1%)
        n_resamples: Number of bootstrap resamples (default 1000)
        rng: Random number generator for reproducibility
        
    Returns:
        Tuple of (threshold_estimate, ci_lower, ci_upper)
    """
    if rng is None:
        rng = np.random.default_rng(42)
        
    n = len(reduction_values)
    bootstrap_thresholds = []
    
    for _ in range(n_resamples):
        # Resample with replacement
        indices = rng.integers(0, n, size=n)
        boot_reductions = reduction_values[indices]
        boot_errors = error_values[indices]
        
        # Sort by reduction to ensure monotonicity for interpolation
        sort_idx = np.argsort(boot_reductions)
        boot_reductions = boot_reductions[sort_idx]
        boot_errors = boot_errors[sort_idx]
        
        # Find the maximum reduction where error <= threshold
        # We look for the point where error crosses the threshold
        valid_mask = boot_errors <= (threshold_pct / 100.0)
        
        if not np.any(valid_mask):
            # If no valid points, take the minimum reduction
            bootstrap_thresholds.append(boot_reductions[0])
            continue
            
        # Get the maximum reduction among valid points
        max_valid_reduction = boot_reductions[valid_mask].max()
        bootstrap_thresholds.append(max_valid_reduction)
    
    bootstrap_thresholds = np.array(bootstrap_thresholds)
    threshold_estimate = np.median(bootstrap_thresholds)
    ci_lower = np.percentile(bootstrap_thresholds, 2.5)
    ci_upper = np.percentile(bootstrap_thresholds, 97.5)
    
    return threshold_estimate, ci_lower, ci_upper

def detect_threshold_with_correction(
    logs_path: str,
    output_dir: str,
    target_error_pct: float = 1.0,
    n_resamples: int = 1000,
    correction_method: str = "benjamini_hochberg"
) -> Dict[str, Any]:
    """
    Main function to detect the threshold with multiple comparison correction and bootstrapping.
    
    Args:
        logs_path: Path to the processed execution logs directory
        output_dir: Directory to save results
        target_error_pct: Target error percentage threshold (default 1%)
        n_resamples: Number of bootstrap resamples
        correction_method: Method for multiple comparison correction
        
    Returns:
        Dictionary containing threshold detection results
    """
    # Load processed logs
    logs = load_processed_logs(logs_path)
    
    if not logs:
        raise ValueError(f"No processed logs found at {logs_path}")
    
    # Prepare data for analysis
    # Extract context reduction percentages and error rates
    reduction_values = []
    error_values = []
    workflow_ids = []
    
    for log in logs:
        # Calculate context reduction percentage
        if 'context_reduction_pct' in log and isinstance(log['context_reduction_pct'], (int, float)):
            reduction = log['context_reduction_pct']
        else:
            continue
            
        # Calculate error rate (violation rate)
        total_steps = log.get('total_steps', 0)
        violations = log.get('policy_violations', 0)
        
        if total_steps > 0:
            error_rate = (violations / total_steps) * 100.0
        else:
            continue
            
        reduction_values.append(reduction)
        error_values.append(error_rate)
        workflow_ids.append(log.get('workflow_id', 'unknown'))
    
    reduction_values = np.array(reduction_values)
    error_values = np.array(error_values)
    
    # Apply multiple comparison correction to error values
    # This adjusts for the fact that we're testing multiple reduction levels
    if correction_method == "bonferroni":
        # Bonferroni correction is typically for p-values, but we can adapt it
        # by adjusting the threshold based on the number of tests
        n_tests = len(np.unique(reduction_values))
        adjusted_target = target_error_pct / n_tests
        corrected_errors = error_values * n_tests
        corrected_errors = np.minimum(corrected_errors, 100.0)  # Cap at 100%
    elif correction_method == "benjamini_hochberg":
        # Benjamini-Hochberg for FDR control
        # We'll use this to adjust the effective threshold
        unique_reductions = np.unique(reduction_values)
        n_tests = len(unique_reductions)
        
        # Sort errors and calculate BH thresholds
        sorted_indices = np.argsort(error_values)
        sorted_errors = error_values[sorted_indices]
        bh_thresholds = (np.arange(1, len(sorted_errors) + 1) / len(sorted_errors)) * target_error_pct
        
        # Find the largest error that satisfies BH condition
        valid_mask = sorted_errors <= bh_thresholds
        if np.any(valid_mask):
            max_valid_idx = np.where(valid_mask)[0][-1]
            effective_target = sorted_errors[max_valid_idx]
        else:
            effective_target = target_error_pct
        
        corrected_errors = error_values
    else:
        corrected_errors = error_values
        effective_target = target_error_pct
    
    # Perform bootstrapping to get confidence interval
    threshold_estimate, ci_lower, ci_upper = bootstrap_threshold(
        reduction_values, corrected_errors, 
        threshold_pct=effective_target,
        n_resamples=n_resamples
    )
    
    # Round to 2 decimal places as required by FR-006 and SC-004
    threshold_estimate = round(threshold_estimate, 2)
    ci_lower = round(ci_lower, 2)
    ci_upper = round(ci_upper, 2)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare results
    results = {
        "threshold_detection": {
            "max_context_reduction_pct": threshold_estimate,
            "target_error_pct": target_error_pct,
            "effective_target_error_pct": effective_target,
            "correction_method": correction_method,
            "confidence_interval_95": {
                "lower_bound": ci_lower,
                "upper_bound": ci_upper
            },
            "n_resamples": n_resamples,
            "n_observations": len(reduction_values),
            "unique_reduction_levels": len(np.unique(reduction_values))
        },
        "data_summary": {
            "min_reduction": float(np.min(reduction_values)),
            "max_reduction": float(np.max(reduction_values)),
            "mean_error": float(np.mean(corrected_errors)),
            "std_error": float(np.std(corrected_errors))
        }
    }
    
    # Save results to threshold_ci.json
    ci_output_path = os.path.join(output_dir, "threshold_ci.json")
    with open(ci_output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Threshold detection completed. Results saved to {ci_output_path}")
    print(f"Max context reduction: {threshold_estimate}%")
    print(f"95% CI: [{ci_lower}%, {ci_upper}%]")
    
    return results

def main():
    """Main entry point for threshold detection."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect threshold for safe context reduction")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/processed",
        help="Path to processed execution logs directory"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/results",
        help="Path to save results"
    )
    parser.add_argument(
        "--target-error",
        type=float,
        default=1.0,
        help="Target error percentage threshold (default: 1.0)"
    )
    parser.add_argument(
        "--n-resamples",
        type=int,
        default=1000,
        help="Number of bootstrap resamples (default: 1000)"
    )
    parser.add_argument(
        "--correction-method",
        type=str,
        choices=["bonferroni", "benjamini_hochberg", "none"],
        default="benjamini_hochberg",
        help="Multiple comparison correction method (default: benjamini_hochberg)"
    )
    
    args = parser.parse_args()
    
    detect_threshold_with_correction(
        logs_path=args.input_dir,
        output_dir=args.output_dir,
        target_error_pct=args.target_error,
        n_resamples=args.n_resamples,
        correction_method=args.correction_method
    )

if __name__ == "__main__":
    main()
