import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from config import get_path, ensure_dirs, get_cv_folds, set_global_seed, get_seed
import warnings

# Suppress specific warnings for cleaner logs if needed
warnings.filterwarnings('ignore', category=FutureWarning)

def load_features(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the features DataFrame from the processed features file.
    Handles chunked loading if the file is extremely large, though typically
    this fits in memory.
    """
    if input_path is None:
        input_path = get_path("processed", "features.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Features file not found at {input_path}")
    
    # Check file size to decide on chunking strategy (threshold ~100MB)
    file_size = os.path.getsize(input_path)
    if file_size > 100 * 1024 * 1024:
        # Chunked loading for very large files
        chunks = []
        for chunk in pd.read_csv(input_path, chunksize=10000):
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
    else:
        df = pd.read_csv(input_path)
    
    return df

def prepare_data(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare X (features) and y (target) arrays.
    Returns X, y, and participant_ids for tracking.
    """
    # Identify target column (median_rt)
    if 'median_rt' not in df.columns:
        raise ValueError("DataFrame must contain 'median_rt' column as target.")
    
    # Filter for valid rows (no NaNs in features or target)
    valid_mask = df[feature_cols + ['median_rt']].notna().all(axis=1)
    df_valid = df[valid_mask]
    
    if df_valid.empty:
        raise ValueError("No valid data rows after removing NaNs.")
    
    X = df_valid[feature_cols].values
    y = df_valid['median_rt'].values
    participant_ids = df_valid['participant_id'].values if 'participant_id' in df_valid.columns else None
    
    return X, y, participant_ids

def fit_model_with_cv(X: np.ndarray, y: np.ndarray, n_folds: int = 5, random_state: int = 42) -> Dict[str, Any]:
    """
    Fit Multiple Linear Regression with K-Fold Cross-Validation.
    Implements chunked processing logic by iterating over folds explicitly
    to manage memory if X is large (though sklearn handles this internally,
    we structure it for clarity and potential extension).
    
    Returns a dictionary containing:
      - r2_scores: list of R2 per fold
      - rmse_scores: list of RMSE per fold
      - mean_r2: average R2
      - mean_rmse: average RMSE
      - fold_models: list of fitted models (optional, can be memory heavy)
      - split_indices: dictionary of fold indices for reproducibility
    """
    if X.shape[0] < n_folds:
        raise ValueError(f"Sample size ({X.shape[0]}) must be greater than number of folds ({n_folds}).")
    
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    r2_scores = []
    rmse_scores = []
    fold_splits = [] # Store indices for reproducibility
    
    # Iterate through folds
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Store indices for this fold
        fold_splits.append({
            "fold": fold_idx,
            "train_indices": train_idx.tolist(),
            "test_indices": test_idx.tolist()
        })
        
        # Fit model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Predict and evaluate
        y_pred = model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
        
        # Optional: Store model if needed, but for memory efficiency in chunked processing,
        # we might skip storing all models if not strictly required.
        # Here we just store metrics.
    
    results = {
        "r2_scores": r2_scores,
        "rmse_scores": rmse_scores,
        "mean_r2": float(np.mean(r2_scores)),
        "std_r2": float(np.std(r2_scores)),
        "mean_rmse": float(np.mean(rmse_scores)),
        "std_rmse": float(np.std(rmse_scores)),
        "n_folds": n_folds,
        "n_samples": X.shape[0],
        "n_features": X.shape[1],
        "split_indices": fold_splits
    }
    
    return results

def save_results(results: Dict[str, Any], split_indices: List[Dict], output_results_path: str, output_splits_path: str):
    """
    Save model results and split indices to JSON files.
    """
    # Ensure directories exist
    ensure_dirs(Path(output_results_path).parent)
    ensure_dirs(Path(output_splits_path).parent)
    
    # Prepare output structure
    results_output = {
        "model_type": "LinearRegression",
        "cv_folds": results["n_folds"],
        "mean_r2": results["mean_r2"],
        "std_r2": results["std_r2"],
        "mean_rmse": results["mean_rmse"],
        "std_rmse": results["std_rmse"],
        "r2_per_fold": results["r2_scores"],
        "rmse_per_fold": results["rmse_scores"],
        "n_samples": results["n_samples"],
        "n_features": results["n_features"],
        "status": "success"
    }
    
    # Save model results
    with open(output_results_path, 'w') as f:
        json.dump(results_output, f, indent=2)
    
    # Save split indices
    with open(output_splits_path, 'w') as f:
        json.dump(split_indices, f, indent=2)

def main():
    """
    Main entry point for T017: Implement Multiple Linear Regression with 5-fold CV.
    """
    parser = argparse.ArgumentParser(description="Fit Multiple Linear Regression with CV")
    parser.add_argument("--input", type=str, default=None, help="Path to features CSV")
    parser.add_argument("--output-results", type=str, default=None, help="Path for model_results.json")
    parser.add_argument("--output-splits", type=str, default=None, help="Path for split_indices.json")
    parser.add_argument("--folds", type=int, default=None, help="Number of CV folds (default from config)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()

    # Set global seed
    seed = args.seed if args.seed is not None else get_seed()
    set_global_seed(seed)

    # Determine paths
    input_path = args.input if args.input else get_path("processed", "features.csv")
    output_results_path = args.output_results if args.output_results else get_path("processed", "model_results.json")
    output_splits_path = args.output_splits if args.output_splits else get_path("interim", "split_indices.json")
    
    n_folds = args.folds if args.folds is not None else get_cv_folds()

    print(f"Loading features from {input_path}...")
    try:
        df = load_features(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Identify feature columns (exclude participant_id and median_rt)
    exclude_cols = ['participant_id', 'median_rt']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found. Check input file schema.")
    
    print(f"Found {len(feature_cols)} feature columns: {feature_cols}")
    print(f"Preparing data for modeling...")

    try:
        X, y, participant_ids = prepare_data(df, feature_cols)
    except ValueError as e:
        print(f"Error preparing data: {e}")
        sys.exit(1)

    print(f"Data prepared: X shape {X.shape}, y shape {y.shape}")
    print(f"Running {n_folds}-fold Cross-Validation...")

    try:
        results = fit_model_with_cv(X, y, n_folds=n_folds, random_state=seed)
    except Exception as e:
        print(f"Error during model fitting: {e}")
        sys.exit(1)

    print(f"Model fitting complete.")
    print(f"Mean R2: {results['mean_r2']:.4f} (+/- {results['std_r2']:.4f})")
    print(f"Mean RMSE: {results['mean_rmse']:.4f}")

    # Save outputs
    try:
        save_results(results, results['split_indices'], output_results_path, output_splits_path)
        print(f"Results saved to {output_results_path}")
        print(f"Split indices saved to {output_splits_path}")
    except Exception as e:
        print(f"Error saving results: {e}")
        sys.exit(1)

    print("Task T017 completed successfully.")

if __name__ == "__main__":
    main()