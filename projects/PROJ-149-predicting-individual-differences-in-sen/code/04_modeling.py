"""
T017: Implement Multiple Linear Regression with 5-fold Cross-Validation.

This script fits a linear model to predict median Reaction Time (RT) from 
EEG band-power features (CLR-transformed).

Inputs:
  - data/processed/features.csv (from T015/T016)

Outputs:
  - data/interim/split_indices.json (CV fold assignments)
  - data/processed/model_results.json (R2, RMSE, coefficients, etc.)
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
import warnings

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    get_path, ensure_dirs, get_seed, set_global_seed, 
    get_cv_folds, get_all_band_names
)

warnings.filterwarnings('ignore')

def load_features() -> pd.DataFrame:
    """Load the processed features dataset."""
    features_path = get_path("processed") / "features.csv"
    if not features_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {features_path}. "
            "Please ensure T015/T016 have completed successfully."
        )
    df = pd.read_csv(features_path)
    
    # Validate required columns
    required_cols = ['participant_id', 'median_rt']
    band_cols = list(get_all_band_names())
    # Check if CLR columns exist (prefix 'clr_' or similar based on T015 output)
    # Assuming T015 outputs columns named exactly as bands but transformed, 
    # or prefixed. We look for the band names in the dataframe.
    available_bands = [c for c in band_cols if c in df.columns]
    
    if not available_bands:
        # Fallback: check for 'clr_' prefix if T015 added it
        available_bands = [c for c in df.columns if c.startswith('clr_')]
        if not available_bands:
            raise ValueError("No EEG band power columns found in features.csv.")
    
    return df, available_bands

def prepare_data(df: pd.DataFrame, feature_cols: list) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare X (features) and y (target).
    Returns: X_scaled, y, split_indices (dict)
    """
    # Filter out rows with missing values in features or target
    valid_mask = df[feature_cols + ['median_rt']].notna().all(axis=1)
    df_clean = df.loc[valid_mask].copy()
    
    if len(df_clean) < 10:
        raise ValueError(f"Insufficient data after cleaning: {len(df_clean)} samples.")

    X = df_clean[feature_cols].values
    y = df_clean['median_rt'].values
    ids = df_clean['participant_id'].values

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, ids

def fit_model_with_cv(X: np.ndarray, y: np.ndarray, n_splits: int, seed: int) -> Dict[str, Any]:
    """
    Perform 5-fold Cross-Validation for Multiple Linear Regression.
    
    Returns:
      dict containing:
        - fold_results: list of dicts with r2, rmse per fold
        - mean_r2, std_r2, mean_rmse, std_rmse
        - split_indices: mapping of fold -> indices (train/test)
        - final_model: fitted on full data (optional, for coefficients)
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    
    fold_results = []
    split_indices = {
        "train": [],
        "test": []
    }
    
    # Store indices for external use (e.g., permutation tests)
    # We store the actual indices into the original array
    # Note: Since we are returning indices relative to the *cleaned* array used here,
    # downstream tasks must be aware of this context or we store the mapping.
    # For simplicity in this task, we store the indices relative to the input X.
    
    # To make split_indices useful for T022 (Permutation), we need to store 
    # the indices of the TEST set for each fold.
    
    full_r2_scores = []
    full_rmse_scores = []
    
    # We also need to track which rows belong to which fold for the final model
    # However, the task asks for split_indices.json.
    # Let's structure it as: { "fold_0": {"train": [...], "test": [...]}, ... }
    
    fold_indices_map = {}

    for fold_idx, (train_index, test_index) in enumerate(kf.split(X)):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        fold_results.append({
            "fold": fold_idx,
            "r2": float(r2),
            "rmse": float(rmse),
            "n_train": int(len(train_index)),
            "n_test": int(len(test_index))
        })
        
        full_r2_scores.append(r2)
        full_rmse_scores.append(rmse)
        
        fold_indices_map[f"fold_{fold_idx}"] = {
            "train": train_index.tolist(),
            "test": test_index.tolist()
        }

    # Fit final model on full data for coefficient reporting
    final_model = LinearRegression()
    final_model.fit(X, y)
    
    # Calculate metrics on full data (just for reference, not CV)
    y_pred_full = final_model.predict(X)
    final_r2 = r2_score(y, y_pred_full)
    final_rmse = np.sqrt(mean_squared_error(y, y_pred_full))

    return {
        "fold_results": fold_results,
        "mean_r2": float(np.mean(full_r2_scores)),
        "std_r2": float(np.std(full_r2_scores)),
        "mean_rmse": float(np.mean(full_rmse_scores)),
        "std_rmse": float(np.std(full_rmse_scores)),
        "final_r2": float(final_r2),
        "final_rmse": float(final_rmse),
        "split_indices": fold_indices_map,
        "coefficients": {
            str(i): float(c) for i, c in enumerate(final_model.coef_)
        },
        "intercept": float(final_model.intercept_),
        "n_samples": int(len(X)),
        "n_features": int(X.shape[1])
    }

def save_results(results: Dict[str, Any], feature_names: list):
    """Save model results to JSON and split indices to separate JSON."""
    ensure_dirs()
    
    # Save full results
    results_path = get_path("processed") / "model_results.json"
    
    # Prepare a clean results dict for saving
    # We separate split_indices to its own file as per task spec
    split_indices = results.pop("split_indices")
    
    # Add feature names to coefficients for readability
    coef_dict = results["coefficients"]
    named_coefs = {feature_names[i]: coef_dict[str(i)] for i in range(len(feature_names))}
    
    output_results = {
        "model_type": "Multiple Linear Regression",
        "cv_folds": len(results["fold_results"]),
        "cv_mean_r2": results["mean_r2"],
        "cv_std_r2": results["std_r2"],
        "cv_mean_rmse": results["mean_rmse"],
        "cv_std_rmse": results["std_rmse"],
        "full_data_r2": results["final_r2"],
        "full_data_rmse": results["final_rmse"],
        "intercept": results["intercept"],
        "coefficients": named_coefs,
        "n_samples": results["n_samples"],
        "n_features": results["n_features"],
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(results_path, "w") as f:
        json.dump(output_results, f, indent=2)
    
    # Save split indices separately
    splits_path = get_path("interim") / "split_indices.json"
    with open(splits_path, "w") as f:
        json.dump(split_indices, f, indent=2)
        
    print(f"Results saved to {results_path}")
    print(f"Split indices saved to {splits_path}")

def main():
    parser = argparse.ArgumentParser(description="Fit MLR model with 5-fold CV")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()
    
    seed = args.seed if args.seed is not None else get_seed()
    set_global_seed(seed)
    
    print(f"Loading features...")
    df, feature_cols = load_features()
    print(f"Found {len(df)} samples and {len(feature_cols)} features.")
    
    print("Preparing data...")
    X, y, ids = prepare_data(df, feature_cols)
    
    n_folds = get_cv_folds()
    print(f"Fitting Multiple Linear Regression with {n_folds}-fold CV...")
    
    results = fit_model_with_cv(X, y, n_folds, seed)
    
    print(f"Cross-Validation Mean R2: {results['mean_r2']:.4f} (+/- {results['std_r2']:.4f})")
    print(f"Cross-Validation Mean RMSE: {results['mean_rmse']:.4f}")
    
    save_results(results, feature_cols)
    
    print("Task T017 completed successfully.")

if __name__ == "__main__":
    main()