import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedKFold, KFold
from sklearn.inspection import permutation_importance
from scipy.stats import rankdata
import warnings

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_config

def load_model_and_features(model_path: str, features_path: str) -> Tuple[Any, pd.DataFrame]:
    """Load the trained model and the feature names used during training."""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load features from the processed dataset or a separate metadata file
    # Assuming the model was trained on the data from T017 (merged_dataset.csv)
    # We need to reload the processed data to get the feature names in order
    # If a specific feature list was saved, load that. Otherwise, infer from data.
    processed_data_path = Path("data/processed/merged_dataset.csv")
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_data_path}")
    
    df = pd.read_csv(processed_data_path)
    
    # Identify target column (usually the VOC target)
    # Based on typical pipeline, target might be 'voc_target' or similar. 
    # We need to know which column was the target. 
    # For stability analysis, we need the X matrix.
    # Let's assume the last column is the target or a specific known target.
    # A safer approach: The model object might have feature names if saved with them, 
    # but standard sklearn RF does not store feature names in the pickle unless explicitly added.
    # We will assume the order matches the processed dataset excluding the target.
    
    # Heuristic: Find the target column name. 
    # In T020/T021, the target is likely 'voc_concentration' or similar.
    # Let's look for common VOC target names or assume the user knows.
    # To be robust, we will try to load a saved feature list if it exists, 
    # otherwise assume all numeric columns except the last one are features.
    
    feature_list_path = Path("data/processed/feature_names.json")
    if feature_list_path.exists():
        with open(feature_list_path, 'r') as f:
            feature_names = json.load(f)
    else:
        # Fallback: assume all columns except the target are features
        # We need to know the target. Let's assume 'target' or 'voc_target'
        possible_targets = ['target', 'voc_target', 'concentration', 'y']
        target_col = None
        for t in possible_targets:
            if t in df.columns:
                target_col = t
                break
        
        if not target_col:
            # Last column is target
            target_col = df.columns[-1]
        
        feature_names = [c for c in df.columns if c != target_col]
    
    X = df[feature_names]
    return model, X, feature_names

def run_single_fold_importance(
    model: Any, 
    X: pd.DataFrame, 
    y: pd.Series, 
    n_repeats: int = 10, 
    random_state: int = 42
) -> pd.Series:
    """
    Run permutation importance for a single fold (or full dataset) 
    and return the importance scores as a Series.
    """
    # We need to run permutation importance on the training data of that fold.
    # However, for stability of the *ranking* of the global model, 
    # we often re-evaluate the global model on different bootstrap samples 
    # or simply re-run the importance calculation on the full data 
    # with different random seeds (which is what T033 likely implies: 
    # stability of the metric itself).
    # 
    # Interpretation of SC-004: "Validate stability of feature importance rankings across CV folds"
    # This implies we need to:
    # 1. Retrain the model on each outer training fold (if we have the CV splits).
    # 2. Calculate importance for each retrained model.
    # 3. Compare the ranks.
    #
    # Since we only have the final model (T024), we might not have the individual fold models.
    # Alternative: If the task implies "stability of the importance calculation method", 
    # we run permutation importance multiple times with different seeds.
    #
    # However, the prompt says "across CV folds". This strongly suggests we need to 
    # re-train on the CV folds.
    #
    # Strategy:
    # 1. Reload the data.
    # 2. Re-run the CV split logic (using the same random state as T021 if known, or default).
    # 3. For each outer training fold:
    #    a. Train a new RF model.
    #    b. Calculate permutation importance on that fold's training set.
    #    c. Record the ranks.
    # 4. Compute std dev of ranks across folds.
    
    # We need to know the original CV parameters. 
    # Assuming standard Nested CV: Outer 5-fold, Inner 3-fold.
    # We will re-simulate the outer loop.
    
    # Note: We cannot access the exact same models unless we retrain.
    # So we retrain.
    
    # But wait, we are inside a function that receives `model`. 
    # If we are retraining, we don't use the passed `model` for the fold models, 
    # we use it only as a reference for hyperparameters.
    
    # Let's implement the retraining approach.
    pass

