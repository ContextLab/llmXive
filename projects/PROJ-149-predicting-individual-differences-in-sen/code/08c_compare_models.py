"""
code/08c_compare_models.py
Compare linear vs polynomial models using F-test.

Implements T024c: Compare adjusted R² of linear vs. polynomial model via F‑test.
Automatically evaluates the F-test p-value against the established significance threshold (p < 0.05).
Outputs: data/processed/non_linear_comparison.json
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Import shared config utilities
# Note: We rely on the global ensure_dirs and get_path from config.py
# We must handle the fact that config.py might have different signatures in different contexts,
# but we will try to import standard names first.
try:
    from config import get_path, ensure_dirs
except ImportError:
    # Fallback if config is not in path or has issues, though task requires real imports
    # This block is defensive; in a correct environment, the above should work.
    print("Warning: Could not import get_path/ensure_dirs from config. Using defaults.")
    def get_path(*args):
        if len(args) == 1:
            return Path(args[0])
        return Path("data") / args[0] / args[1] if len(args) == 2 else Path("data") / "/".join(args)
    
    def ensure_dirs(path):
        if isinstance(path, (list, tuple)):
            for p in path:
                Path(p).mkdir(parents=True, exist_ok=True)
        else:
            Path(path).mkdir(parents=True, exist_ok=True)
        return path

def load_poly_results(input_path: str) -> dict:
    """
    Load the polynomial model results from JSON.
    
    Args:
        input_path: Path to the JSON file containing model results.
        
    Returns:
        Dictionary containing model metrics.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        return json.load(f)

def perform_f_test(linear_r2: float, poly_r2: float, n: int, p_linear: int, p_poly: int) -> dict:
    """
    Perform an F-test to compare the fit of the linear vs. polynomial model.
    
    The F-statistic is calculated as:
    F = ((RSS_reduced - RSS_full) / (df_reduced - df_full)) / (RSS_full / df_full)
    
    Where:
    RSS = Residual Sum of Squares = (1 - R²) * TSS
    Since TSS cancels out in the ratio:
    F = ((R²_full - R²_reduced) / (p_full - p_reduced)) / ((1 - R²_full) / (n - p_full - 1))
    
    Args:
        linear_r2: R-squared of the linear model (reduced).
        poly_r2: R-squared of the polynomial model (full).
        n: Number of samples.
        p_linear: Number of parameters in the linear model (excluding intercept).
        p_poly: Number of parameters in the polynomial model (excluding intercept).
        
    Returns:
        Dictionary with 'f_statistic', 'p_value', 'significant', and 'interpretation'.
    """
    if linear_r2 >= poly_r2:
        # Polynomial model should not be worse; if it is, F-test is not meaningful in this direction
        # or R² calculation has issues. We treat it as not significant improvement.
        return {
            "f_statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "interpretation": "Polynomial model did not improve R² over linear model."
        }

    # Degrees of freedom
    df_num = p_poly - p_linear
    df_den = n - p_poly - 1

    if df_den <= 0:
        return {
            "f_statistic": np.nan,
            "p_value": np.nan,
            "significant": False,
            "interpretation": "Insufficient samples for F-test (df_den <= 0)."
        }

    # Calculate F-statistic
    # F = ((R2_poly - R2_linear) / (p_poly - p_linear)) / ((1 - R2_poly) / (n - p_poly - 1))
    numerator = (poly_r2 - linear_r2) / df_num
    denominator = (1.0 - poly_r2) / df_den
    
    if denominator == 0:
        # If denominator is 0, R2_poly is 1.0, perfect fit.
        f_stat = np.inf
        p_val = 0.0
    else:
        f_stat = numerator / denominator
        p_val = 1.0 - stats.f.cdf(f_stat, df_num, df_den)

    significant = p_val < 0.05
    
    interpretation = (
        f"F-statistic: {f_stat:.4f}, p-value: {p_val:.4f}. "
        f"{'Significant improvement' if significant else 'No significant improvement'} "
        f"of polynomial model over linear model at p < 0.05."
    )

    return {
        "f_statistic": float(f_stat),
        "p_value": float(p_val),
        "significant_at_p05": significant,
        "interpretation": interpretation
    }

