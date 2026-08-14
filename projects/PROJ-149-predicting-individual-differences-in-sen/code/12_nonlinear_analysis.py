"""
T024: Perform non-linear interaction analysis.

This script performs polynomial regression (degree=2) on alpha and beta bands
to test for non-linear relationships with RT. It then compares the linear
and non-linear models using an F-test.

Output: data/processed/nonlinear_results.json
"""

import os
import sys
import json
import argparse
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score

from config import get_path, ensure_dirs

def load_features():
    """Load features dataset."""
    path = get_path("data/processed", "features.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Features file not found at {path}")
    return pd.read_csv(path)

def prepare_polynomial_features(df, band='alpha', degree=2):
    """Prepare polynomial features for a specific band."""
    # Get the band feature
    band_col = f"{band}_clr" if f"{band}_clr" in df.columns else f"{band}_relative"
    if band_col not in df.columns:
        # Try without suffix
        band_col = band
    
    if band_col not in df.columns:
        raise ValueError(f"Band column {band_col} not found in features")
    
    X = df[band_col].values.reshape(-1, 1)
    y = df['median_rt'].values
    
    # Create polynomial features
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly.fit_transform(X)
    
    return X_poly, y, poly

def fit_models(X_poly, y):
    """Fit linear and polynomial models and compare."""
    # Fit linear model (just first degree term)
    linear_model = LinearRegression()
    linear_model.fit(X_poly[:, :1], y)
    linear_r2 = linear_model.score(X_poly[:, :1], y)
    
    # Fit polynomial model
    poly_model = LinearRegression()
    poly_model.fit(X_poly, y)
    poly_r2 = poly_model.score(X_poly, y)
    
    # F-test comparison
    n = len(y)
    p_linear = 1  # degrees of freedom for linear
    p_poly = X_poly.shape[1]  # degrees of freedom for polynomial
    
    # Calculate F-statistic
    ss_res_poly = np.sum((y - poly_model.predict(X_poly)) ** 2)
    ss_res_linear = np.sum((y - linear_model.predict(X_poly[:, :1])) ** 2)
    
    if ss_res_poly == 0:
        f_stat = float('inf')
    else:
        f_stat = ((ss_res_linear - ss_res_poly) / (p_poly - p_linear)) / (ss_res_poly / (n - p_poly - 1))
    
    # Calculate p-value
    from scipy import stats
    p_value = 1 - stats.f.cdf(f_stat, p_poly - p_linear, n - p_poly - 1)
    
    return {
        'linear_r2': linear_r2,
        'polynomial_r2': poly_r2,
        'r2_improvement': poly_r2 - linear_r2,
        'f_statistic': f_stat,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'degrees_of_freedom': {'model': p_poly - p_linear, 'error': n - p_poly - 1}
    }

def save_results(results, output_path):
    """Save non-linear analysis results."""
    ensure_dirs(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved non-linear analysis results to {output_path}")

def main():
    """Main function for non-linear analysis."""
    parser = argparse.ArgumentParser(description="Perform non-linear interaction analysis")
    parser.add_argument("--band", type=str, default="alpha",
                      help="Band to analyze (default: alpha)")
    parser.add_argument("--degree", type=int, default=2,
                      help="Polynomial degree (default: 2)")
    parser.add_argument("--output", type=str, default=None,
                      help="Output path for results JSON (default: data/processed/nonlinear_results.json)")
    args = parser.parse_args()
    
    print(f"Loading features...")
    df = load_features()
    
    print(f"Preparing polynomial features for {args.band} band (degree={args.degree})...")
    X_poly, y, poly = prepare_polynomial_features(df, args.band, args.degree)
    
    print("Fitting models and comparing...")
    results = fit_models(X_poly, y)
    results['band'] = args.band
    results['degree'] = args.degree
    results['sample_size'] = len(df)
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = get_path("data/processed", "nonlinear_results.json")
    
    save_results(results, output_path)
    
    # Also save to the expected location for T025
    expected_output = get_path("data/processed", "non_linear_comparison.json")
    if output_path != expected_output:
        ensure_dirs(expected_output)
        with open(expected_output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Also saved to {expected_output}")
    
    print(f"Non-linear analysis completed. R² improvement: {results['r2_improvement']:.4f}, p-value: {results['p_value']:.4f}")

if __name__ == "__main__":
    main()
