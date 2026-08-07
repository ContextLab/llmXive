"""
T024: Implement non-linear interaction analysis (polynomial alpha/beta) and F-test comparison (FR-012).

This script:
1. Loads the validated features from data/processed/features.csv.
2. Fits two models:
   - Linear: RT ~ Alpha + Beta + Covariates
   - Non-linear: RT ~ Alpha + Beta + Alpha^2 + Beta^2 + (Alpha * Beta) + Covariates
3. Performs an F-test to compare the nested models.
4. Saves the results to data/processed/non_linear_comparison.json.
"""
import os
import sys
import json
import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, get_seed
from utils.stats_helpers import f_test_comparison

def load_features():
    """Load the processed features dataset."""
    input_path = get_path("processed", "features.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please ensure T016 (validation) and T015 (feature generation) have completed."
        )
    df = pd.read_csv(input_path)
    
    # Ensure we have the necessary columns
    required_cols = ['participant_id', 'median_rt', 'alpha_rel', 'beta_rel']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in features.csv: {missing}")
    
    return df

def prepare_polynomial_features(df):
    """
    Create polynomial and interaction terms for non-linear model.
    Features: Alpha, Beta, Alpha^2, Beta^2, Alpha*Beta
    """
    df = df.copy()
    
    # Drop rows with NaN in key columns to avoid issues in modeling
    df = df.dropna(subset=['alpha_rel', 'beta_rel', 'median_rt'])
    
    # Polynomial terms
    df['alpha_sq'] = df['alpha_rel'] ** 2
    df['beta_sq'] = df['beta_rel'] ** 2
    
    # Interaction term
    df['alpha_beta_interact'] = df['alpha_rel'] * df['beta_rel']
    
    return df

def fit_models(df):
    """
    Fit Linear and Non-linear models using OLS from scipy/stats manually 
    or via a simple matrix approach to avoid heavy dependencies if not needed,
    but using statsmodels is ideal. Since statsmodels isn't explicitly in the 
    provided API surface, we will implement the OLS and F-test logic using 
    numpy and scipy to ensure compatibility with the existing utils.
    
    Model 1 (Reduced): y = b0 + b1*Alpha + b2*Beta
    Model 2 (Full):    y = b0 + b1*Alpha + b2*Beta + b3*Alpha^2 + b4*Beta^2 + b5*Alpha*Beta
    """
    # Prepare matrices
    # Reduced model predictors
    X_reduced = np.column_stack([
        np.ones(len(df)),
        df['alpha_rel'].values,
        df['beta_rel'].values
    ])
    y = df['median_rt'].values

    # Full model predictors
    X_full = np.column_stack([
        np.ones(len(df)),
        df['alpha_rel'].values,
        df['beta_rel'].values,
        df['alpha_sq'].values,
        df['beta_sq'].values,
        df['alpha_beta_interact'].values
    ])

    # Solve OLS using least squares
    # beta = (X'X)^-1 X'y
    try:
        # Reduced
        beta_reduced, _, _, _ = np.linalg.lstsq(X_reduced, y, rcond=None)
        y_pred_reduced = X_reduced @ beta_reduced
        ss_res_reduced = np.sum((y - y_pred_reduced) ** 2)
        df_res_reduced = len(y) - X_reduced.shape[1]

        # Full
        beta_full, _, _, _ = np.linalg.lstsq(X_full, y, rcond=None)
        y_pred_full = X_full @ beta_full
        ss_res_full = np.sum((y - y_pred_full) ** 2)
        df_res_full = len(y) - X_full.shape[1]

    except np.linalg.LinAlgError as e:
        raise RuntimeError(f"Linear algebra error during model fitting: {e}")

    # F-test for nested models
    # F = ((RSS_reduced - RSS_full) / (df_reduced - df_full)) / (RSS_full / df_full)
    # Note: df_res = n - p. So df_reduced - df_full = (n - p_red) - (n - p_full) = p_full - p_red
    num_df = X_full.shape[1] - X_reduced.shape[1]
    den_df = df_res_full

    if den_df <= 0:
        raise ValueError("Insufficient degrees of freedom for F-test. Sample size too small relative to model complexity.")

    f_stat = ((ss_res_reduced - ss_res_full) / num_df) / (ss_res_full / den_df)
    p_value = 1.0 - stats.f.cdf(f_stat, num_df, den_df)

    # Calculate R-squared for both
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2_reduced = 1 - (ss_res_reduced / ss_tot)
    r2_full = 1 - (ss_res_full / ss_tot)

    return {
        "reduced_model": {
            "description": "Linear: RT ~ Alpha + Beta",
            "r_squared": float(r2_reduced),
            "ss_res": float(ss_res_reduced),
            "degrees_of_freedom_residual": int(df_res_reduced),
            "coefficients": {
                "intercept": float(beta_reduced[0]),
                "alpha": float(beta_reduced[1]),
                "beta": float(beta_reduced[2])
            }
        },
        "full_model": {
            "description": "Non-linear: RT ~ Alpha + Beta + Alpha^2 + Beta^2 + Alpha*Beta",
            "r_squared": float(r2_full),
            "ss_res": float(ss_res_full),
            "degrees_of_freedom_residual": int(df_res_full),
            "coefficients": {
                "intercept": float(beta_full[0]),
                "alpha": float(beta_full[1]),
                "beta": float(beta_full[2]),
                "alpha_squared": float(beta_full[3]),
                "beta_squared": float(beta_full[4]),
                "alpha_beta_interaction": float(beta_full[5])
            }
        },
        "f_test": {
            "description": "Comparison of Non-linear vs Linear model",
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "numerator_df": int(num_df),
            "denominator_df": int(den_df),
            "significant_at_0.05": p_value < 0.05,
            "significant_at_0.01": p_value < 0.01
        },
        "sample_size": int(len(df))
    }

def save_results(results, output_path):
    """Save results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")

def main():
    """Main entry point for T024."""
    parser = argparse.ArgumentParser(description="Non-linear interaction analysis (T024)")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path (optional)")
    args = parser.parse_args()

    # Set seed for reproducibility (though OLS is deterministic)
    seed = get_seed()
    np.random.seed(seed)

    print(f"Starting Non-linear Interaction Analysis (T024)...")
    print(f"Using seed: {seed}")

    try:
        # 1. Load Data
        print("Loading features...")
        df = load_features()
        print(f"Loaded {len(df)} participants.")

        # 2. Prepare Polynomial Features
        print("Creating polynomial features...")
        df_poly = prepare_polynomial_features(df)

        # 3. Fit Models and Perform F-Test
        print("Fitting models and performing F-test...")
        results = fit_models(df_poly)

        # 4. Save Results
        output_path = args.output or get_path("processed", "non_linear_comparison.json")
        save_results(results, output_path)

        print("Analysis complete.")
        
        # Print summary to stdout
        print("\n--- Summary ---")
        print(f"Linear R²: {results['reduced_model']['r_squared']:.4f}")
        print(f"Non-linear R²: {results['full_model']['r_squared']:.4f}")
        print(f"F-statistic: {results['f_test']['f_statistic']:.4f}")
        print(f"P-value: {results['f_test']['p_value']:.4f}")
        if results['f_test']['significant_at_0.05']:
            print("Result: The non-linear model provides a statistically significant improvement over the linear model (p < 0.05).")
        else:
            print("Result: The non-linear model does not provide a statistically significant improvement over the linear model (p >= 0.05).")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Data Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
