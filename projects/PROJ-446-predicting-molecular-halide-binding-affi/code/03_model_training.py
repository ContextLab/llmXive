import os
import json
import logging
import time
import tracemalloc
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import r2_score, mean_squared_error
import joblib
from pathlib import Path

# Local imports matching API surface
from utils.config import get_data_path, get_code_path, get_logger, set_seed
from utils.performance_optimizer import check_ram_constraint, check_runtime_constraint, enforce_cpu_only, monitor_resources

logger = get_logger(__name__)

class HostIdentityKFold:
    """
    Custom cross-validator that ensures no host molecule appears in both
    train and validation sets within a fold.
    """
    def __init__(self, n_splits=5, random_state=42):
        self.n_splits = n_splits
        self.random_state = random_state
        self.logger = get_logger(__name__)

    def split(self, X: pd.DataFrame, y: pd.Series, groups: pd.Series):
        unique_hosts = groups.unique()
        self.logger.info(f"Creating {self.n_splits} folds from {len(unique_hosts)} unique hosts.")
        
        # Shuffle hosts
        rng = np.random.RandomState(self.random_state)
        rng.shuffle(unique_hosts)
        
        n_hosts = len(unique_hosts)
        fold_size = n_hosts // self.n_splits
        
        for i in range(self.n_splits):
            start_idx = i * fold_size
            if i == self.n_splits - 1:
                end_idx = n_hosts
            else:
                end_idx = (i + 1) * fold_size
            
            val_hosts = unique_hosts[start_idx:end_idx]
            train_hosts = np.setdiff1d(unique_hosts, val_hosts)
            
            train_idx = groups.isin(train_hosts)
            val_idx = groups.isin(val_hosts)
            
            yield train_idx, val_idx

def load_preprocessed_data() -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Loads the processed dataset and splits into features, target, and host groups.
    """
    data_path = get_data_path()
    file_path = data_path / "processed" / "halide_binding_data.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Processed data not found at {file_path}. Run data pipeline first.")
    
    df = pd.read_csv(file_path)
    
    # Identify feature columns (exclude target and metadata)
    exclude_cols = ['log_k', 'host_smiles', 'host_id', 'halide_identity']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in dataset.")
    
    X = df[feature_cols]
    y = df['log_k']
    groups = df['host_id']
    
    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features.")
    return X, y, groups

def train_and_evaluate_model(
    model, 
    X: pd.DataFrame, 
    y: pd.Series, 
    groups: pd.Series,
    model_name: str
) -> Dict[str, Any]:
    """
    Trains a model using host-identity stratified CV and returns metrics.
    """
    cv = HostIdentityKFold(n_splits=5, random_state=42)
    
    r2_scores = []
    rmse_scores = []
    feature_importances = None
    
    start_time = time.time()
    tracemalloc.start()
    
    for fold_idx, (train_idx, val_idx) in enumerate(cv.split(X, y, groups)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        
        r2 = r2_score(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
        
        logger.info(f"Fold {fold_idx + 1}: R² = {r2:.4f}, RMSE = {rmse:.4f}")
        
        if hasattr(model, 'feature_importances_'):
            if feature_importances is None:
                feature_importances = model.feature_importances_
            else:
                feature_importances += model.feature_importances_
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    runtime = time.time() - start_time
    
    # Check constraints
    check_ram_constraint(peak / (1024 ** 3))
    check_runtime_constraint(runtime)
    
    if feature_importances is not None:
        feature_importances = (feature_importances / 5).tolist()
    
    return {
        "model_type": model_name,
        "folds": 5,
        "r2_scores": r2_scores,
        "rmse_scores": rmse_scores,
        "mean_r2": float(np.mean(r2_scores)),
        "mean_rmse": float(np.mean(rmse_scores)),
        "std_r2": float(np.std(r2_scores)),
        "std_rmse": float(np.std(rmse_scores)),
        "runtime_seconds": runtime,
        "peak_ram_gb": float(peak / (1024 ** 3)),
        "feature_importances": feature_importances,
        "feature_names": X.columns.tolist()
    }

def run_random_forest_training(X: pd.DataFrame, y: pd.Series, groups: pd.Series) -> Dict[str, Any]:
    """
    Trains a Random Forest model with default hyperparameters.
    """
    logger.info("Starting Random Forest training...")
    set_seed(42)
    model = RandomForestRegressor(random_state=42)
    return train_and_evaluate_model(model, X, y, groups, "RandomForest")

def run_gradient_boosting_training(X: pd.DataFrame, y: pd.Series, groups: pd.Series) -> Dict[str, Any]:
    """
    Trains a Gradient Boosting model with default hyperparameters.
    """
    logger.info("Starting Gradient Boosting training...")
    set_seed(42)
    model = GradientBoostingRegressor(random_state=42)
    return train_and_evaluate_model(model, X, y, groups, "GradientBoosting")

def save_model_artifacts(rf_results: Dict, gb_results: Dict) -> None:
    """
    Saves model run artifacts to data/processed/model_runs.json.
    """
    output_path = get_data_path() / "processed" / "model_runs.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    artifacts = {
        "random_forest": rf_results,
        "gradient_boosting": gb_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(artifacts, f, indent=2)
    
    logger.info(f"Model artifacts saved to {output_path}")

def main():
    """
    Main entry point for model training pipeline.
    """
    try:
        enforce_cpu_only()
        X, y, groups = load_preprocessed_data()
        
        rf_results = run_random_forest_training(X, y, groups)
        gb_results = run_gradient_boosting_training(X, y, groups)
        
        save_model_artifacts(rf_results, gb_results)
        
        logger.info("Model training pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()