"""
Model training logic.
Implements Random Forest and SVM with grid search.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib
from config import RANDOM_SEED
from utils.io import load_parquet, check_memory_limit

def train_random_forest_grid_search(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    param_grid: Dict[str, list],
    random_seed: int = RANDOM_SEED,
    output_dir: Optional[Path] = None
) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a Random Forest model with Grid Search.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        X_val: Validation features.
        y_val: Validation targets.
        param_grid: Grid of hyperparameters.
        random_seed: Random seed for reproducibility.
        output_dir: Directory to save model and metrics.
        
    Returns:
        Tuple of (best_model, metrics_dict)
    """
    rf = RandomForestRegressor(random_state=random_seed, n_jobs=-1)
    
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=3,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Evaluate on validation set
    y_pred = best_model.predict(X_val)
    r2 = r2_score(y_val, y_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    mae = mean_absolute_error(y_val, y_pred)
    
    metrics = {
        "r2": float(r2),
        "rmse": float(rmse),
        "mae": float(mae),
        "best_params": best_params
    }
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = output_dir / "rf_best_model.pkl"
        metrics_path = output_dir / "rf_metrics.json"
        
        joblib.dump(best_model, model_path)
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    return best_model, metrics

def train_svm_grid_search(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    param_grid: Dict[str, list],
    random_seed: int = RANDOM_SEED,
    output_dir: Optional[Path] = None
) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a Support Vector Machine (SVR) model with Grid Search.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        X_val: Validation features.
        y_val: Validation targets.
        param_grid: Grid of hyperparameters for C and kernel.
        random_seed: Random seed for reproducibility (used for data shuffling if applicable).
        output_dir: Directory to save model and metrics.
        
    Returns:
        Tuple of (best_model, metrics_dict)
    """
    # SVR does not have a random_state parameter in the same way, 
    # but we ensure deterministic behavior by setting the global seed if needed
    # and using shuffle=False in GridSearch if the data is already shuffled.
    # For reproducibility in CV, we rely on the data order or explicit shuffle logic.
    # Here we use the provided random_seed for any internal shuffling if we were to add it,
    # but standard GridSearchCV with shuffle=True would need it.
    # We will use shuffle=False to match the deterministic nature of the split if it's fixed,
    # or rely on the fact that the input data is fixed.
    
    svr = SVR()
    
    grid_search = GridSearchCV(
        estimator=svr,
        param_grid=param_grid,
        cv=3,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Evaluate on validation set
    y_pred = best_model.predict(X_val)
    r2 = r2_score(y_val, y_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    mae = mean_absolute_error(y_val, y_pred)
    
    metrics = {
        "r2": float(r2),
        "rmse": float(rmse),
        "mae": float(mae),
        "best_params": best_params
    }
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = output_dir / "svm_best_model.pkl"
        metrics_path = output_dir / "svm_metrics.json"
        
        joblib.dump(best_model, model_path)
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    return best_model, metrics

def main():
    """
    Main entry point to run the Random Forest and SVM grid search training pipelines.
    Loads data from data/processed/, performs the split, trains the models,
    and saves results to data/results/best_models/.
    """
    # Paths
    data_path = Path("data/processed/cleaned_reactions.parquet")
    split_indices_path = Path("data/processed/split_indices.parquet")
    output_dir = Path("data/results/best_models")
    
    # Check memory limit before loading
    check_memory_limit(limit_mb=7000)
    
    # Load data
    print(f"Loading data from {data_path}...")
    df = load_parquet(data_path)
    
    # Verify required columns exist
    required_cols = ['reactants_fp', 'reagents_fp', 'yield_pct']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in dataset.")
    
    # Prepare features (concatenate reactants and reagents fingerprints)
    # Assuming fingerprints are stored as lists or arrays in the parquet
    print("Preparing features...")
    # Convert lists to numpy arrays if they aren't already
    if isinstance(df['reactants_fp'].iloc[0], list):
        X_reactants = np.vstack(df['reactants_fp'].values)
    else:
        X_reactants = np.array(df['reactants_fp'].values.tolist())
        
    if isinstance(df['reagents_fp'].iloc[0], list):
        X_reagents = np.vstack(df['reagents_fp'].values)
    else:
        X_reagents = np.array(df['reagents_fp'].values.tolist())
        
    X = X_reactants + X_reagents
    y = df['yield_pct'].values.astype(float)
    
    # Load split indices
    print(f"Loading split indices from {split_indices_path}...")
    split_df = load_parquet(split_indices_path)
    
    train_idx = split_df[split_df['split'] == 'train'].index
    val_idx = split_df[split_df['split'] == 'val'].index
    test_idx = split_df[split_df['split'] == 'test'].index
    
    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    
    print(f"Train set size: {len(X_train)}, Val set size: {len(X_val)}")
    
    # --- Random Forest Training ---
    print("\n=== Starting Random Forest Grid Search ===")
    rf_param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [10, 20, None]
    }
    
    best_rf_model, rf_metrics = train_random_forest_grid_search(
        X_train, y_train,
        X_val, y_val,
        param_grid=rf_param_grid,
        output_dir=output_dir
    )
    
    print(f"Random Forest Best R2: {rf_metrics['r2']:.4f}")
    print(f"Random Forest Best Params: {rf_metrics['best_params']}")
    
    # --- SVM Training ---
    print("\n=== Starting SVM Grid Search ===")
    # Grid search for C and kernel (linear, rbf)
    svm_param_grid = {
        'C': [0.1, 1.0, 10.0],
        'kernel': ['linear', 'rbf']
    }
    
    best_svm_model, svm_metrics = train_svm_grid_search(
        X_train, y_train,
        X_val, y_val,
        param_grid=svm_param_grid,
        output_dir=output_dir
    )
    
    print(f"SVM Best R2: {svm_metrics['r2']:.4f}")
    print(f"SVM Best Params: {svm_metrics['best_params']}")
    
    print("\nTraining complete.")
    print(f"Results saved to {output_dir}")

if __name__ == "__main__":
    main()