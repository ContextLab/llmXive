"""
code/08b_fit_nonlinear_model.py

Implements Task T024b: Fit Linear and Polynomial Models for Non-linear Analysis.

Loads polynomial features prepared by code/08a_prepare_polynomial_features.py,
fits a standard Linear Regression model and a Polynomial Regression model (degree 2),
compares their performance (R²), and saves the results to data/interim/nonlinear_model_results.json.

Dependencies:
    - T024a (code/08a_prepare_polynomial_features.py) producing data/interim/poly_features.csv
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score

# Import shared config utilities if available, otherwise define minimal fallback
# The project uses code/config.py for paths.
try:
    from config import get_path, ensure_dirs
except ImportError:
    # Fallback for direct execution without config module context if needed
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    def get_path(*parts):
        return PROJECT_ROOT / Path(*parts)
    def ensure_dirs(p):
        Path(p).mkdir(parents=True, exist_ok=True)
        return p


def load_poly_features(input_path: str) -> pd.DataFrame:
    """
    Load the polynomial features dataset.

    Args:
        input_path: Path to the CSV file containing polynomial features.

    Returns:
        DataFrame with features and target.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Please ensure T024a (code/08a_prepare_polynomial_features.py) has run successfully.")

    df = pd.read_csv(input_path)

    # Expected columns based on T024a:
    # The target is 'median_rt'. Features include original bands + polynomial terms.
    # We need to identify feature columns. Assuming the CSV has 'median_rt' and other numeric cols.
    if 'median_rt' not in df.columns:
        raise ValueError("Input file must contain 'median_rt' column.")

    feature_cols = [col for col in df.columns if col != 'median_rt']
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in input file besides 'median_rt'.")

    return df, feature_cols


