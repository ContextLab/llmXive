import os
import json
import logging
import time
import tracemalloc
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
from pathlib import Path

from code.utils.config import get_data_path, get_code_path, set_seed
from code.utils.logger import get_logger
from code.utils.validators import validate_dataset

logger = get_logger(__name__)

class HostIdentityKFold:
    """
    Custom K-Fold splitter that ensures no host molecule appears in both
    train and validation sets within a fold.
    """
    def __init__(self, n_splits=5, random_state=42):
        self.n_splits = n_splits
        self.random_state = random_state
        self.kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    def split(self, X: pd.DataFrame, y: Optional[pd.Series] = None, groups: Optional[pd.Series] = None) -> Any:
        if groups is None:
            raise ValueError("HostIdentityKFold requires 'groups' (host_id) to be provided.")
        
        unique_hosts = groups.unique()
        n_hosts = len(unique_hosts)
        
        if n_hosts < self.n_splits:
            logger.warning(f"Number of unique hosts ({n_hosts}) is less than n_splits ({self.n_splits}). Adjusting n_splits.")
            adjusted_splits = max(1, n_hosts)
            self.kf.n_splits = adjusted_splits

        # We need to split hosts, not rows
        host_indices = {host: groups[groups == host].index.tolist() for host in unique_hosts}
        host_keys = list(host_indices.keys())
        
        # Shuffle host keys
        np.random.seed(self.random_state)
        np.random.shuffle(host_keys)
        
        # Split host keys into folds
        fold_size = len(host_keys) // self.n_splits
        for i in range(self.n_splits):
            start_idx = i * fold_size
            end_idx = start_idx + fold_size if i < self.n_splits - 1 else len(host_keys)
            
            val_hosts = host_keys[start_idx:end_idx]
            train_hosts = [h for h in host_keys if h not in val_hosts]
            
            train_idx = []
            val_idx = []
            
            for h in train_hosts:
                train_idx.extend(host_indices[h])
            for h in val_hosts:
                val_idx.extend(host_indices[h])
                
            yield np.array(train_idx), np.array(val_idx)

def load_preprocessed_data() -> pd.DataFrame:
    """
    Loads the preprocessed dataset from data/processed/halide_binding_data.csv.
    """
    data_path = get_data_path()
    file_path = data_path / "processed" / "halide_binding_data.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Preprocessed data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    # Validate basic structure
    required_cols = ['host_id', 'halide_identity', 'log_k', 'ecfp_fingerprint', 'charge_density', 'cavity_volume']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} records from {file_path}")
    return df

def train_and_evaluate_model(
    model_name: str,
    model_class: Any,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series
) -> Tuple[Any, Dict[str, float]]:
    """
    Trains a model and returns the trained instance and metrics.
    """
    logger.info(f"Training {model_name}...")
    model = model_class()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_val)
    
    r2 = r2_score(y_val, y_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    
    metrics = {
        "r2": float(r2),
        "rmse": float(rmse)
    }
    
    logger.info(f"{model_name} metrics - R2: {r2:.4f}, RMSE: {rmse:.4f}")
    return model, metrics

def run_random_forest_training(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Runs Random Forest training with host-identity stratified cross-validation.
    """
    set_seed(42)
    X = df.drop(columns=['host_id', 'halide_identity', 'log_k'])
    y = df['log_k']
    groups = df['host_id']
    
    splitter = HostIdentityKFold(n_splits=5, random_state=42)
    results = []
    
    for fold_idx, (train_idx, val_idx) in enumerate(splitter.split(X, y, groups)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        model, metrics = train_and_evaluate_model(
            "RandomForest", 
            RandomForestRegressor, 
            X_train, y_train, 
            X_val, y_val
        )
        
        # Extract feature importances
        importances = dict(zip(X.columns, model.feature_importances_.tolist()))
        
        results.append({
            "fold": fold_idx + 1,
            "model_type": "RandomForest",
            "metrics": metrics,
            "feature_importances": importances
        })
    
    return results

def run_gradient_boosting_training(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Runs Gradient Boosting training with host-identity stratified cross-validation.
    """
    set_seed(42)
    X = df.drop(columns=['host_id', 'halide_identity', 'log_k'])
    y = df['log_k']
    groups = df['host_id']
    
    splitter = HostIdentityKFold(n_splits=5, random_state=42)
    results = []
    
    for fold_idx, (train_idx, val_idx) in enumerate(splitter.split(X, y, groups)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        model, metrics = train_and_evaluate_model(
            "GradientBoosting", 
            GradientBoostingRegressor, 
            X_train, y_train, 
            X_val, y_val
        )
        
        # Extract feature importances
        importances = dict(zip(X.columns, model.feature_importances_.tolist()))
        
        results.append({
            "fold": fold_idx + 1,
            "model_type": "GradientBoosting",
            "metrics": metrics,
            "feature_importances": importances
        })
    
    return results

def save_model_artifacts(rf_results: List[Dict[str, Any]], gb_results: List[Dict[str, Any]]) -> None:
    """
    Saves model run artifacts to data/processed/model_runs.json.
    """
    output_path = get_data_path() / "processed" / "model_runs.json"
    
    artifact = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "random_forest_runs": rf_results,
        "gradient_boosting_runs": gb_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(artifact, f, indent=2)
    
    logger.info(f"Model artifacts saved to {output_path}")

def main():
    """
    Main entry point for model training and artifact saving.
    """
    logger.info("Starting model training pipeline...")
    start_time = time.time()
    tracemalloc.start()
    
    try:
        df = load_preprocessed_data()
        
        # Check for simulated mode
        state_path = get_data_path() / "simulated" / "state.json"
        if state_path.exists():
            with open(state_path, 'r') as f:
                state = json.load(f)
            if state.get("SIMULATED_MODE", False):
                logger.warning("WARNING: Simulated Data Mode active. Training on simulated data.")
        
        rf_results = run_random_forest_training(df)
        gb_results = run_gradient_boosting_training(df)
        
        save_model_artifacts(rf_results, gb_results)
        
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        runtime = end_time - start_time
        peak_ram_gb = peak / (1024 ** 3)
        
        logger.info(f"Training completed in {runtime:.2f} seconds. Peak RAM: {peak_ram_gb:.2f} GB")
        
        if runtime > 6 * 3600:
            raise RuntimeError("Runtime exceeded 6-hour threshold.")
        if peak_ram_gb > 7:
            raise RuntimeError("Peak RAM exceeded 7GB threshold.")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    finally:
        tracemalloc.stop()

if __name__ == "__main__":
    main()