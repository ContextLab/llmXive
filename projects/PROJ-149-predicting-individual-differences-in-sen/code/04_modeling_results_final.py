"""
T019: Calculate Adjusted R² and Optimal Lambda, update model_results.json.

This script loads the results from the modeling phase (T017/T018), calculates
the Adjusted R² metric to account for the number of predictors, identifies the
optimal lambda value from LASSO tuning, and appends these to the existing
model_results.json file.
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Import from local config
from config import get_path, ensure_dirs


def load_json_safe(path: str) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None if it doesn't exist or is invalid."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: File not found: {path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}")
        return None


def calculate_adjusted_r2(r2: float, n_samples: int, n_features: int) -> float:
    """
    Calculate Adjusted R².

    Formula: 1 - (1 - R²) * (n - 1) / (n - p - 1)
    where n is sample count and p is number of predictors.

    Args:
        r2: The raw R² score.
        n_samples: Number of samples used in the model.
        n_features: Number of features (predictors) used in the model.

    Returns:
        The Adjusted R² value.
    """
    if n_samples <= n_features + 1:
        # Avoid division by zero or negative denominator
        return 0.0

    adj_r2 = 1 - (1 - r2) * (n_samples - 1) / (n_samples - n_features - 1)
    return float(adj_r2)


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save the results dictionary to a JSON file."""
    ensure_dirs(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Calculate Adjusted R² and Optimal Lambda for T019.")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to input model_results.json. Defaults to config path.")
    parser.add_argument("--output", type=str, default=None,
                        help="Path to output model_results.json. Defaults to config path.")
    args = parser.parse_args()

    # Determine paths
    if args.input:
        input_path = args.input
    else:
        input_path = get_path("data/processed/model_results.json")

    if args.output:
        output_path = args.output
    else:
        output_path = get_path("data/processed/model_results.json")

    print(f"Loading model results from: {input_path}")
    results = load_json_safe(input_path)

    if results is None:
        # If file doesn't exist or is empty, create a base structure
        print("Input file missing or invalid. Creating new results structure.")
        results = {
            "model_type": "Linear/LASSO",
            "metrics": {},
            "hyperparameters": {},
            "validation": {}
        }

    # Ensure metrics and hyperparameters sections exist
    if "metrics" not in results:
        results["metrics"] = {}
    if "hyperparameters" not in results:
        results["hyperparameters"] = {}
    if "validation" not in results:
        results["validation"] = {}

    # Extract necessary values
    # We assume the 'metrics' section contains 'r2' from cross-validation
    # and 'n_samples' and 'n_features' might be present or need to be inferred.
    # If not present, we attempt to infer from the data if available, or use placeholders.

    r2 = results["metrics"].get("r2")
    n_samples = results["metrics"].get("n_samples")
    n_features = results["metrics"].get("n_features")

    # If n_samples or n_features are missing, we might need to load the data to count them
    # or assume they were set during the modeling phase (T017/T018).
    # For robustness, if missing, we try to load the features file to count rows/cols.
    if r2 is not None and (n_samples is None or n_features is None):
        features_path = get_path("data/processed/features_clr.csv")
        if os.path.exists(features_path):
            df = pd.read_csv(features_path)
            if n_samples is None:
                n_samples = len(df)
            if n_features is None:
                # Exclude non-feature columns like 'participant_id' or 'median_rt'
                # Assuming the last column is the target 'median_rt' and first is ID
                # A safer approach is to check the modeling script's feature list.
                # For now, we assume all numeric columns except target are features.
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                # Remove 'median_rt' if present
                if 'median_rt' in numeric_cols:
                    numeric_cols.remove('median_rt')
                n_features = len(numeric_cols)
                print(f"Inferred n_features: {n_features} from features file.")
        else:
            print("Warning: Could not infer n_samples/n_features. Using defaults (0).")
            n_samples = 0
            n_features = 0

    # Calculate Adjusted R²
    if r2 is not None and n_samples and n_features:
        adj_r2 = calculate_adjusted_r2(r2, n_samples, n_features)
        results["metrics"]["adjusted_r2"] = adj_r2
        print(f"Calculated Adjusted R²: {adj_r2:.4f} (R²={r2:.4f}, n={n_samples}, p={n_features})")
    else:
        print("Warning: Could not calculate Adjusted R². Missing r2, n_samples, or n_features.")
        results["metrics"]["adjusted_r2"] = None

    # Identify Optimal Lambda
    # The modeling script (T018) should have stored the optimal lambda in hyperparameters
    optimal_lambda = results["hyperparameters"].get("optimal_lambda")
    
    # If not present, but we have LassoCV results stored, we might need to extract it.
    # Assuming T018 stored it. If not, we check if 'lasso_lambda' exists.
    if optimal_lambda is None:
        optimal_lambda = results["hyperparameters"].get("lasso_lambda")
    
    if optimal_lambda is not None:
        results["hyperparameters"]["optimal_lambda"] = optimal_lambda
        print(f"Optimal Lambda identified: {optimal_lambda}")
    else:
        print("Warning: Optimal lambda not found in hyperparameters.")
        results["hyperparameters"]["optimal_lambda"] = None

    # Save updated results
    save_results(results, output_path)
    print("T019 completed successfully.")


if __name__ == "__main__":
    main()