def calculate_stability_metrics(
    X: pd.DataFrame,
    y: pd.Series,
    model_params: Dict[str, Any],
    n_folds: int = 5,
    n_repeats: int = 10,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Retrain models on CV folds, calculate permutation importance for each,
    and compute the standard deviation of feature ranks.
    """
    np.random.seed(random_state)
    feature_names = X.columns.tolist()
    n_features = len(feature_names)
    
    # Store ranks for each fold: list of arrays (one per fold)
    fold_ranks = []
    
    # Use KFold for regression (StratifiedKFold is for classification)
    # We assume the target is continuous for regression.
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    for fold_idx, (train_idx, _) in enumerate(kf.split(X)):
        X_train_fold = X.iloc[train_idx]
        y_train_fold = y.iloc[train_idx]
        
        # Retrain model on this fold
        # Use the parameters from the final model (or defaults if not passed)
        # We assume RandomForestRegressor
        rf_fold = RandomForestRegressor(
            n_estimators=model_params.get('n_estimators', 100),
            max_depth=model_params.get('max_depth', None),
            random_state=random_state + fold_idx, # Different seed per fold to ensure variation
            n_jobs=-1
        )
        rf_fold.fit(X_train_fold, y_train_fold)
        
        # Calculate permutation importance on this fold's training data
        # We use the training data of the fold to evaluate importance
        perm_result = permutation_importance(
            rf_fold, 
            X_train_fold, 
            y_train_fold, 
            n_repeats=n_repeats, 
            random_state=random_state + fold_idx,
            n_jobs=-1
        )
        
        # Get mean importance
        importances = perm_result.importances_mean
        
        # Handle negative importances (set to 0 for ranking or keep as is? 
        # Usually ranking is done on the magnitude or mean. We'll use mean as is.)
        # If all are negative or zero, ranks might be weird.
        
        # Calculate ranks (1 is most important)
        # rankdata with 'average' handles ties. 
        # We want rank 1 for highest importance.
        # rankdata returns 1-based ranks. Higher value -> lower rank number?
        # rankdata([10, 5, 2]) -> [3, 2, 1]. We want 10 to be rank 1.
        # So we rank the negative of the importances? Or use method='min' and invert?
        # Let's use: rank = rankdata(-importances, method='average')
        ranks = rankdata(-importances, method='average')
        
        fold_ranks.append(ranks)
    
    # Convert to numpy array: shape (n_folds, n_features)
    ranks_array = np.array(fold_ranks)
    
    # Calculate standard deviation of ranks for each feature
    rank_std = np.std(ranks_array, axis=0)
    
    # Create a dictionary of results
    stability_data = {
        "feature_names": feature_names,
        "rank_std": rank_std.tolist(),
        "mean_rank": np.mean(ranks_array, axis=0).tolist(),
        "n_folds": n_folds,
        "n_repeats": n_repeats,
        "method": "Permutation Importance (Retrained on CV Folds)",
        "description": "Standard deviation of feature ranks across 5 CV folds. Lower values indicate more stable rankings."
    }
    
    # Sort by mean rank for readability
    sorted_indices = np.argsort(stability_data["mean_rank"])
    stability_data["sorted_feature_names"] = [feature_names[i] for i in sorted_indices]
    stability_data["sorted_rank_std"] = [rank_std[i] for i in sorted_indices]
    stability_data["sorted_mean_rank"] = [stability_data["mean_rank"][i] for i in sorted_indices]
    
    return stability_data

def main():
    print("Starting Stability Validation (T033)...")
    
    config = get_config()
    model_path = Path("data/models/random_forest.pkl")
    output_path = Path("data/results/stability_metrics.json")
    
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}. Please run T024 first.")
        sys.exit(1)
    
    # Load model to get parameters
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Extract parameters for retraining
    model_params = {
        'n_estimators': model.n_estimators,
        'max_depth': model.max_depth,
        'min_samples_split': model.min_samples_split,
        'min_samples_leaf': model.min_samples_leaf,
        'max_features': model.max_features
    }
    
    # Load data
    # We need X and y.
    processed_data_path = Path("data/processed/merged_dataset.csv")
    if not processed_data_path.exists():
        print(f"Error: Processed data not found at {processed_data_path}.")
        sys.exit(1)
    
    df = pd.read_csv(processed_data_path)
    
    # Identify target
    possible_targets = ['target', 'voc_target', 'concentration', 'y', 'VOC_concentration']
    target_col = None
    for t in possible_targets:
        if t in df.columns:
            target_col = t
            break
    
    if not target_col:
        # Assume last column
        target_col = df.columns[-1]
        print(f"Warning: Target column not explicitly found. Using last column: {target_col}")
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Ensure numeric
    X = X.apply(pd.to_numeric, errors='coerce')
    y = pd.to_numeric(y, errors='coerce')
    
    # Drop rows with NaN if any
    mask = ~(X.isna().any(axis=1) | y.isna())
    X = X[mask]
    y = y[mask]
    
    print(f"Running stability analysis on {len(X)} samples and {X.shape[1]} features...")
    
    stability_metrics = calculate_stability_metrics(
        X, y, model_params, n_folds=5, n_repeats=10, random_state=42
    )
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stability_metrics, f, indent=2)
    
    print(f"Stability metrics saved to {output_path}")
    print(f"Mean rank std: {np.mean(stability_metrics['rank_std']):.4f}")

if __name__ == "__main__":
    main()