def fit_models(df: pd.DataFrame, feature_cols: list, target_col: str = 'median_rt') -> dict:
    """
    Fit Linear and Polynomial models and compute metrics.

    Args:
        df: DataFrame with features and target.
        feature_cols: List of column names to use as features.
        target_col: Name of the target column.

    Returns:
        Dictionary containing model coefficients, R² scores, and metadata.
    """
    X = df[feature_cols].values
    y = df[target_col].values

    # Handle missing values if any (drop or impute) - strictly drop for simplicity here
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X_clean = X[mask]
    y_clean = y[mask]

    if len(X_clean) < 2:
        raise ValueError("Not enough valid samples to fit models after removing NaNs.")

    results = {
        "n_samples": len(y_clean),
        "feature_columns": feature_cols,
        "linear_model": {},
        "polynomial_model": {}
    }

    # 1. Fit Linear Model
    lin_model = LinearRegression()
    lin_model.fit(X_clean, y_clean)
    y_pred_lin = lin_model.predict(X_clean)
    r2_lin = r2_score(y_clean, y_pred_lin)

    results["linear_model"] = {
        "r2": float(r2_lin),
        "coefficients": dict(zip(feature_cols, [float(c) for c in lin_model.coef_])),
        "intercept": float(lin_model.intercept_),
        "description": "Standard Linear Regression on polynomial-expanded features."
    }

    # 2. Fit Polynomial Model (Degree 2)
    # Note: The features in df are ALREADY polynomially expanded by T024a.
    # However, to strictly follow the task "Fit a polynomial model", we treat the input as base features
    # and apply PolynomialFeatures again, OR we interpret "Polynomial Model" as using the expanded features
    # directly in a Linear Regression (which is mathematically equivalent to fitting a polynomial surface).
    # Given T024a created 'poly_features.csv', the standard approach is:
    #   - The features in the CSV are X_poly.
    #   - We fit a Linear Regression on X_poly. This IS the polynomial model fit.
    #   - The "Linear Model" comparison usually implies fitting on ORIGINAL features (before expansion).
    #
    # BUT, the task description says: "Fit a linear model and a polynomial model on poly_features.csv".
    # This implies both models run on the SAME input data (the expanded features).
    # If we run LinearRegression on expanded features, that is the Polynomial Model.
    # What is the "Linear Model" in this context?
    # Interpretation A: Fit LinearRegression on ONLY the original base features (alpha, beta, etc.) found in the CSV.
    # Interpretation B: The task implies comparing the fit of the expanded model vs a baseline.
    #
    # Let's follow the most robust scientific interpretation:
    #   - "Linear Model": Fit on the original non-polynomial columns (e.g., 'alpha', 'beta', 'gamma', 'median_rt' is target).
    #   - "Polynomial Model": Fit on ALL columns (including squared/interaction terms) in the CSV.
    #
    # We need to identify which columns are original vs polynomial.
    # T024a likely added suffixes or specific names. Let's assume columns starting with 'poly_' or containing '^' are polynomial.
    # If we can't distinguish, we assume the CSV contains ONLY the expanded features + target,
    # and we cannot fit a "Linear Model" on the original data without reloading the original.
    #
    # Re-reading T024a: "add polynomial terms... Output: poly_features.csv".
    # Usually, this means the file contains [Original, Polynomial, Target].
    # Let's try to separate them.
    # If separation fails, we will fit a Linear Model on the first N columns (assuming they are base)
    # and a Polynomial Model on all columns.
    #
    # Alternative: The task might mean "Fit a model assuming linear relationship" (LinearRegression)
    # vs "Fit a model assuming non-linear" (PolynomialFeatures + LinearRegression).
    # But since the input is already expanded, the "Polynomial Model" is just LinearRegression on the expanded set.
    # The "Linear Model" must be LinearRegression on the subset of original features.
    #
    # Heuristic: Columns that are NOT 'median_rt' and DO NOT contain '^' or 'poly_' might be original?
    # Or, we assume the first K columns are original.
    #
    # Let's implement a robust check:
    #   - Identify columns that look like interactions (contain '^' or '_x_' or '_sq').
    #   - If we find them, use the rest as "linear_base".
    #   - If we don't find them, we might have to skip the "Linear Model" comparison or assume all are polynomial.
    #
    # For this implementation, we will assume the CSV contains the original features (e.g., 'alpha', 'beta')
    # and the polynomial terms (e.g., 'alpha^2', 'alpha*beta').
    # We will fit:
    #   1. Linear Model: On columns that do NOT look like polynomial terms.
    #   2. Polynomial Model: On ALL feature columns.

    base_cols = []
    poly_cols = []

    # Heuristic for identifying polynomial columns
    poly_indicators = ['^', 'poly_', '_sq', '_x_', '_sq_']

    for col in feature_cols:
        is_poly = any(ind in col for ind in poly_indicators)
        if is_poly:
            poly_cols.append(col)
        else:
            base_cols.append(col)

    if len(base_cols) == 0:
        # Fallback: If we can't distinguish, assume the first half are base? No, that's risky.
        # If no polynomial terms detected, the "Polynomial Model" is the same as "Linear Model" on full set.
        # We will report the same result for both but note the limitation.
        base_cols = feature_cols
        poly_cols = feature_cols
        print("Warning: No polynomial columns detected in input. Using all features for both models.")

    # Fit Linear Model on base features
    if len(base_cols) > 0:
        X_base = X_clean[:, [feature_cols.index(c) for c in base_cols]]
        lin_base_model = LinearRegression()
        lin_base_model.fit(X_base, y_clean)
        y_pred_base = lin_base_model.predict(X_base)
        r2_base = r2_score(y_clean, y_pred_base)

        results["linear_model"] = {
            "r2": float(r2_base),
            "coefficients": dict(zip(base_cols, [float(c) for c in lin_base_model.coef_])),
            "intercept": float(lin_base_model.intercept_),
            "feature_count": len(base_cols),
            "description": f"Linear Regression on {len(base_cols)} base features."
        }

    # Fit Polynomial Model on all features (including interactions)
    X_poly = X_clean
    poly_model = LinearRegression() # LinearRegression on expanded features IS the polynomial fit
    poly_model.fit(X_poly, y_clean)
    y_pred_poly = poly_model.predict(X_poly)
    r2_poly = r2_score(y_clean, y_pred_poly)

    # Get coefficients for all features
    full_coef = dict(zip(feature_cols, [float(c) for c in poly_model.coef_]))

    results["polynomial_model"] = {
        "r2": float(r2_poly),
        "coefficients": full_coef,
        "intercept": float(poly_model.intercept_),
        "feature_count": len(feature_cols),
        "description": "Linear Regression on full polynomial-expanded features (Degree 2)."
    }

    return results


def save_results(results: dict, output_path: str):
    """
    Save the model results to a JSON file.

    Args:
        results: Dictionary of results.
        output_path: Path to the output JSON file.
    """
    ensure_dirs(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Fit Linear and Polynomial models for non-linear analysis.")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to the polynomial features CSV (default: data/interim/poly_features.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to the output JSON file (default: data/interim/nonlinear_model_results.json)"
    )
    args = parser.parse_args()

    # Set default paths
    input_path = args.input if args.input else str(get_path("interim", "poly_features.csv"))
    output_path = args.output if args.output else str(get_path("interim", "nonlinear_model_results.json"))

    print(f"Loading polynomial features from {input_path}...")
    try:
        df, feature_cols = load_poly_features(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Found {len(feature_cols)} features. Fitting models...")
    try:
        results = fit_models(df, feature_cols)
    except Exception as e:
        print(f"Error during model fitting: {e}")
        sys.exit(1)

    print(f"Saving results to {output_path}...")
    try:
        save_results(results, output_path)
    except Exception as e:
        print(f"Error saving results: {e}")
        sys.exit(1)

    print("Task T024b completed successfully.")


if __name__ == "__main__":
    main()