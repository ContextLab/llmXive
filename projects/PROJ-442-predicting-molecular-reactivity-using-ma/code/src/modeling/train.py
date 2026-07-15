import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import GroupKFold
from sklearn.metrics import spearmanr

from src.utils.logging import get_logger
from src.modeling.config import load_config
from src.utils.state_manager import register_artifact, update_stage_status

logger = get_logger(__name__)

def load_target_data(feature_path: str, target_path: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load feature matrix and target variable.
    Expects feature_path to be a parquet file and target_path to be a CSV with a 'target' column.
    """
    logger.info(f"Loading features from {feature_path}")
    X = pd.read_parquet(feature_path)
    
    logger.info(f"Loading targets from {target_path}")
    # Assuming target file has a column named 'target' or 'yield_pct'
    df_target = pd.read_csv(target_path)
    if 'target' not in df_target.columns:
        if 'yield_pct' in df_target.columns:
            df_target['target'] = df_target['yield_pct']
        else:
            raise ValueError(f"Target file {target_path} must contain 'target' or 'yield_pct' column")
    
    y = df_target['target']
    
    # Ensure alignment
    if X.shape[0] != y.shape[0]:
        logger.warning(f"Feature rows ({X.shape[0]}) != Target rows ({y.shape[0]}). Attempting index alignment.")
        # In a real pipeline, indices should match or be explicit. 
        # Here we assume they are ordered identically as per ingestion pipeline.
        if len(X) > len(y):
            X = X.iloc[:len(y)]
        elif len(y) > len(X):
            y = y.iloc[:len(X)]
    
    return X, y

def normalize_target(y: pd.Series) -> Tuple[pd.Series, Dict[str, float]]:
    """
    Z-score normalize the target variable.
    Returns normalized series and normalization params.
    """
    mean = y.mean()
    std = y.std()
    if std == 0:
        logger.warning("Target standard deviation is zero. Skipping normalization.")
        return y, {"mean": mean, "std": 1.0}
    
    y_norm = (y - mean) / std
    return y_norm, {"mean": mean, "std": std}

def train_xgboost_model(X: pd.DataFrame, y: pd.Series, config: Dict[str, Any]) -> xgb.Booster:
    """
    Train XGBoost model with given config.
    """
    params = {
        'objective': 'reg:squarederror',
        'eval_metric': 'rmse',
        'max_depth': config.get('max_depth', 6),
        'learning_rate': config.get('learning_rate', 0.1),
        'n_estimators': config.get('n_estimators', 100),
        'subsample': config.get('subsample', 0.8),
        'colsample_bytree': config.get('colsample_bytree', 0.8),
        'seed': 42
    }
    
    dtrain = xgb.DMatrix(X, label=y)
    model = xgb.train(params, dtrain, num_boost_round=params['n_estimators'])
    return model

def run_training_pipeline(
    feature_path: str,
    target_path: str,
    output_model_path: str,
    output_log_path: str,
    runtime_threshold_seconds: float = 1800.0  # Default 30 mins
) -> Dict[str, Any]:
    """
    Run the full training pipeline with runtime enforcement.
    
    FR-003: Abort training if runtime exceeds threshold.
    """
    start_time = time.time()
    logger.info(f"Starting training pipeline. Runtime threshold: {runtime_threshold_seconds}s")
    
    config = load_config()
    training_config = config.get('training', {})
    # Allow override from function arg or config
    threshold = training_config.get('runtime_threshold_seconds', runtime_threshold_seconds)
    
    # 1. Load Data
    X, y = load_target_data(feature_path, target_path)
    elapsed = time.time() - start_time
    if elapsed > threshold:
        raise RuntimeError(f"Data loading exceeded runtime threshold of {threshold}s (took {elapsed:.2f}s). Aborting.")
    
    # 2. Normalize Target
    y_norm, norm_params = normalize_target(y)
    elapsed = time.time() - start_time
    if elapsed > threshold:
        raise RuntimeError(f"Target normalization exceeded runtime threshold of {threshold}s (took {elapsed:.2f}s). Aborting.")
    
    # 3. Prepare GroupKFold (LOSO)
    # Assuming 'scaffold_id' column exists in X or we derive it. 
    # For this implementation, we assume a 'scaffold_id' column exists in the feature dataframe 
    # or we use a dummy group if not present (fallback to standard CV if scaffold info missing).
    if 'scaffold_id' in X.columns:
        groups = X['scaffold_id']
    else:
        logger.warning("No 'scaffold_id' column found. Using standard KFold groups (random).")
        groups = np.zeros(len(X), dtype=int)
    
    gkf = GroupKFold(n_splits=5)
    
    fold_scores = []
    best_model = None
    fold_results = []
    
    # 4. Training Loop
    for fold_idx, (train_idx, val_idx) in enumerate(gkf.split(X, y_norm, groups)):
        current_time = time.time() - start_time
        if current_time > threshold:
            raise RuntimeError(f"Training loop exceeded runtime threshold of {threshold}s at fold {fold_idx}. Aborting.")
        
        logger.info(f"Starting Fold {fold_idx + 1}/5")
        
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y_norm.iloc[train_idx], y_norm.iloc[val_idx]
        
        model = train_xgboost_model(X_train, y_train, training_config)
        
        # Evaluate
        dval = xgb.DMatrix(X_val, label=y_val)
        preds = model.predict(dval)
        spearman_corr, p_value = spearmanr(preds, y_val)
        fold_scores.append(spearman_corr)
        
        fold_results.append({
            "fold": fold_idx + 1,
            "spearman_rho": float(spearman_corr),
            "p_value": float(p_value),
            "runtime_s": float(time.time() - start_time)
        })
        
        # Keep the last model (or best, but keeping last for simplicity in this snippet)
        best_model = model
        
        elapsed = time.time() - start_time
        logger.info(f"Fold {fold_idx + 1} completed. Spearman: {spearman_corr:.4f}. Total Runtime: {elapsed:.2f}s")
        
        if elapsed > threshold:
            raise RuntimeError(f"Training exceeded runtime threshold of {threshold}s after fold {fold_idx + 1}.")
    
    final_runtime = time.time() - start_time
    
    if final_runtime > threshold:
        raise RuntimeError(f"Total training time {final_runtime:.2f}s exceeded threshold {threshold}s. Final model NOT saved.")
    
    # 5. Save Artifacts
    logger.info(f"Training completed successfully in {final_runtime:.2f}s.")
    
    # Save Model
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    best_model.save_model(output_model_path)
    
    # Save Log
    log_data = {
        "total_runtime_seconds": final_runtime,
        "threshold_seconds": threshold,
        "status": "completed",
        "fold_results": fold_results,
        "mean_spearman_rho": float(np.mean(fold_scores)),
        "normalization_params": norm_params
    }
    
    os.makedirs(os.path.dirname(output_log_path), exist_ok=True)
    with open(output_log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Model saved to {output_model_path}")
    logger.info(f"Training log saved to {output_log_path}")
    
    # Register artifacts
    register_artifact("model", output_model_path)
    register_artifact("training_log", output_log_path)
    update_stage_status("US2", "completed")
    
    return log_data

def main():
    """
    Entry point for the training script.
    Reads config for paths and thresholds.
    """
    config = load_config()
    paths = config.get('paths', {})
    training = config.get('training', {})
    
    feature_path = paths.get('feature_matrix', 'data/processed/feature_matrix.parquet')
    target_path = paths.get('target', 'data/processed/targets.csv')
    model_output = paths.get('model_output', 'data/models/xgboost_model.json')
    log_output = paths.get('training_log', 'data/processed/training_log.json')
    
    runtime_threshold = training.get('runtime_threshold_seconds', 1800.0)
    
    try:
        run_training_pipeline(
            feature_path=feature_path,
            target_path=target_path,
            output_model_path=model_output,
            output_log_path=log_output,
            runtime_threshold_seconds=runtime_threshold
        )
    except RuntimeError as e:
        logger.error(f"Training aborted: {e}")
        # Re-raise to ensure the pipeline execution stage sees the failure
        raise

if __name__ == "__main__":
    main()