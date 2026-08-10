"""
Regression Model for Statistical Properties of Integer Partitions.

This module implements the statistical modeling of the residual error R(n) = log(p_P(n)) - log(Q_as(n)).
It fits a Generalized Additive Model (GAM) or Linear Regression with splines to detect systematic bias
driven by prime density features and oscillatory terms.

Asymptotic Regime Definition (Task T018):
The analysis targets the TRANSITION REGION (100 < n <= 50,000).
In this regime, prime gaps are significant enough to create measurable "holes" in the summand set,
causing deviations from the smooth asymptotic baseline Q_as(n) derived from Meinardus' theorem.
The model explicitly includes features to capture these gap effects.
"""

import os
import sys
import json
import math
import argparse
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
from patsy import dmatrix
from scipy import stats

# Import local utilities if needed, though standard libs are used here
# from utils.prime_sieve import generate_primes # Not strictly needed if features are precomputed

def load_features(filepath: str) -> pd.DataFrame:
    """
    Load the precomputed features from the CSV file.
    
    Args:
        filepath: Path to data/processed/features.csv
        
    Returns:
        DataFrame with columns: n, R_n, pi_n, inv_log_n, dist_nearest, sin_log_n, cos_log_n
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Feature file not found: {filepath}. "
                                "Run feature_engineering.py first.")
    
    df = pd.read_csv(filepath)
    
    # Validate required columns
    required_cols = ['n', 'R_n', 'pi_n', 'inv_log_n', 'dist_nearest', 'sin_log_n', 'cos_log_n']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {filepath}: {missing}")
        
    # Filter for the asymptotic regime (transition region)
    # We exclude very small n where the asymptotic baseline is invalid
    # and ensure we are in the defined scope (n <= 50000)
    df = df[(df['n'] > 100) & (df['n'] <= 50000)]
    
    if df.empty:
        raise ValueError("No data points remaining after filtering for the asymptotic regime (100 < n <= 50000).")
        
    return df

def benjamini_hochberg(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply the Benjamini-Hochberg correction to a list of p-values.
    
    Args:
        p_values: Array of raw p-values.
        alpha: Significance level.
        
    Returns:
        Tuple of (adjusted p-values, boolean mask for significance)
    """
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([])
        
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate adjusted p-values
    # BH procedure: p_adj[i] = p[i] * n / i
    # We ensure monotonicity by taking the cumulative minimum from the end
    adjusted = np.zeros(n)
    adjusted[sorted_indices] = sorted_p * n / (np.arange(1, n + 1))
    
    # Enforce monotonicity
    for i in range(n - 2, -1, -1):
        adjusted[sorted_indices[i]] = min(adjusted[sorted_indices[i]], adjusted[sorted_indices[i+1]])
        
    # Clamp to 1.0
    adjusted = np.clip(adjusted, 0.0, 1.0)
    
    # Determine significance
    significant = adjusted < alpha
    
    return adjusted, significant

