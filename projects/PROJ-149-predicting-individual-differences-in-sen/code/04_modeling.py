import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
import config
from utils.stats_helpers import calculate_sample_size_for_r2

# Ensure paths are resolved relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG = config.load_config()

def load_features(filepath: str) -> pd.DataFrame:
    """
    Load the processed features dataset.
    Expects a CSV with 'participant_id', 'median_rt', and band power columns.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Feature file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Required columns check
    required_cols = ['participant_id', 'median_rt']
    # Identify band columns (delta, theta, alpha, low_beta, high_beta, gamma, etc.)
    # Based on T015 output, we expect relative/CLR transformed bands
    band_cols = [c for c in df.columns if any(b in c.lower() for b in ['delta', 'theta', 'alpha', 'beta', 'gamma'])]
    
    if not all(c in df.columns for c in required_cols):
        raise ValueError(f"Missing required columns: {required_cols}")
    if len(band_cols) == 0:
        raise ValueError("No band power columns found in features file.")
    
    return df, band_cols

def prepare_data(df: pd.DataFrame, feature_cols: List[str], target_col: str = 'median_rt') -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare X (features) and y (target) arrays.
    Handles missing values by dropping rows (strict requirement: no nulls allowed).
    """
    # Drop rows with any NaN in features or target
    clean_df = df.dropna(subset=feature_cols + [target_col])
    
    if clean_df.empty:
        raise ValueError("No valid data rows remaining after dropping NaNs.")
    
    X = clean_df[feature_cols].values
    y = clean_df[target_col].values
    
    return X, y, clean_df['participant_id'].values

def fit_model_with_cv(X: np.ndarray, y: np.ndarray, n_folds: int = 5, random_state: int = 42) -> Dict[str, Any]:
    """
    Fit Multiple Linear Regression with K-Fold Cross-Validation.
    Returns metrics and split indices.
    """
    # Initialize KFold
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    # Store split indices for reproducibility/debugging (T022 dependency)
    split_indices = {
        "folds": []
    }
    
    # Store fold scores
    fold_scores = []
    fold_models = []
    
    # Scale features for consistency (though OLS is scale-invariant for R2, good practice)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Store indices (relative to the clean_df order)
        split_indices["folds"].append({
            "fold": fold_idx + 1,
            "train_indices": train_idx.tolist(),
            "test_indices": test_idx.tolist()
        })
        
        # Fit model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Predict and score
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        fold_scores.append({"fold": fold_idx + 1, "r2": r2, "rmse": rmse})
        fold_models.append({
            "coefficients": model.coef_.tolist(),
            "intercept": float(model.intercept_)
        })
    
    # Aggregate metrics
    mean_r2 = float(np.mean([f["r2"] for f in fold_scores]))
    std_r2 = float(np.std([f["r2"] for f in fold_scores]))
    mean_rmse = float(np.mean([f["rmse"] for f in fold_scores]))
    
    # Fit final model on full data for coefficient reporting
    final_model = LinearRegression()
    final_model.fit(X_scaled, y)
    
    results = {
        "model_type": "Multiple Linear Regression",
        "cv_method": "K-Fold",
        "n_folds": n_folds,
        "n_samples": len(y),
        "n_features": X.shape[1],
        "metrics": {
            "mean_r2": mean_r2,
            "std_r2": std_r2,
            "mean_rmse": mean_rmse,
            "adjusted_r2": float(1 - (1 - mean_r2) * (len(y) - 1) / (len(y) - X.shape[1] - 1)) if len(y) > X.shape[1] + 1 else None
        },
        "fold_results": fold_scores,
        "final_model": {
            "coefficients": final_model.coef_.tolist(),
            "intercept": float(final_model.intercept_)
        },
        "split_indices": split_indices
    }
    
    return results

def save_results(results: Dict[str, Any], output_path: str, split_path: str):
    """
    Save model results and split indices to JSON files.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save main results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save split indices separately if requested (T022 dependency)
    if split_path:
        os.makedirs(os.path.dirname(split_path), exist_ok=True)
        with open(split_path, 'w') as f:
            json.dump(results["split_indices"], f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Fit predictive models on EEG features.")
    parser.add_argument("--input", type=str, default="data/processed/features.csv",
                        help="Path to input features CSV")
    parser.add_argument("--output", type=str, default="data/processed/model_results.json",
                        help="Path to output model results JSON")
    parser.add_argument("--splits", type=str, default="data/interim/split_indices.json",
                        help="Path to save split indices JSON")
    parser.add_argument("--folds", type=int, default=5,
                        help="Number of CV folds")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set global seed if provided
    if args.seed is not None:
        config.set_global_seed(args.seed)
        seed = args.seed
    else:
        seed = config.get_seed()
    
    print(f"Loading features from {args.input}...")
    try:
        df, band_cols = load_features(args.input)
    except Exception as e:
        print(f"ERROR: Failed to load features: {e}")
        sys.exit(1)
    
    print(f"Found {len(band_cols)} band features: {band_cols}")
    
    print("Preparing data...")
    try:
        X, y, pids = prepare_data(df, band_cols, target_col='median_rt')
    except Exception as e:
        print(f"ERROR: Failed to prepare data: {e}")
        sys.exit(1)
    
    print(f"Data shape: {X.shape}, Target shape: {y.shape}")
    
    print(f"Fitting Multiple Linear Regression with {args.folds}-fold CV...")
    try:
        results = fit_model_with_cv(X, y, n_folds=args.folds, random_state=seed)
    except Exception as e:
        print(f"ERROR: Model fitting failed: {e}")
        sys.exit(1)
    
    print(f"Saving results to {args.output}...")
    try:
        save_results(results, args.output, args.splits)
    except Exception as e:
        print(f"ERROR: Failed to save results: {e}")
        sys.exit(1)
    
    print("Modeling complete.")
    print(f"Mean R²: {results['metrics']['mean_r2']:.4f} (+/- {results['metrics']['std_r2']:.4f})")
    print(f"Adjusted R²: {results['metrics']['adjusted_r2']:.4f}")
    print(f"Split indices saved to {args.splits}")

if __name__ == "__main__":
    main()
