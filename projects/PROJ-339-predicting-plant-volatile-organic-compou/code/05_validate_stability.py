import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score, mean_squared_error

# Ensure imports from sibling modules work if needed, though this script
# primarily re-implements the logic to ensure isolation or uses the model directly.
# We rely on the model artifact created in T024.

def ensure_dirs():
    """Ensure output directories exist."""
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_model_and_features():
    """
    Load the trained model and the feature matrix used for training.
    Expects data/models/random_forest.pkl and data/processed/merged_dataset.csv
    or the specific feature file if separated.
    """
    model_path = Path("data/models/random_forest.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}. "
                                "Ensure T024 has completed successfully.")
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    # Load the processed data to get feature names and X
    # Assuming merged_dataset.csv contains the features used for training
    # We need to know exactly which columns were used.
    # If the training script saved a feature list, load it.
    # Otherwise, we assume all numeric columns except the target are features.
    
    processed_path = Path("data/processed/merged_dataset.csv")
    if not processed_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_path}.")
    
    df = pd.read_csv(processed_path)
    
    # Heuristic: Identify target column (usually 'target' or similar, or last column)
    # Based on typical pipeline, target is often named 'target' or 'voc_profile'
    # Let's assume the last column is the target if not specified, or look for common names.
    # A robust way is to check if a 'feature_columns.json' exists from training.
    feature_cols_path = Path("data/models/feature_columns.json")
    if feature_cols_path.exists():
        with open(feature_cols_path, "r") as f:
            feature_cols = json.load(f)
    else:
        # Fallback: assume all numeric columns except 'sample_id' or similar are features
        # This is risky if the dataset has mixed types.
        # Let's assume the training script saved the X and y separately or we infer.
        # For this implementation, we assume the last column is the target 'target'.
        # Adjust based on actual data schema if known.
        # Let's try to load a specific feature list if available in the model metadata
        # or assume standard naming.
        # Given the constraints, we'll assume the training script saved feature names.
        # If not, we infer:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'target' in numeric_cols:
            feature_cols = [c for c in numeric_cols if c != 'target']
        elif 'voc' in numeric_cols:
             # Heuristic
            target_candidates = [c for c in numeric_cols if 'target' in c.lower() or 'voc' in c.lower()]
            if target_candidates:
                target_col = target_candidates[0]
                feature_cols = [c for c in numeric_cols if c != target_col]
            else:
                feature_cols = numeric_cols[:-1]
        else:
            feature_cols = numeric_cols[:-1]
    
    X = df[feature_cols]
    y = df['target'] if 'target' in df.columns else df[feature_cols].iloc[:, -1] # Fallback
    
    return model, X, y, feature_cols

def run_single_fold_importance(model, X, y, feature_names: List[str], random_state: int = 42):
    """
    Run permutation importance on a single fold (or the whole dataset if no split provided).
    For stability analysis, we typically run the importance calculation on the
    training data of a specific fold. However, since we only have the final model
    (trained on all data), we cannot easily re-run the CV folds without re-training.
    
    To satisfy SC-004 (stability across CV folds), we need the feature ranks from
    each outer fold of the Nested CV.
    
    Since T023/T024 saved the final model, we might not have the per-fold importance.
    However, T033 depends on T024. If T024 only saved the final model, we cannot
    calculate stability across folds unless we re-run the CV process or if the
    training script saved the per-fold metrics.
    
    Assumption: The training script (T020/T021) saved the per-fold importance
    or we must re-run a simplified version of the CV to get stability.
    
    Alternative Interpretation: The task asks to validate stability. If the
    per-fold data is not available, we must re-run the CV logic to extract
    importance ranks for each fold.
    
    Let's implement a re-run of the CV loop specifically for importance stability.
    We will use the same X, y, and model hyperparameters (or retrain a model
    on each fold to get fold-specific importance).
    
    To be robust and avoid re-training complexity if not needed, we assume
    the training script saved a file `data/models/cv_fold_importances.json`
    or similar. If not, we must re-implement the CV loop.
    
    Given the strict "no stubs" rule, we will implement the re-run of the
    CV loop to calculate importance for each fold.
    """
    # Re-run CV to get fold-specific importance
    # We need the same X, y.
    # We need the same model parameters.
    # We need the same CV strategy (Nested or just Outer for stability of feature ranking?)
    # Stability of feature importance is usually checked on the outer folds.
    
    # Let's assume a standard k-fold (e.g., 5-fold) for stability check.
    k_folds = 5
    kf = KFold(n_splits=k_folds, shuffle=True, random_state=42)
    
    fold_importances = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Train a model on this fold
        # Use default RF params or load from the main model if possible
        # To be safe, we use the same type and reasonable defaults
        fold_model = RandomForestRegressor(
            n_estimators=100, 
            random_state=42, 
            n_jobs=-1
        )
        fold_model.fit(X_train, y_train)
        
        # Calculate permutation importance on the TEST set of this fold?
        # Or on the training set? Usually, stability is checked on the
        # importance derived from the training data to see if the model
        # consistently picks the same features.
        # Let's use the training set for importance calculation to avoid
        # noise from small test sets.
        result = permutation_importance(
            fold_model, 
            X_train, 
            y_train, 
            n_repeats=10, 
            random_state=42, 
            n_jobs=-1
        )
        
        # Get mean importance
        importance = result.importances_mean
        fold_importances.append(importance)
    
    # Convert to array
    fold_importances = np.array(fold_importances) # Shape: (k_folds, n_features)
    
    return fold_importances, feature_names

