import os
import sys
import json
import logging
import tracemalloc
import time
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Import utilities from the project
from utils.config import set_seed, get_config_value
from utils.logging import get_main_logger, log_pipeline_step

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
MEMORY_LOG_PATH = os.path.join(RESULTS_DIR, "memory_profile.log")

# Ensure directories exist (defensive, though T001 tasks should have done this)
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

logger = get_main_logger("model_training")

def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset from the processed data directory."""
    input_path = os.path.join(DATA_PROCESSED_DIR, "cleaned_aluminum_fatigue.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data not found at {input_path}. Run data acquisition first.")
    logger.info(f"Loading cleaned data from {input_path}")
    return pd.read_csv(input_path)

def prepare_features_and_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare feature matrix X, target y, and grouping array.
    Assumes target column is 'fatigue_cycles' and grouping columns are
    'alloy_batch_id' and 'heat_treatment_group'.
    """
    target_col = "fatigue_cycles"
    group_cols = ["alloy_batch_id", "heat_treatment_group"]
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
    
    # Drop non-numeric columns for features, keeping only feature columns
    feature_cols = [c for c in df.columns if c not in [target_col] + group_cols]
    X = df[feature_cols].values
    y = df[target_col].values
    groups = df[group_cols].values  # This creates a 2D array, GroupKFold expects 1D or tuple of groups
    # Flatten groups if it's 2D (GroupKFold handles tuple of arrays or single array)
    # For simplicity, we create a composite group key
    composite_groups = df[group_cols[0]].astype(str) + "_" + df[group_cols[1]].astype(str)
    
    return X, y, composite_groups.values

def train_and_validate_grouped_cv(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    n_splits: int = 5,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Train Random Forest, Gradient Boosting, and ElasticNet models using
    Grouped K-Fold cross-validation. Returns aggregated metrics.
    """
    set_seed(seed)
    
    models = {
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=seed, n_jobs=1),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=100, random_state=seed),
        "ElasticNet": ElasticNet(random_state=seed, max_iter=1000)
    }
    
    gkf = GroupKFold(n_splits=n_splits)
    
    results = {}
    
    for name, model in models.items():
        logger.info(f"Training {name} with GroupKFold ({n_splits} splits)...")
        r2_scores = []
        rmse_scores = []
        mae_scores = []
        
        for train_idx, test_idx in gkf.split(X, y, groups):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            r2_scores.append(r2_score(y_test, y_pred))
            rmse_scores.append(np.sqrt(mean_squared_error(y_test, y_pred)))
            mae_scores.append(mean_absolute_error(y_test, y_pred))
        
        results[name] = {
            "r2_mean": float(np.mean(r2_scores)),
            "r2_std": float(np.std(r2_scores)),
            "rmse_mean": float(np.mean(rmse_scores)),
            "rmse_std": float(np.std(rmse_scores)),
            "mae_mean": float(np.mean(mae_scores)),
            "mae_std": float(np.std(mae_scores)),
            "best_params": model.get_params()
        }
        logger.info(f"{name} completed. R2: {results[name]['r2_mean']:.4f} (+/- {results[name]['r2_std']:.4f})")
    
    return results

def save_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save metrics to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def log_memory_profile(output_path: str) -> None:
    """
    Start memory profiling, run a dummy training loop to capture peak usage,
    and log the results.
    
    Note: In a real execution flow, this function would wrap the actual training
    logic. For this task, we assume the caller handles the training execution
    within the memory profile context, or we profile the training function directly.
    
    To satisfy the task requirement of logging peak usage to results/memory_profile.log,
    this function is designed to be called around the training process.
    However, since the training function is complex, we will implement a wrapper
    pattern or direct usage in main.
    
    This specific function will initialize tracemalloc and provide a context manager
    or helper to log peak memory after a block of code.
    """
    # This function is primarily a placeholder for the logging mechanism.
    # The actual profiling logic is integrated into main() to wrap the training call.
    pass

def main():
    """
    Main execution flow for Model Training with Memory Profiling.
    1. Load data.
    2. Start memory profiling.
    3. Train models (Grouped CV).
    4. Stop profiling and log peak memory.
    5. Save metrics.
    """
    logger.info("Starting Model Training Pipeline with Memory Profiling (T023a)")
    
    # 1. Load Data
    try:
        df = load_cleaned_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 2. Prepare Data
    try:
        X, y, groups = prepare_features_and_target(df)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info(f"Data prepared: {X.shape[0]} samples, {X.shape[1]} features.")
    
    # 3. Memory Profiling
    tracemalloc.start()
    start_time = time.time()
    
    logger.info("Starting model training with memory tracking...")
    try:
        metrics = train_and_validate_grouped_cv(X, y, groups)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        tracemalloc.stop()
        sys.exit(1)
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    peak_mb = peak / 1024 / 1024
    
    # 4. Log Memory Profile to results/memory_profile.log
    log_entry = (
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Peak Memory Usage: {peak_mb:.2f} MB\n"
        f"Current Memory Usage: {current / 1024 / 1024:.2f} MB\n"
        f"Total Training Time: {elapsed_time:.2f} seconds\n"
        f"Samples Processed: {X.shape[0]}\n"
        f"Models Trained: {list(metrics.keys())}\n"
        f"Memory Limit Check (7GB): {'PASS' if peak_mb < 7000 else 'FAIL'}\n"
        f"----------------------------------------\n"
    )
    
    with open(MEMORY_LOG_PATH, 'a') as f:
        f.write(log_entry)
    
    logger.info(f"Memory profile logged to {MEMORY_LOG_PATH}. Peak: {peak_mb:.2f} MB.")
    
    # 5. Save Metrics
    metrics_output_path = os.path.join(RESULTS_DIR, "metrics.json")
    save_metrics(metrics, metrics_output_path)
    
    logger.info("Model Training Pipeline completed successfully.")

if __name__ == "__main__":
    main()