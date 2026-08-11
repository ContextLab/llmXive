"""
T024: Non-linear interaction analysis (polynomial alpha/beta, degree=2) and F-test comparison.
Implements FR-012.

Input: data/processed/features.csv (from T016)
Output: data/processed/non_linear_comparison.json
Dependencies: T019 (model_results.json for baseline comparison)
"""
import os
import sys
import json
import argparse
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from config import get_path, ensure_dirs, get_seed
from utils.stats_helpers import f_test_comparison

def load_features():
    """Load the processed features dataset."""
    features_path = get_path("processed", "features.csv")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Input file not found: {features_path}. Run T016 first.")
    return pd.read_csv(features_path)

def prepare_polynomial_features(df, target_col="median_rt", degree=2):
    """
    Prepare polynomial features for Alpha and Beta bands.
    Returns X_poly, y, feature_names, and the original X for baseline.
    """
    # Select relevant band power columns (relative/CLR transformed)
    # Assuming columns are named: alpha_rel, beta_rel (or similar based on T015)
    # We need to identify the exact column names for alpha and beta from the dataframe
    cols = df.columns.tolist()
    alpha_cols = [c for c in cols if 'alpha' in c.lower() and ('rel' in c.lower() or 'clr' in c.lower())]
    beta_cols = [c for c in cols if 'beta' in c.lower() and ('rel' in c.lower() or 'clr' in c.lower())]
    
    if not alpha_cols or not beta_cols:
        # Fallback to generic names if specific ones aren't found, but warn
        warnings.warn("Could not find specific alpha/beta relative columns. Attempting generic names.")
        if 'alpha_rel' in cols: alpha_cols = ['alpha_rel']
        if 'beta_rel' in cols: beta_cols = ['beta_rel']
    
    if not alpha_cols or not beta_cols:
        raise ValueError("Could not identify Alpha and Beta band columns for polynomial expansion.")

    # Use the first found alpha and beta column for interaction
    alpha_col = alpha_cols[0]
    beta_col = beta_cols[0]
    
    X_base = df[[alpha_col, beta_col]].values
    y = df[target_col].values

    # Create polynomial features (degree=2)
    poly = PolynomialFeatures(degree=degree, include_bias=False, interaction_only=False)
    X_poly = poly.fit_transform(X_base)
    
    feature_names = poly.get_feature_names_out([alpha_col, beta_col])
    
    return X_poly, y, feature_names, X_base, alpha_col, beta_col

def fit_models(X_train, y_train, X_test, y_test, feature_names):
    """
    Fit Linear (Baseline) and Polynomial (Interaction) models.
    Returns model results and statistics for F-test.
    """
    # 1. Baseline Linear Model (using original 2 features)
    # Note: X_train_poly has 5 features: [1, x1, x2, x1^2, x1*x2, x2^2] if interaction_only=False
    # But we need to compare a model with just [x1, x2] vs [x1, x2, x1^2, x2^2, x1*x2]
    # To do this fairly with sklearn, we can fit a model on the full poly set, 
    # but for F-test we need the residual sum of squares (RSS) and degrees of freedom.
    
    # Actually, F-test compares nested models.
    # Model 0 (Reduced): y = b0 + b1*x1 + b2*x2
    # Model 1 (Full): y = b0 + b1*x1 + b2*x2 + b3*x1^2 + b4*x2^2 + b5*x1*x2
    
    # We need to extract the RSS for both.
    
    # Fit Reduced Model (Linear on original 2)
    # We need to slice X_poly to get only the linear terms (indices 1 and 2 if bias is included, 
    # but include_bias=False means indices 0,1 are x1, x2? No, PolynomialFeatures with 2 inputs:
    # [1, 0]: x1, [0, 1]: x2, [1, 0]: x1^2, [1, 1]: x1*x2, [0, 1]: x2^2
    # With include_bias=False: [x1, x2, x1^2, x1*x2, x2^2]
    
    # Reduced features: indices 0, 1
    X_train_red = X_train[:, :2]
    X_test_red = X_test[:, :2]
    
    model_red = LinearRegression()
    model_red.fit(X_train_red, y_train)
    y_pred_red_test = model_red.predict(X_test_red)
    rss_red = np.sum((y_test - y_pred_red_test) ** 2)
    df_red = len(y_test) - 2 - 1 # n - p - 1 (p=2)
    
    # Fit Full Model (Polynomial)
    model_full = LinearRegression()
    model_full.fit(X_train, y_train)
    y_pred_full_test = model_full.predict(X_test)
    rss_full = np.sum((y_test - y_pred_full_test) ** 2)
    df_full = len(y_test) - X_train.shape[1] - 1 # n - p - 1 (p=5)
    
    # Calculate R-squared for both
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    r2_red = 1 - (rss_red / ss_tot)
    r2_full = 1 - (rss_full / ss_tot)
    
    # F-test for significance of the added terms
    # F = ((RSS_red - RSS_full) / (df_red - df_full)) / (RSS_full / df_full)
    num_df = df_red - df_full
    den_df = df_full
    f_stat, p_val = f_test_comparison(rss_red, rss_full, num_df, den_df)
    
    return {
        "baseline": {
            "r2": float(r2_red),
            "rss": float(rss_red),
            "df_error": int(df_red),
            "coefficients": model_red.coef_.tolist(),
            "intercept": float(model_red.intercept_)
        },
        "polynomial": {
            "r2": float(r2_full),
            "rss": float(rss_full),
            "df_error": int(df_full),
            "coefficients": model_full.coef_.tolist(),
            "intercept": float(model_full.intercept_)
        },
        "f_test": {
            "f_statistic": float(f_stat),
            "p_value": float(p_val),
            "numerator_df": int(num_df),
            "denominator_df": int(den_df),
            "significant_at_0.05": bool(p_val < 0.05)
        },
        "feature_names": list(feature_names)
    }

def save_results(results, output_path):
    """Save results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Non-linear interaction analysis (T024)")
    parser.add_argument("--degree", type=int, default=2, help="Polynomial degree")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set size")
    args = parser.parse_args()

    print("Loading features...")
    df = load_features()

    print(f"Preparing polynomial features (degree={args.degree})...")
    X_poly, y, feature_names, X_base, alpha_col, beta_col = prepare_polynomial_features(
        df, target_col="median_rt", degree=args.degree
    )

    # Split data (using seed from config)
    seed = get_seed()
    X_train, X_test, y_train, y_test = train_test_split(
        X_poly, y, test_size=args.test_size, random_state=seed
    )

    print(f"Fitting models (Baseline vs Polynomial on {alpha_col} & {beta_col})...")
    results = fit_models(X_train, y_train, X_test, y_test, feature_names)

    # Add metadata
    results["metadata"] = {
        "task_id": "T024",
        "alpha_column": alpha_col,
        "beta_column": beta_col,
        "polynomial_degree": args.degree,
        "test_size": args.test_size,
        "seed": seed
    }

    output_dir = ensure_dirs("processed")
    output_path = os.path.join(output_dir, "non_linear_comparison.json")
    
    save_results(results, output_path)
    print("Analysis complete.")

if __name__ == "__main__":
    main()