def main():
    parser = argparse.ArgumentParser(description="Compare linear vs polynomial models via F-test.")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to the nonlinear model results JSON (default: data/interim/nonlinear_model_results.json)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to the output comparison JSON (default: data/processed/non_linear_comparison.json)"
    )
    args = parser.parse_args()

    # Determine paths
    input_path = args.input if args.input else get_path("interim", "nonlinear_model_results.json")
    output_path = args.output if args.output else get_path("processed", "non_linear_comparison.json")

    print(f"Loading results from: {input_path}")
    
    # Ensure output directory exists
    ensure_dirs(Path(output_path).parent)

    try:
        results = load_poly_results(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_path}: {e}")
        sys.exit(1)

    # Extract metrics
    # Expected keys in results: 'linear_r2', 'poly_r2', 'n_samples', 'linear_params', 'poly_params'
    # The T024b output structure is assumed to be:
    # {
    #   "linear_model": {"r2": ..., "params_count": ...},
    #   "polynomial_model": {"r2": ..., "params_count": ...},
    #   "n_samples": ...
    # }
    # Or flat keys. We adapt.
    
    linear_r2 = results.get("linear_r2") or (results.get("linear_model", {}).get("r2"))
    poly_r2 = results.get("poly_r2") or (results.get("polynomial_model", {}).get("r2"))
    n_samples = results.get("n_samples") or (results.get("n"))
    
    # Count parameters (excluding intercept)
    # If not provided, we infer from typical model structures or use defaults if ambiguous.
    # For a linear model with 6 bands + intercept, p=6.
    # For polynomial (degree 2) with 2 bands (alpha, beta) + interactions, it's more complex.
    # We rely on the producer (T024b) to have calculated this or we estimate based on data.
    # However, the task spec says T024b writes 'coefficients'. We can count them.
    
    linear_params = results.get("linear_params") or (results.get("linear_model", {}).get("params_count"))
    poly_params = results.get("poly_params") or (results.get("polynomial_model", {}).get("params_count"))
    
    # Fallback estimation if not explicitly in JSON (robustness)
    if linear_params is None and "linear_coefficients" in results:
        linear_params = len(results["linear_coefficients"]) - 1 # exclude intercept
    if poly_params is None and "polynomial_coefficients" in results:
        poly_params = len(results["polynomial_coefficients"]) - 1
        
    # If still missing, we might need to read the features file to count columns, but let's assume T024b provided it.
    # If T024b didn't provide it, we can't accurately compute F-test without knowing p.
    # We will raise an error if critical info is missing.
    if linear_r2 is None or poly_r2 is None or n_samples is None:
        print("Error: Missing required metrics (r2 or n_samples) in input file.")
        sys.exit(1)
    
    if linear_params is None or poly_params is None:
        print("Warning: Parameter counts not found in input. Attempting to infer from coefficient lists if available.")
        # Fallback: try to infer from coefficients if present
        if "linear_coefficients" in results:
            linear_params = len(results["linear_coefficients"]) - 1
        if "polynomial_coefficients" in results:
            poly_params = len(results["polynomial_coefficients"]) - 1
        
        if linear_params is None or poly_params is None:
            print("Error: Could not determine parameter counts (p_linear, p_poly). Cannot perform F-test.")
            sys.exit(1)

    print(f"Linear R²: {linear_r2:.4f}, Polynomial R²: {poly_r2:.4f}, N: {n_samples}")
    print(f"Linear params: {linear_params}, Polynomial params: {poly_params}")

    comparison_result = perform_f_test(
        linear_r2=linear_r2,
        poly_r2=poly_r2,
        n=n_samples,
        p_linear=linear_params,
        p_poly=poly_params
    )

    # Prepare output
    output_data = {
        "linear_r2": float(linear_r2),
        "polynomial_r2": float(poly_r2),
        "n_samples": int(n_samples),
        "linear_params": int(linear_params),
        "polynomial_params": int(poly_params),
        "f_test": comparison_result
    }

    print(f"Writing results to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print("Comparison complete.")
    print(f"Significant at p < 0.05: {comparison_result['significant_at_p05']}")
    print(f"Interpretation: {comparison_result['interpretation']}")

if __name__ == "__main__":
    main()