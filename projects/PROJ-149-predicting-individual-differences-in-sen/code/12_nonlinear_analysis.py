"""
T024: Perform non-linear interaction analysis (polynomial terms).
This script fits polynomial models and performs F-tests to compare against linear models.
It produces the data/processed/non_linear_comparison.json artifact.
"""
import os
import sys
import json
import argparse
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score
from scipy import stats

# Import config utilities if needed, but standard libraries used here
from config import ensure_dirs

def load_features():
    """
    Loads the features dataset.
    """
    path = Path("data/processed/features.csv")
    if not path.exists():
        raise FileNotFoundError("Features file not found at data/processed/features.csv")
    return pd.read_csv(path)

def prepare_polynomial_features(X, y, degree=2):
    """
    Prepares polynomial features and fits the model.
    """
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly.fit_transform(X)
    
    model = LinearRegression()
    model.fit(X_poly, y)
    y_pred = model.predict(X_poly)
    
    return model, y_pred, X_poly

def fit_models(df, feature_cols, target_col='median_rt', degree=2):
    """
    Fits linear and polynomial models and compares them.
    """
    X = df[feature_cols].values
    y = df[target_col].values

    # Linear Model
    lin_model = LinearRegression()
    lin_model.fit(X, y)
    y_pred_lin = lin_model.predict(X)
    r2_lin = r2_score(y, y_pred_lin)
    rss_lin = np.sum((y - y_pred_lin) ** 2)
    df_lin = len(y) - len(feature_cols) - 1

    # Polynomial Model
    poly_model, y_pred_poly, X_poly = prepare_polynomial_features(X, y, degree=degree)
    r2_poly = r2_score(y, y_pred_poly)
    rss_poly = np.sum((y - y_pred_poly) ** 2)
    n_params_poly = X_poly.shape[1] + 1 # +1 for intercept
    df_poly = len(y) - n_params_poly

    # F-Test
    # F = ((RSS_lin - RSS_poly) / (df_lin - df_poly)) / (RSS_poly / df_poly)
    if rss_poly == 0 or df_poly == 0:
        f_stat = np.inf
        p_val = 0.0
    else:
        numerator = (rss_lin - rss_poly) / (df_lin - df_poly)
        denominator = rss_poly / df_poly
        if denominator == 0:
            f_stat = np.inf
            p_val = 0.0
        else:
            f_stat = numerator / denominator
            p_val = 1 - stats.f.cdf(f_stat, df_lin - df_poly, df_poly)

    return {
        'linear_model': {
            'r2': float(r2_lin),
            'rss': float(rss_lin),
            'df': int(df_lin)
        },
        'polynomial_model': {
            'r2': float(r2_poly),
            'rss': float(rss_poly),
            'df': int(df_poly),
            'degree': degree
        },
        'f_test': {
            'f_statistic': float(f_stat),
            'p_value': float(p_val),
            'significant_at_0_05': p_val < 0.05,
            'degrees_of_freedom_num': int(df_lin - df_poly),
            'degrees_of_freedom_den': int(df_poly)
        }
    }

def save_results(results: dict, output_path: str):
    """
    Saves the non-linear comparison results to JSON.
    """
    output = Path(output_path)
    ensure_dirs(output)
    
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved non-linear comparison to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Non-linear interaction analysis (T024)")
    parser.add_argument('--degree', type=int, default=2, help='Polynomial degree')
    parser.add_argument('--output', default='data/processed/non_linear_comparison.json', help='Output path')
    args = parser.parse_args()

    print("Loading features...")
    try:
        df = load_features()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Select band power columns (relative)
    # Based on T015, these are delta, theta, alpha, low_beta, high_beta, gamma
    band_cols = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    # Filter to only those present
    feature_cols = [c for c in band_cols if c in df.columns]
    
    if 'median_rt' not in df.columns:
        print("Error: 'median_rt' column not found in features.")
        sys.exit(1)

    if not feature_cols:
        print("Error: No band power columns found.")
        sys.exit(1)

    print(f"Fitting models with degree {args.degree} using features: {feature_cols}")
    results = fit_models(df, feature_cols, target_col='median_rt', degree=args.degree)

    print("Saving results...")
    save_results(results, args.output)

    print("T024 Complete.")

if __name__ == "__main__":
    main()