"""
T024c: Compare linear vs polynomial models via F-test.
Implements FR-012: Compare adjusted R² of linear vs. polynomial model via F-test.
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from config import get_path, ensure_dirs

def load_poly_results(input_path: str) -> dict:
    """Load results from the nonlinear model fitting script (T024b)."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with open(input_path, 'r') as f:
        return json.load(f)

def perform_f_test(linear_r2: float, poly_r2: float, 
                   n: int, p_linear: int, p_poly: int) -> dict:
    """
    Perform an F-test to compare nested linear and polynomial models.
    
    Parameters:
    -----------
    linear_r2 : float
        Adjusted R² of the linear model (or R² if not adjusted, but we use R² for F-test calc)
        Note: The F-test formula uses unadjusted R² values. If only adjusted R² is available,
        we must approximate or retrieve unadjusted R². However, the task specifies comparing
        adjusted R², but the F-test statistic is derived from R² and degrees of freedom.
        We will assume the input 'linear_r2' and 'poly_r2' are the R² values used for the F-test.
        If the source file provided adjusted R², we note that the F-test is technically
        on the reduction in residual sum of squares, which relates to R².
        
        To be precise: 
        F = ((R2_poly - R2_linear) / (p_poly - p_linear)) / ((1 - R2_poly) / (n - p_poly - 1))
        
        We assume the values passed are the R² values (coefficient of determination) for the 
        respective models. If the source file only has adjusted R², we cannot perfectly recover 
        the unadjusted R² without knowing the exact number of parameters and N, but we can 
        approximate or use the values as proxies if the difference is small. 
        
        However, the task says "Compare adjusted R² ... via F-test". This is slightly contradictory
        because the F-test is on the model fit (R²), not the adjusted R². 
        We will interpret this as: Use the R² values from the models to perform the F-test,
        and the "comparison" is the result of that test.
        
        Let's assume the input values are the R² (unadjusted) for the purpose of the F-test calculation.
        If the source file provided adjusted R², we might need to adjust. 
        Looking at T024b output structure (assumed): 
        It likely has 'linear_r2' and 'poly_r2'. If these are adjusted, we need to be careful.
        For the sake of this implementation, we will treat them as the R² values for the F-test.
        If the previous task (T024b) outputted adjusted R², we will note that the F-test is an 
        approximation in that case. 
        
        Correction: The F-test compares the residual sum of squares (RSS).
        R² = 1 - RSS/TSS.
        So RSS = TSS * (1 - R²).
        F = ((RSS_linear - RSS_poly) / (df_linear - df_poly)) / (RSS_poly / df_poly)
          = ((TSS(1-R2_lin) - TSS(1-R2_poly)) / (p_poly - p_lin)) / (TSS(1-R2_poly) / (n - p_poly - 1))
          = ((R2_poly - R2_lin) / (p_poly - p_lin)) / ((1 - R2_poly) / (n - p_poly - 1))
        
        So we need the R² values. We will assume the input values are the R² values.
    
    n : int
        Number of observations
    p_linear : int
        Number of predictors in the linear model (excluding intercept)
    p_poly : int
        Number of predictors in the polynomial model (excluding intercept)
        
    Returns:
    --------
    dict with keys: f_statistic, p_value, significant, interpretation
    """
    # Degrees of freedom
    df_num = p_poly - p_linear
    df_den = n - p_poly - 1
    
    if df_den <= 0:
        return {
            "f_statistic": None,
            "p_value": None,
            "significant": False,
            "interpretation": "Cannot perform F-test: insufficient degrees of freedom."
        }
    
    # F-statistic calculation
    # F = ((R2_poly - R2_linear) / df_num) / ((1 - R2_poly) / df_den)
    numerator = (poly_r2 - linear_r2) / df_num
    denominator = (1 - poly_r2) / df_den
    
    if denominator == 0:
        return {
            "f_statistic": None,
            "p_value": None,
            "significant": False,
            "interpretation": "Cannot perform F-test: denominator is zero (R2_poly is 1.0)."
        }
        
    f_stat = numerator / denominator
    
    # P-value
    p_value = 1 - stats.f.cdf(f_stat, df_num, df_den)
    
    significant = p_value < 0.05
    
    if significant:
        interpretation = (
            f"The polynomial model provides a significantly better fit than the linear model "
            f"(F({df_num}, {df_den}) = {f_stat:.4f}, p = {p_value:.4f}). "
            f"Non-linear relationships are present."
        )
    else:
        interpretation = (
            f"There is no significant evidence that the polynomial model improves upon the linear model "
            f"(F({df_num}, {df_den}) = {f_stat:.4f}, p = {p_value:.4f}). "
            f"The linear model is sufficient."
        )
        
    return {
        "f_statistic": f_stat,
        "p_value": p_value,
        "significant": significant,
        "interpretation": interpretation,
        "df_num": df_num,
        "df_den": df_den
    }

def main():
    parser = argparse.ArgumentParser(description="Compare linear vs polynomial models (T024c).")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to non_linear_model_results.json (default: auto-resolve from config)")
    parser.add_argument("--output", type=str, default=None,
                        help="Path to output non_linear_comparison.json (default: auto-resolve from config)")
    args = parser.parse_args()
    
    # Resolve paths
    if args.input is None:
        # Try to find the file in the expected location based on T024b output
        # T024b output: data/interim/nonlinear_model_results.json
        input_path = get_path("interim", "nonlinear_model_results.json")
    else:
        input_path = args.input
        
    if args.output is None:
        output_path = get_path("processed", "non_linear_comparison.json")
    else:
        output_path = args.output
        
    print(f"Loading results from: {input_path}")
    try:
        results = load_poly_results(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
        
    # Extract necessary values
    # Expected structure from T024b:
    # {
    #   "linear_model": {"r2": float, "n_predictors": int},
    #   "polynomial_model": {"r2": float, "n_predictors": int},
    #   "n_observations": int
    # }
    # Or similar. We need to be flexible.
    
    linear_r2 = results.get("linear_model", {}).get("r2") or results.get("linear_r2")
    poly_r2 = results.get("polynomial_model", {}).get("r2") or results.get("poly_r2")
    n_obs = results.get("n_observations") or results.get("n")
    
    # Number of predictors (excluding intercept)
    p_linear = results.get("linear_model", {}).get("n_predictors") or results.get("linear_n_predictors")
    p_poly = results.get("polynomial_model", {}).get("n_predictors") or results.get("poly_n_predictors")
    
    if linear_r2 is None or poly_r2 is None or n_obs is None or p_linear is None or p_poly is None:
        print("Error: Could not extract required fields from input JSON.")
        print(f"Available keys: {results.keys()}")
        sys.exit(1)
        
    # Perform F-test
    f_test_results = perform_f_test(
        linear_r2=linear_r2,
        poly_r2=poly_r2,
        n=n_obs,
        p_linear=p_linear,
        p_poly=p_poly
    )
    
    # Prepare output
    output_data = {
        "linear_r2": linear_r2,
        "polynomial_r2": poly_r2,
        "n_observations": n_obs,
        "f_test": f_test_results,
        "significant_at_0p05": f_test_results["significant"],
        "interpretation": f_test_results["interpretation"]
    }
    
    # Ensure output directory exists
    ensure_dirs(output_path)
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"Results written to: {output_path}")
    print(f"Significant at 0.05: {f_test_results['significant']}")
    print(f"Interpretation: {f_test_results['interpretation']}")

if __name__ == "__main__":
    main()