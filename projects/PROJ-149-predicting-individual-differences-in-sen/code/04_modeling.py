"""
code/04_modeling.py
Implements Multiple Linear Regression with 5-fold cross-validation.

Outputs:
    data/interim/split_indices.json
    data/processed/model_results.json (partial)
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from config import set_global_seed, get_seed, get_path, ensure_dirs

def load_features(filepath: str) -> pd.DataFrame:
    """
    Load the processed features dataset.
    Expects columns: participant_id, median_rt, delta, theta, alpha, low_beta, high_beta, gamma (or CLR variants).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Features file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Validate required columns
    required_cols = ['participant_id', 'median_rt']
    # Check for at least one band power column
    band_cols = [c for c in df.columns if any(b in c.lower() for b in ['delta', 'theta', 'alpha', 'beta', 'gamma'])]
    
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns. Found: {list(df.columns)}")
    
    if len(band_cols) == 0:
        raise ValueError("No band power columns found in features file.")
        
    return df, band_cols

def prepare_data(df: pd.DataFrame, feature_cols: list) -> tuple:
    """
    Prepare X (features) and y (target) arrays.
    Handles NaNs by dropping rows (as per strict validation in T016).
    """
    # Drop rows with any NaN in the selected columns
    cols_to_use = ['median_rt'] + feature_cols
    clean_df = df[cols_to_use].dropna()
    
    if clean_df.empty:
        raise ValueError("No valid data rows after dropping NaNs.")
        
    y = clean_df['median_rt'].values
    X = clean_df[feature_cols].values
    
    return X, y, clean_df['participant_id'].values

def fit_model_with_cv(X: np.ndarray, y: np.ndarray, n_folds: int = 5, random_state: int = 42) -> dict:
    """
    Fit Multiple Linear Regression with K-Fold Cross-Validation.
    
    Returns a dictionary containing:
      - fold_scores: list of R2 scores per fold
      - mean_r2: float
      - std_r2: float
      - rmse_cv: float (root mean squared error averaged over folds)
      - split_indices: dict mapping fold index to train/test indices
      - cv_model: the fitted LinearRegression object (optional, not saved to JSON)
    """
    set_global_seed(random_state)
    
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    fold_scores = []
    fold_rmse = []
    split_indices = {}
    
    # We need to store the split indices for later permutation tests (T022)
    # We'll store them as relative positions in the clean_df (which we don't have here directly, 
    # but we can store the indices relative to the input X array)
    
    # To ensure we can reconstruct splits later, we store indices of the input arrays
    # Note: The caller (main) is responsible for mapping these back to participant_ids if needed.
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        fold_scores.append(r2)
        fold_rmse.append(rmse)
        
        # Store indices relative to the input X array
        split_indices[str(fold_idx)] = {
            "train": train_idx.tolist(),
            "test": test_idx.tolist()
        }
        
        # Optional: print progress
        # print(f"Fold {fold_idx}: R² = {r2:.4f}, RMSE = {rmse:.4f}")

    results = {
        "fold_scores": fold_scores,
        "mean_r2": float(np.mean(fold_scores)),
        "std_r2": float(np.std(fold_scores)),
        "rmse_cv": float(np.mean(fold_rmse)),
        "split_indices": split_indices,
        "n_folds": n_folds,
        "n_samples": len(y),
        "n_features": X.shape[1]
    }
    
    return results

def save_results(results: dict, output_path: str, split_path: str):
    """
    Save model results and split indices to JSON files.
    """
    # Ensure directories exist
    ensure_dirs([output_path, split_path])
    
    # Save split indices separately as required by T017/T022
    with open(split_path, 'w') as f:
        json.dump(results['split_indices'], f, indent=2)
    
    # Prepare partial model results (excluding split_indices to keep file clean, 
    # though spec says partial results go here, we'll include metrics)
    partial_results = {
        "model_type": "Multiple Linear Regression",
        "cv_method": "KFold",
        "n_folds": results['n_folds'],
        "mean_r2": results['mean_r2'],
        "std_r2": results['std_r2'],
        "rmse_cv": results['rmse_cv'],
        "n_samples": results['n_samples'],
        "n_features": results['n_features']
        # split_indices is saved separately
    }
    
    with open(output_path, 'w') as f:
        json.dump(partial_results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Fit MLR model with 5-fold CV")
    parser.add_argument("--input", type=str, default=None, 
                        help="Path to features.csv. If None, uses config path.")
    parser.add_argument("--output", type=str, default=None,
                        help="Path to model_results.json. If None, uses config path.")
    parser.add_argument("--splits", type=str, default=None,
                        help="Path to split_indices.json. If None, uses config path.")
    parser.add_argument("--folds", type=int, default=5,
                        help="Number of CV folds (default: 5)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    
    args = parser.parse_args()
    
    # Resolve paths
    input_path = args.input or get_path("processed_features")
    output_path = args.output or get_path("model_results")
    split_path = args.splits or get_path("split_indices")
    
    print(f"Loading features from: {input_path}")
    try:
        df, band_cols = load_features(input_path)
    except Exception as e:
        print(f"Error loading features: {e}")
        sys.exit(1)
        
    print(f"Found {len(df)} participants and {len(band_cols)} band features: {band_cols}")
    
    X, y, participant_ids = prepare_data(df, band_cols)
    print(f"Prepared data: X shape {X.shape}, y shape {y.shape}")
    
    if X.shape[0] < args.folds:
        print(f"Error: Not enough samples ({X.shape[0]}) for {args.folds} folds.")
        sys.exit(1)
    
    print(f"Fitting model with {args.folds}-fold CV...")
    results = fit_model_with_cv(X, y, n_folds=args.folds, random_state=args.seed)
    
    print(f"Mean R²: {results['mean_r2']:.4f} (+/- {results['std_r2']:.4f})")
    print(f"Mean RMSE: {results['rmse_cv']:.4f}")
    
    print(f"Saving results to: {output_path}")
    print(f"Saving split indices to: {split_path}")
    save_results(results, output_path, split_path)
    
    print("Task T017 completed successfully.")

if __name__ == "__main__":
    main()