def fit_null_model(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Fit an intercept-only (null) model.
    
    Args:
        X: Feature matrix (ignored for null model).
        y: Target vector.
        
    Returns:
        Dictionary with null model stats.
    """
    mean_y = np.mean(y)
    ss_tot = np.sum((y - mean_y) ** 2)
    ss_res = np.sum((y - mean_y) ** 2) # Same as ss_tot for null model
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return {
        "type": "null",
        "intercept": float(mean_y),
        "r_squared": float(r_squared),
        "ss_res": float(ss_res),
        "ss_tot": float(ss_tot)
    }

def fit_full_model(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """
    Fit a linear regression model with the specified features.
    Uses Patsy to handle formula-like syntax if needed, but here we use direct matrix.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        feature_names: List of names corresponding to columns in X.
        
    Returns:
        Dictionary with model stats, coefficients, and p-values.
    """
    model = LinearRegression()
    model.fit(X, y)
    
    y_pred = model.predict(X)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    # Calculate p-values for coefficients
    n_samples, n_features = X.shape
    dof = n_samples - n_features - 1
    
    # Standard errors
    mse = ss_res / dof if dof > 0 else 0
    try:
        cov_matrix = mse * np.linalg.inv(X.T @ X)
        std_err = np.sqrt(np.diag(cov_matrix))
    except np.linalg.LinAlgError:
        std_err = np.zeros(n_features)
        
    t_stats = model.coef_ / std_err if std_err.any() else np.zeros(n_features)
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), dof))
    
    results = {
        "type": "full",
        "r_squared": float(r_squared),
        "ss_res": float(ss_res),
        "coefficients": {name: float(val) for name, val in zip(feature_names, model.coef_)},
        "p_values": {name: float(val) for name, val in zip(feature_names, p_values)},
        "std_errors": {name: float(val) for name, val in zip(feature_names, std_err)}
    }
    
    return results

def perform_cross_validation(X: np.ndarray, y: np.ndarray, k: int = 10) -> Dict[str, Any]:
    """
    Perform k-fold cross-validation.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        k: Number of folds.
        
    Returns:
        Dictionary with MSE per fold and mean MSE.
    """
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    mse_scores = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        mse = mean_squared_error(y_test, y_pred)
        mse_scores.append(mse)
        
    return {
        "k_folds": k,
        "mse_per_fold": [float(m) for m in mse_scores],
        "mean_mse": float(np.mean(mse_scores)),
        "std_mse": float(np.std(mse_scores))
    }

def save_results(results: Dict[str, Any], filepath: str):
    """
    Save results to a JSON file.
    
    Args:
        results: Dictionary containing all model results.
        filepath: Output path.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """
    Main entry point for the regression model pipeline.
    
    Steps:
    1. Load features from data/processed/features.csv.
    2. Fit Null Model.
    3. Fit Full Model with prime density and oscillatory terms.
    4. Apply Benjamini-Hochberg correction to p-values.
    5. Perform 10-fold Cross-Validation.
    6. Save results to data/processed/model_results.json.
    """
    parser = argparse.ArgumentParser(description="Fit regression model to partition residuals.")
    parser.add_argument("--input", type=str, default="data/processed/features.csv",
                        help="Path to features CSV.")
    parser.add_argument("--output", type=str, default="data/processed/model_results.json",
                        help="Path to output JSON.")
    args = parser.parse_args()
    
    print(f"Loading features from {args.input}...")
    df = load_features(args.input)
    
    # Prepare data
    feature_cols = ['pi_n', 'inv_log_n', 'dist_nearest', 'sin_log_n', 'cos_log_n']
    X = df[feature_cols].values
    y = df['R_n'].values
    
    print(f"Dataset size: {len(df)} samples.")
    print(f"Fitting Null Model...")
    null_results = fit_null_model(X, y)
    
    print("Fitting Full Model...")
    full_results = fit_full_model(X, y, feature_cols)
    
    print("Applying Benjamini-Hochberg correction...")
    p_vals = np.array([full_results['p_values'][name] for name in feature_cols])
    adj_p_vals, significant = benjamini_hochberg(p_vals, alpha=0.05)
    
    # Update full results with corrected p-values
    full_results['adjusted_p_values'] = {name: float(val) for name, val in zip(feature_cols, adj_p_vals)}
    full_results['significant_at_0.05'] = {name: bool(sig) for name, sig in zip(feature_cols, significant)}
    
    print("Performing 10-fold Cross-Validation...")
    cv_results = perform_cross_validation(X, y, k=10)
    
    # Compile final results
    final_results = {
        "asymptotic_regime": "Transition Region (100 < n <= 50,000)",
        "description": "Analysis of residual error R(n) in the transition region where prime gaps create 'holes' in the summand set.",
        "null_model": null_results,
        "full_model": full_results,
        "cross_validation": cv_results
    }
    
    print(f"Saving results to {args.output}...")
    save_results(final_results, args.output)
    
    print("Done.")

if __name__ == "__main__":
    main()