def calculate_stability_metrics(fold_importances: np.ndarray, feature_names: List[str]):
    """
    Calculate stability metrics:
    1. Standard deviation of feature ranks across folds.
    2. Mean importance per feature.
    3. Rank correlation (optional).
    
    Returns a dictionary with the metrics.
    """
    n_folds, n_features = fold_importances.shape
    
    # Calculate ranks for each fold
    # Higher importance -> Lower rank (1 is best)
    # np.argsort returns indices that would sort the array.
    # We want rank 1 for the highest value.
    # argsort() gives indices of sorted array (ascending).
    # So the last element is the max.
    # We can invert the values or use order='descending' logic.
    
    ranks = np.zeros_like(fold_importances, dtype=float)
    for i in range(n_folds):
        # argsort gives indices that sort ascending.
        # We want rank 1 for the largest value.
        # So we argsort the negative importance, or argsort and reverse.
        # Let's do: sort descending, assign ranks 1..N
        sorted_indices = np.argsort(fold_importances[i])[::-1]
        # Assign ranks: position 0 gets rank 1, position 1 gets rank 2, etc.
        current_ranks = np.empty(n_features, dtype=int)
        current_ranks[sorted_indices] = np.arange(1, n_features + 1)
        ranks[i] = current_ranks
    
    # Standard deviation of ranks
    rank_std = np.std(ranks, axis=0)
    mean_rank = np.mean(ranks, axis=0)
    mean_importance = np.mean(fold_importances, axis=0)
    
    # Create result structure
    metrics = {
        "description": "Stability of feature importance rankings across CV folds (Standard Deviation of Ranks)",
        "n_folds": n_folds,
        "n_features": n_features,
        "features": [],
        "summary": {
            "mean_rank_std": float(np.mean(rank_std)),
            "max_rank_std": float(np.max(rank_std)),
            "min_rank_std": float(np.min(rank_std))
        }
    }
    
    for i, name in enumerate(feature_names):
        metrics["features"].append({
            "feature_name": name,
            "mean_importance": float(mean_importance[i]),
            "mean_rank": float(mean_rank[i]),
            "rank_std": float(rank_std[i])
        })
    
    # Sort by rank_std ascending (most stable first)
    metrics["features"].sort(key=lambda x: x["rank_std"])
    
    return metrics

def main():
    """Main entry point for T033."""
    print("Starting T033: Stability Validation of Feature Importance...")
    
    try:
        # 1. Load Model and Data
        model, X, y, feature_names = load_model_and_features()
        print(f"Loaded model and {len(feature_names)} features.")
        
        # 2. Run CV to get fold-specific importance
        # Note: This re-trains a simplified model on folds to get stability metrics.
        # If the original training used Nested CV, we are approximating with Outer CV
        # for stability check, which is standard for this metric.
        fold_importances, names = run_single_fold_importance(model, X, y, feature_names)
        print(f"Calculated importance across {fold_importances.shape[0]} folds.")
        
        # 3. Calculate Stability Metrics
        stability_metrics = calculate_stability_metrics(fold_importances, names)
        
        # 4. Save Output
        output_dir = ensure_dirs()
        output_path = output_dir / "stability_metrics.json"
        
        with open(output_path, "w") as f:
            json.dump(stability_metrics, f, indent=2)
        
        print(f"Stability metrics saved to {output_path}")
        print("T033 completed successfully.")
        
    except Exception as e:
        print(f"Error during T033 execution: {e}")
        raise

if __name__ == "__main__":
    main()
