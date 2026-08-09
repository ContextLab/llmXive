import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Any
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.inspection import permutation_importance
import warnings

# Suppress specific sklearn warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)

# Add project root to path if running as script
if __name__ == "__main__" and "code" not in sys.path[0]:
    sys.path.insert(0, str(Path(__file__).parent))

def load_model_and_features():
    """
    Load the trained Random Forest model and the original feature names.
    
    Returns:
        Tuple[RandomForestRegressor, List[str]]: The model and feature names.
    """
    model_path = Path("data/models/random_forest.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}. Run T024 first.")
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    feature_names = model_data['feature_names']
    return model, feature_names

def run_single_fold_importance(
    X_train: pd.DataFrame, 
    y_train: pd.Series, 
    model: RandomForestRegressor, 
    n_repeats: int = 10,
    random_state: int = 42
) -> List[str]:
    """
    Run permutation importance on a single fold and return ranked feature names.
    
    Args:
        X_train: Training features for this fold.
        y_train: Training targets for this fold.
        model: The fitted model to evaluate.
        n_repeats: Number of permutation repeats.
        random_state: Random seed for reproducibility.
    
    Returns:
        List[str]: Feature names sorted by importance (highest to lowest).
    """
    # Calculate permutation importance
    # We use the trained model on the training data for this specific fold
    # to simulate the fold-specific importance.
    result = permutation_importance(
        model, X_train, y_train, 
        n_repeats=n_repeats, 
        random_state=random_state,
        n_jobs=1
    )
    
    # Get importance scores
    importances = result.importances_mean
    
    # Create a list of (feature_name, importance)
    feature_importance_pairs = list(zip(X_train.columns, importances))
    
    # Sort by importance descending
    feature_importance_pairs.sort(key=lambda x: x[1], reverse=True)
    
    # Extract just the feature names in order
    ranked_features = [feat for feat, _ in feature_importance_pairs]
    
    return ranked_features

def calculate_stability_metrics(
    ranked_features_list: List[List[str]],
    feature_names: List[str]
) -> Dict[str, Any]:
    """
    Calculate stability metrics (standard deviation of ranks) across folds.
    
    Args:
        ranked_features_list: List of ranked feature lists, one per fold.
        feature_names: Complete list of all features.
    
    Returns:
        Dict containing stability metrics.
    """
    n_folds = len(ranked_features_list)
    n_features = len(feature_names)
    
    if n_folds == 0:
        raise ValueError("No folds processed. Cannot calculate stability.")
    
    # Create a rank matrix: rows=folds, cols=features
    # Value = rank position (0-based) of the feature in that fold
    rank_matrix = np.full((n_folds, n_features), np.nan)
    
    feature_to_idx = {f: i for i, f in enumerate(feature_names)}
    
    for fold_idx, ranked_list in enumerate(ranked_features_list):
        for rank, feature_name in enumerate(ranked_list):
            if feature_name in feature_to_idx:
                col_idx = feature_to_idx[feature_name]
                rank_matrix[fold_idx, col_idx] = rank
    
    # Calculate mean rank and std rank for each feature
    mean_ranks = np.nanmean(rank_matrix, axis=0)
    std_ranks = np.nanstd(rank_matrix, axis=0)
    
    # Build results
    stability_data = []
    for i, feature in enumerate(feature_names):
        stability_data.append({
            "feature": feature,
            "mean_rank": float(mean_ranks[i]) if not np.isnan(mean_ranks[i]) else None,
            "std_rank": float(std_ranks[i]) if not np.isnan(std_ranks[i]) else None,
            "n_folds_present": int(np.sum(~np.isnan(rank_matrix[:, i])))
        })
    
    # Sort by std_rank ascending (most stable first)
    stability_data.sort(key=lambda x: x["std_rank"] if x["std_rank"] is not None else float('inf'))
    
    # Calculate overall stability score (average std rank across all features)
    valid_stds = [d["std_rank"] for d in stability_data if d["std_rank"] is not None]
    overall_std_rank = float(np.mean(valid_stds)) if valid_stds else None
    
    return {
        "n_folds_analyzed": n_folds,
        "n_features": n_features,
        "overall_std_rank": overall_std_rank,
        "feature_stability": stability_data
    }

