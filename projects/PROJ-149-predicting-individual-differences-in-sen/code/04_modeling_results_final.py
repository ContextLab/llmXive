"""
T019: Calculate and log Adjusted R² and optimal lambda to data/processed/model_results.json.

This script loads the results from the Linear Regression (T017) and LASSO (T018) models,
calculates the Adjusted R² for the Linear Regression model, extracts the optimal lambda
from the LASSO model, and merges these metrics into the final model_results.json file.

Dependencies:
- T017: code/04_modeling.py (produces data/processed/model_results.json with basic R²)
- T018: code/04_modeling_lasso.py (produces data/interim/lasso_results.json or similar)
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Import config utilities
sys.path.insert(0, str(Path(__file__).parent))
from config import get_path, ensure_dirs, load_config

def load_json_safe(path: Path) -> Dict[str, Any]:
    """Load a JSON file safely."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def calculate_adjusted_r2(r2: float, n_samples: int, n_features: int) -> float:
    """
    Calculate Adjusted R².
    Formula: 1 - (1 - R²) * (n - 1) / (n - p - 1)
    where n is sample size, p is number of predictors.
    """
    if n_samples <= n_features + 1:
        return np.nan
    return 1 - (1 - r2) * (n_samples - 1) / (n_samples - n_features - 1)

def main():
    parser = argparse.ArgumentParser(description="Finalize model results with Adjusted R² and optimal Lambda.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    
    # Define paths
    results_path = get_path("model_results")
    lasso_results_path = get_path("lasso_results") # Assuming T018 writes here, or we read from the main file if updated in place
    
    # Ensure output directory exists
    ensure_dirs(results_path)

    # Load existing results from T017 (Linear Regression)
    # We expect T017 to have written a file with basic R², RMSE, etc.
    # If T018 updated the same file, we load that. If T018 wrote a separate file, we merge.
    # Based on T018 description, it likely writes to model_results.json or a separate interim file.
    # We assume T018 might have updated model_results.json or we need to load a specific lasso output.
    # Let's try to load the main model_results.json first.
    
    try:
        results = load_json_safe(results_path)
    except FileNotFoundError:
        # If main file doesn't exist, T017 might have failed or not run.
        # We cannot proceed without the base results.
        print(f"Error: {results_path} not found. Ensure T017 has completed successfully.")
        sys.exit(1)

    # Check if LASSO results are in a separate file (common pattern) or merged
    # If T018 wrote to a separate file, load it.
    lasso_data = None
    if lasso_results_path.exists():
        lasso_data = load_json_safe(lasso_results_path)
    else:
        # Fallback: Check if 'lasso' key exists in main results (if T018 updated in place)
        if 'lasso' in results:
            lasso_data = results['lasso']
        else:
            # If neither, we assume T018 might not have run or wrote to a different default.
            # Let's assume T018 writes to data/interim/lasso_results.json if not specified otherwise.
            alt_lasso_path = get_path("interim") / "lasso_results.json"
            if alt_lasso_path.exists():
                lasso_data = load_json_safe(alt_lasso_path)
            else:
                print("Warning: LASSO results not found. Proceeding with Linear Regression only.")
                lasso_data = None

    # Process Linear Regression results
    if 'linear_regression' in results:
        lr_results = results['linear_regression']
        r2 = lr_results.get('r2', 0.0)
        n_samples = lr_results.get('n_samples', 0)
        n_features = lr_results.get('n_features', 0)
        
        adj_r2 = calculate_adjusted_r2(r2, n_samples, n_features)
        lr_results['adjusted_r2'] = adj_r2
        print(f"Linear Regression: R²={r2:.4f}, Adjusted R²={adj_r2:.4f} (n={n_samples}, p={n_features})")
    
    # Process LASSO results
    optimal_lambda = None
    if lasso_data:
        if isinstance(lasso_data, dict):
            # If it's a dict with a 'best_params' or similar structure
            best_params = lasso_data.get('best_params', {})
            optimal_lambda = best_params.get('alpha') # sklearn uses 'alpha' for lambda
            if optimal_lambda is None:
                optimal_lambda = lasso_data.get('optimal_lambda')
                if optimal_lambda is None:
                    optimal_lambda = lasso_data.get('lambda_')
            
            # Ensure LASSO has adjusted R² too if it has R²
            if 'r2' in lasso_data:
                n_samples = lasso_data.get('n_samples', 0)
                # LASSO effective degrees of freedom is tricky, but we can use number of non-zero coeffs
                n_nonzero = lasso_data.get('n_nonzero', 0)
                if n_nonzero > 0:
                    adj_r2 = calculate_adjusted_r2(lasso_data['r2'], n_samples, n_nonzero)
                    lasso_data['adjusted_r2'] = adj_r2
            
            # Update the main results dict if it's a nested structure
            if 'lasso' not in results:
                results['lasso'] = lasso_data
            else:
                results['lasso'].update(lasso_data)
        elif isinstance(lasso_data, list):
            # If it's a list of folds, find the best one
            best_fold = max(lasso_data, key=lambda x: x.get('r2', 0))
            optimal_lambda = best_fold.get('alpha')
            results['lasso'] = best_fold

    # Save updated results
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Updated model results saved to {results_path}")
    print(f"Optimal LASSO Lambda: {optimal_lambda}")

if __name__ == "__main__":
    main()
