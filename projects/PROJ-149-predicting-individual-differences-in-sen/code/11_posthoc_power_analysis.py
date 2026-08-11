import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

# Import from utils.stats_helpers as per API surface
from utils.stats_helpers import calculate_sample_size_for_r2

# Import from config as per API surface
from config import get_path, ensure_dirs, get_seed

def load_model_results(results_path: str) -> Dict[str, Any]:
    """Load the model results JSON file."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def perform_power_analysis(
    results: Dict[str, Any],
    target_r2: float = 0.10,
    target_power: float = 0.80,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis to estimate required sample size.
    
    Uses the F-test for multiple regression (R-squared).
    Calculates the non-centrality parameter and required N for the target power.
    
    Args:
        results: Dictionary containing model results (R2, N, predictors).
        target_r2: Target R-squared value to detect (effect size).
        target_power: Desired statistical power (1 - beta).
        alpha: Significance level.
        
    Returns:
        Dictionary with power analysis results.
    """
    # Extract current model statistics
    # Handle both linear and lasso results if present
    r2_val = results.get('adjusted_r2', results.get('r2', 0.0))
    n_obs = results.get('n_samples', results.get('n', 0))
    n_predictors = results.get('n_predictors', results.get('n_features', 0))
    
    if n_obs == 0 or n_predictors == 0:
        # Fallback if not explicitly stored, try to infer from data if available
        # For now, return a failure state or estimate based on typical values
        # We assume the calling script ensures these are populated
        raise ValueError("Model results must contain n_samples and n_predictors")

    # Use the utility function from stats_helpers
    # calculate_sample_size_for_r2(f2, power, alpha, u)
    # f2 = R2 / (1 - R2)
    f2 = target_r2 / (1 - target_r2)
    u = n_predictors  # numerator degrees of freedom
    
    try:
        required_n = calculate_sample_size_for_r2(f2, target_power, alpha, u)
        achieved_power = None # Could calculate achieved power if needed
        
        # Calculate achieved power with current N if we want to be thorough
        # This requires inverting the calculation, which is complex without statsmodels
        # We'll stick to the required N for the target effect size.
        
    except Exception as e:
        # If the utility fails (e.g., numerical issues), handle gracefully
        return {
            "status": "error",
            "error": str(e),
            "target_r2": target_r2,
            "target_power": target_power,
            "current_n": n_obs,
            "current_r2": r2_val
        }

    return {
        "status": "success",
        "target_r2": target_r2,
        "target_power": target_power,
        "alpha": alpha,
        "n_predictors": n_predictors,
        "current_n": n_obs,
        "current_r2": r2_val,
        "required_n": int(np.ceil(required_n)),
        "effect_size_f2": f2,
        "notes": f"Required N calculated for R²={target_r2} with power={target_power} and {n_predictors} predictors."
    }

def save_results(results: Dict[str, Any], power_analysis: Dict[str, Any], output_path: str):
    """Append power analysis results to the model results JSON."""
    results['power_analysis'] = power_analysis
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Perform post-hoc power analysis for EEG-RT prediction model.")
    parser.add_argument(
        '--input', 
        type=str, 
        default=get_path('model_results_json'), 
        help='Path to input model_results.json'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default=get_path('model_results_json'), 
        help='Path to output model_results.json (overwrites input)'
    )
    parser.add_argument(
        '--target-r2',
        type=float,
        default=0.10,
        help='Target R-squared value for power analysis (default: 0.10)'
    )
    parser.add_argument(
        '--target-power',
        type=float,
        default=0.80,
        help='Target statistical power (default: 0.80)'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance level (default: 0.05)'
    )
    
    args = parser.parse_args()
    
    # Set seed for reproducibility if needed in any stochastic parts
    set_global_seed()
    
    print(f"Loading model results from: {args.input}")
    try:
        model_results = load_model_results(args.input)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print(f"Performing power analysis for R²={args.target_r2}, Power={args.target_power}...")
    power_results = perform_power_analysis(
        model_results,
        target_r2=args.target_r2,
        target_power=args.target_power,
        alpha=args.alpha
    )
    
    print(f"Saving updated results to: {args.output}")
    save_results(model_results, power_results, args.output)
    
    if power_results['status'] == 'success':
        print(f"Required sample size: {power_results['required_n']}")
        print(f"Current sample size: {power_results['current_n']}")
        if power_results['current_n'] < power_results['required_n']:
            print(f"Warning: Current N ({power_results['current_n']}) is less than required ({power_results['required_n']}).")
        else:
            print(f"Success: Current N ({power_results['current_n']}) meets the requirement.")
    else:
        print(f"Power analysis failed: {power_results.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
