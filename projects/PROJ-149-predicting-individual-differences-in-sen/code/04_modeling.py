import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LassoCV
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error

# Ensure we can import from code/
sys.path.insert(0, str(Path(__file__).parent))
from config import get_path, set_global_seed

def load_features(path_str: str) -> pd.DataFrame:
    """Load the processed features dataset."""
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {path}")
    return pd.read_csv(path)

def prepare_data(df: pd.DataFrame, target_col: str = "median_rt", 
                 feature_cols: list = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare X and y for modeling.
    Drops rows with NaNs in target or features.
    """
    if feature_cols is None:
        # Select relative power columns if available, otherwise all numeric except target
        cols = [c for c in df.columns if c.startswith("rel_") and c != target_col]
        if not cols:
            cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col]
        feature_cols = cols

    data = df[feature_cols + [target_col]].dropna()
    X = data[feature_cols].values
    y = data[target_col].values
    return X, y

def fit_model_with_cv(X: np.ndarray, y: np.ndarray, seed: int = 42) -> Dict[str, Any]:
    """
    Fit Multiple Linear Regression and LASSO with 5-fold CV.
    Returns metrics including Adjusted R² and optimal lambda.
    """
    set_global_seed(seed)
    n, p = X.shape
    results = {}

    # 1. Multiple Linear Regression
    model_lr = LinearRegression()
    kf = KFold(n_splits=5, shuffle=True, random_state=seed)
    
    r2_scores = []
    y_pred_lr = np.zeros_like(y)

    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model_lr.fit(X_train, y_train)
        y_pred = model_lr.predict(X_test)
        r2_scores.append(r2_score(y_test, y_pred))
        y_pred_lr[test_idx] = y_pred

    mean_r2 = np.mean(r2_scores)
    rmse_lr = np.sqrt(mean_squared_error(y, y_pred_lr))
    
    # Calculate Adjusted R² for the full dataset (using all data for final metric reporting as per common practice in small N)
    # Or use the CV prediction R2. We will calculate Adj R2 on the full fit for the final report.
    model_lr_full = LinearRegression().fit(X, y)
    r2_full = r2_score(y, model_lr_full.predict(X))
    # Adjusted R^2 = 1 - (1 - R^2) * (n - 1) / (n - p - 1)
    if n > p + 1:
        adj_r2 = 1 - (1 - r2_full) * (n - 1) / (n - p - 1)
    else:
        adj_r2 = np.nan # Cannot calculate if p >= n-1

    results["linear_regression"] = {
        "mean_cv_r2": float(mean_r2),
        "cv_std_r2": float(np.std(r2_scores)),
        "rmse": float(rmse_lr),
        "adj_r2": float(adj_r2) if not np.isnan(adj_r2) else None,
        "coefficients": {k: float(v) for k, v in zip(
            [c for c in df.columns if c.startswith("rel_") or (c != "median_rt" and c in df.select_dtypes(include=[np.number]).columns)], 
            model_lr_full.coef_
        )},
        "intercept": float(model_lr_full.intercept_)
    }

    # 2. LASSO Regression with CV for lambda selection
    # LassoCV handles lambda tuning internally
    lasso_cv = LassoCV(cv=5, random_state=seed, max_iter=10000)
    lasso_cv.fit(X, y)
    
    optimal_lambda = lasso_cv.alpha_
    y_pred_lasso = lasso_cv.predict(X)
    r2_lasso = r2_score(y, y_pred_lasso)
    rmse_lasso = np.sqrt(mean_squared_error(y, y_pred_lasso))

    # Adjusted R2 for Lasso (using non-zero coefficients count for p)
    non_zero_coef = np.sum(lasso_cv.coef_ != 0)
    p_lasso = non_zero_coef
    if n > p_lasso + 1:
        adj_r2_lasso = 1 - (1 - r2_lasso) * (n - 1) / (n - p_lasso - 1)
    else:
        adj_r2_lasso = None

    results["lasso"] = {
        "optimal_lambda": float(optimal_lambda),
        "r2": float(r2_lasso),
        "rmse": float(rmse_lasso),
        "adj_r2": float(adj_r2_lasso) if adj_r2_lasso is not None else None,
        "n_nonzero_features": int(non_zero_coef),
        "coefficients": {k: float(v) for k, v in zip(
            [c for c in df.columns if c.startswith("rel_") or (c != "median_rt" and c in df.select_dtypes(include=[np.number]).columns)], 
            lasso_cv.coef_
        )}
    }

    return results

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save model results to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Fit predictive models and log results.")
    parser.add_argument("--input", type=str, default="data/processed/features.csv", 
                        help="Path to features CSV")
    parser.add_argument("--output", type=str, default="data/processed/model_results.json",
                        help="Path to output JSON")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Load data
    print(f"Loading features from {args.input}...")
    df = load_features(args.input)
    
    # Prepare data
    print("Preparing data...")
    X, y = prepare_data(df, target_col="median_rt")
    
    if X.shape[0] == 0:
        raise ValueError("No valid data points after cleaning.")

    # Fit models
    print("Fitting models...")
    results = fit_model_with_cv(X, y, seed=args.seed)
    
    # Add metadata
    results["metadata"] = {
        "n_samples": int(len(y)),
        "n_features": int(X.shape[1]),
        "seed": args.seed
    }

    # Save results
    save_results(results, args.output)

    # Print summary
    print("\n--- Model Results Summary ---")
    print(f"Linear Regression Adjusted R²: {results['linear_regression']['adj_r2']:.4f}")
    print(f"LASSO Optimal Lambda: {results['lasso']['optimal_lambda']:.4f}")
    print(f"LASSO Adjusted R²: {results['lasso']['adj_r2']:.4f}")

if __name__ == "__main__":
    main()