def main():
    """
    Main entry point for T033: Validate stability of feature importance rankings.
    
    This function:
    1. Loads the trained model and features.
    2. Loads the processed dataset.
    3. Simulates K-Fold splits (using the same K as training) to get fold-specific importance.
    4. Calculates rank stability metrics.
    5. Saves results to data/results/stability_metrics.json.
    """
    print("Starting T033: Stability Validation of Feature Importance Rankings")
    
    # Ensure output directory exists
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load model and features
    print("Loading model and features...")
    model, feature_names = load_model_and_features()
    
    # Load the processed dataset used for training
    # We need to re-extract the X and y to simulate folds
    merged_path = Path("data/processed/merged_dataset.csv")
    if not merged_path.exists():
        # Try synthetic data path if merged dataset not found
        merged_path = Path("data/processed/synthetic_merged_dataset.csv")
    
    if not merged_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {merged_path}. Run T017 first.")
    
    df = pd.read_csv(merged_path)
    
    # Identify target column (usually the VOC column)
    # Based on typical pipeline, the target is likely the last numeric column or named specifically
    # We'll assume the target is 'VOC_emission' or similar, or infer from context
    # For robustness, let's look for a column that isn't 'sample_id' and is numeric
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Heuristic: The target is usually distinct. If we have a known target name, use it.
    # Otherwise, assume the last numeric column is the target (common in these pipelines)
    # A safer approach: check for common VOC column names
    target_candidates = ['VOC_emission', 'volatile_emission', 'target', 'emission_rate']
    target_col = None
    for candidate in target_candidates:
        if candidate in df.columns:
            target_col = candidate
            break
    
    if not target_col and len(numeric_cols) > 0:
        target_col = numeric_cols[-1]
    
    if not target_col:
        raise ValueError("Could not identify target column in merged dataset.")
    
    X = df.drop(columns=[target_col, 'sample_id'], errors='ignore')
    y = df[target_col]
    
    # Ensure X has the correct feature names (subset of loaded feature_names if needed)
    # The model was trained on a specific set of features. We must align.
    available_features = [f for f in feature_names if f in X.columns]
    if len(available_features) == 0:
        raise ValueError("No matching features found between model and dataset.")
    
    X = X[available_features]
    
    # Define K-Fold parameters (matching training)
    n_splits = 5
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    ranked_features_list = []
    
    print(f"Running permutation importance on {n_splits} folds...")
    
    for fold_idx, (train_idx, _) in enumerate(kfold.split(X)):
        X_fold = X.iloc[train_idx]
        y_fold = y.iloc[train_idx]
        
        # We need a model trained on this specific fold to get fold-specific importance
        # However, retraining a full RF for every fold just for stability check is expensive.
        # Alternative: Use the global model but evaluate importance on the fold-specific data distribution?
        # The requirement is "stability ... across CV folds".
        # Strict interpretation: The importance ranking should be derived from models trained on each fold.
        # Since we don't have the fold-specific models saved, we must retrain a small RF on the fold data.
        
        # Train a quick RF on this fold
        fold_model = RandomForestRegressor(
            n_estimators=50, # Smaller for speed
            max_depth=5,
            random_state=42,
            n_jobs=1
        )
        fold_model.fit(X_fold, y_fold)
        
        # Get ranking
        ranking = run_single_fold_importance(
            X_fold, y_fold, fold_model, n_repeats=5, random_state=42
        )
        
        ranked_features_list.append(ranking)
        print(f"  Fold {fold_idx + 1}/{n_splits} completed.")
    
    # Calculate stability metrics
    print("Calculating stability metrics...")
    stability_results = calculate_stability_metrics(ranked_features_list, available_features)
    
    # Save results
    output_path = output_dir / "stability_metrics.json"
    with open(output_path, 'w') as f:
        json.dump(stability_results, f, indent=2)
    
    print(f"Stability metrics saved to {output_path}")
    print(f"Overall Rank Stability (Std Dev): {stability_results['overall_std_rank']:.4f}")
    
    return stability_results

if __name__ == "__main__":
    main()
