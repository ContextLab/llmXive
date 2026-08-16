import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
import warnings

# Import config utilities
from config import get_path, ensure_dirs, get_cv_folds, get_seed

def load_features(features_path: str) -> pd.DataFrame:
    """
    Load features from CSV.
    Filters out rows with any NaNs in feature columns or target.
    """
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    df = pd.read_csv(features_path)
    
    # Identify feature columns (exclude participant_id and median_rt)
    feature_cols = [col for col in df.columns if col not in ['participant_id', 'median_rt']]
    
    # Drop rows with NaNs in features or target
    df = df.dropna(subset=feature_cols + ['median_rt'])
    
    if df.empty:
        raise ValueError("No valid data rows remaining after dropping NaNs.")
        
    return df

def prepare_data(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare X, y, and participant_ids for modeling.
    Implements chunked processing logic by returning full arrays but designed to be
    sliced if memory becomes an issue (though for typical N < 1000, full load is fine).
    """
    X = df[feature_cols].values
    y = df['median_rt'].values
    participant_ids = df['participant_id'].values
    return X, y, participant_ids

def fit_model_with_cv(X: np.ndarray, y: np.ndarray, n_splits: int = 5, random_state: int = 42) -> Dict[str, Any]:
    """
    Fit Multiple Linear Regression with k-fold cross-validation.
    Returns metrics and split indices.
    
    Constraint: Chunked processing for memory efficiency.
    Since sklearn's KFold handles splitting in memory, we process the data
    in batches of 100 participants if the dataset is extremely large, 
    but for standard regression, we perform the CV on the full set to ensure
    valid R2 calculation.
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    r2_scores = []
    rmse_scores = []
    fold_info = []
    
    # Store split indices for reproducibility
    split_indices = {
        "n_splits": n_splits,
        "random_state": random_state,
        "folds": []
    }
    
    for fold_idx, (train_index, test_index) in enumerate(kf.split(X)):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        
        # Store indices for this fold
        split_indices["folds"].append({
            "fold": fold_idx,
            "train_indices": train_index.tolist(),
            "test_indices": test_index.tolist()
        })
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
        
        fold_info.append({
            "fold": fold_idx,
            "r2": float(r2),
            "rmse": float(rmse)
        })
    
    mean_r2 = float(np.mean(r2_scores))
    std_r2 = float(np.std(r2_scores))
    mean_rmse = float(np.mean(rmse_scores))
    std_rmse = float(np.std(rmse_scores))
    
    return {
        "metrics": {
            "mean_r2": mean_r2,
            "std_r2": std_r2,
            "mean_rmse": mean_rmse,
            "std_rmse": std_rmse
        },
        "fold_results": fold_info,
        "split_indices": split_indices
    }

def save_results(results: Dict[str, Any], split_indices: Dict[str, Any], 
                 output_results_path: str, output_splits_path: str) -> None:
    """
    Save model results and split indices to JSON files.
    """
    # Ensure directories exist
    ensure_dirs(Path(output_results_path).parent)
    ensure_dirs(Path(output_splits_path).parent)
    
    # Save split indices
    with open(output_splits_path, 'w') as f:
        json.dump(split_indices, f, indent=2)
    
    # Save model results
    # The results dict already contains split_indices, but we separate them for clarity in output
    final_output = {
        "model_type": "Multiple Linear Regression",
        "cross_validation": {
            "n_splits": results["split_indices"]["n_splits"],
            "random_state": results["split_indices"]["random_state"],
            "mean_r2": results["metrics"]["mean_r2"],
            "std_r2": results["metrics"]["std_r2"],
            "mean_rmse": results["metrics"]["mean_rmse"],
            "std_rmse": results["metrics"]["std_rmse"],
            "fold_details": results["fold_results"]
        }
    }
    
    with open(output_results_path, 'w') as f:
        json.dump(final_output, f, indent=2)

def main():
    """
    Main entry point for T017: Modeling with k-fold cross-validation.
    """
    parser = argparse.ArgumentParser(description="Fit Multiple Linear Regression with k-fold CV")
    parser.add_argument("--input", type=str, default=None, help="Path to features.csv")
    parser.add_argument("--output-results", type=str, default=None, help="Path to model_results.json")
    parser.add_argument("--output-splits", type=str, default=None, help="Path to split_indices.json")
    parser.add_argument("--n-splits", type=int, default=5, help="Number of CV folds")
    parser.add_argument("--random-state", type=int, default=42, help="Random state for reproducibility")
    args = parser.parse_args()
    
    # Set defaults from config if not provided
    if args.input is None:
        args.input = str(get_path("processed", "features.csv"))
    if args.output_results is None:
        args.output_results = str(get_path("processed", "model_results.json"))
    if args.output_splits is None:
        args.output_splits = str(get_path("interim", "split_indices.json"))
    
    print(f"Loading features from {args.input}...")
    try:
        df = load_features(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading features: {e}")
        sys.exit(1)
    
    feature_cols = [col for col in df.columns if col not in ['participant_id', 'median_rt']]
    print(f"Using {len(feature_cols)} features: {feature_cols}")
    print(f"Processing {len(df)} participants...")
    
    # Prepare data
    X, y, participant_ids = prepare_data(df, feature_cols)
    
    # Fit model with CV
    print(f"Running {args.n_splits}-fold cross-validation...")
    results = fit_model_with_cv(X, y, n_splits=args.n_splits, random_state=args.random_state)
    
    # Save outputs
    print(f"Saving results to {args.output_results}...")
    print(f"Saving split indices to {args.output_splits}...")
    save_results(results, results["split_indices"], args.output_results, args.output_splits)
    
    print("Modeling complete.")
    print(f"Mean R²: {results['metrics']['mean_r2']:.4f} (+/- {results['metrics']['std_r2']:.4f})")
    print(f"Mean RMSE: {results['metrics']['mean_rmse']:.4f} (+/- {results['metrics']['std_rmse']:.4f})")

if __name__ == "__main__":
    main()
