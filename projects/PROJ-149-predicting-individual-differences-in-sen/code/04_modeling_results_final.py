"""
T019: Calculate and log Adjusted R² and optimal lambda to model_results.json.
This script reads the results from the LASSO modeling (T018), calculates Adjusted R²,
identifies the optimal lambda, and updates the model_results.json file.
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, ensure_dirs, get_cv_folds


def load_json_safe(path: str) -> dict:
    """Load a JSON file safely, raising an error if it doesn't exist."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)


def calculate_adjusted_r2(r2: float, n_samples: int, n_features: int) -> float:
    """
    Calculate Adjusted R².

    Formula: 1 - (1 - R²) * (n - 1) / (n - p - 1)
    Where:
      n = number of samples
      p = number of predictors (features)

    Args:
        r2: The R² value from the model.
        n_samples: Number of samples in the training set.
        n_features: Number of features used in the model.

    Returns:
        Adjusted R² value.
    """
    if n_samples <= n_features + 1:
        # Prevent division by zero or negative denominator
        return 0.0

    adjusted_r2 = 1 - (1 - r2) * (n_samples - 1) / (n_samples - n_features - 1)
    return adjusted_r2


def main():
    parser = argparse.ArgumentParser(description="Calculate Adjusted R² and update model results.")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input model_results.json. Defaults to config path."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output model_results.json. Defaults to config path."
    )
    args = parser.parse_args()

    # Determine paths
    if args.input:
        input_path = args.input
    else:
        # Try to get from config, fallback to standard path
        try:
            input_path = get_path("model_results")
        except ValueError:
            input_path = "data/processed/model_results.json"

    if args.output:
        output_path = args.output
    else:
        try:
            output_path = get_path("model_results")
        except ValueError:
            output_path = "data/processed/model_results.json"

    print(f"Loading model results from: {input_path}")

    try:
        results = load_json_safe(input_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {input_path}: {e}")
        sys.exit(1)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        ensure_dirs(output_dir)

    # Process results
    # The results structure is expected to be a dictionary containing model metrics.
    # We expect keys like 'linear_regression' and 'lasso_regression'.
    # We will calculate Adjusted R2 for both if present.

    updated_results = results.copy()

    # Process Linear Regression if present
    if 'linear_regression' in updated_results:
        lr_data = updated_results['linear_regression']
        if isinstance(lr_data, dict) and 'r2' in lr_data:
            # Estimate n_samples and n_features from available data
            # If we have feature coefficients, count them.
            # If we have a 'n_features' key, use that. Otherwise, estimate from coefficients.
            n_features = len(lr_data.get('coefficients', []))
            if n_features == 0:
                n_features = lr_data.get('n_features', 0)

            # We need n_samples. If not stored, we might need to load features to count.
            # For now, we assume n_samples is stored or we use a placeholder if missing.
            # A robust implementation would load the features.csv to count rows.
            # Let's try to load features to get exact N.
            try:
                features_path = get_path("processed", "features.csv")
                df_features = pd.read_csv(features_path)
                n_samples = len(df_features)
            except Exception:
                # Fallback: use stored value or 0
                n_samples = lr_data.get('n_samples', 0)

            if n_samples > 0 and n_features > 0:
                r2 = lr_data['r2']
                adj_r2 = calculate_adjusted_r2(r2, n_samples, n_features)
                lr_data['adjusted_r2'] = adj_r2
                print(f"Linear Regression: R²={r2:.4f}, Adjusted R²={adj_r2:.4f} (n={n_samples}, p={n_features})")
            else:
                print("WARNING: Could not calculate Adjusted R² for Linear Regression (missing n_samples or n_features).")
                lr_data['adjusted_r2'] = None

    # Process LASSO Regression if present
    if 'lasso_regression' in updated_results:
        lasso_data = updated_results['lasso_regression']
        if isinstance(lasso_data, dict) and 'r2' in lasso_data:
            # Extract optimal lambda
            # The LASSO results should contain 'best_lambda' or similar.
            optimal_lambda = lasso_data.get('best_lambda', lasso_data.get('optimal_lambda', None))
            if optimal_lambda is not None:
                lasso_data['optimal_lambda'] = optimal_lambda
                print(f"LASSO: Optimal Lambda = {optimal_lambda}")

            # Calculate Adjusted R²
            n_features = len(lasso_data.get('coefficients', []))
            if n_features == 0:
                n_features = lasso_data.get('n_features', 0)

            try:
                features_path = get_path("processed", "features.csv")
                df_features = pd.read_csv(features_path)
                n_samples = len(df_features)
            except Exception:
                n_samples = lasso_data.get('n_samples', 0)

            if n_samples > 0 and n_features > 0:
                r2 = lasso_data['r2']
                adj_r2 = calculate_adjusted_r2(r2, n_samples, n_features)
                lasso_data['adjusted_r2'] = adj_r2
                print(f"LASSO: R²={r2:.4f}, Adjusted R²={adj_r2:.4f} (n={n_samples}, p={n_features})")
            else:
                print("WARNING: Could not calculate Adjusted R² for LASSO (missing n_samples or n_features).")
                lasso_data['adjusted_r2'] = None

    # Save updated results
    print(f"Saving updated results to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(updated_results, f, indent=2)

    print("Task T019 completed successfully.")


if __name__ == "__main__":
    main()