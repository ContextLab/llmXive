import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import spearmanr

from src.modeling.config import load_config
from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import update_stage_status, register_artifact
from src.data.preprocessing import load_feature_matrix

# Configure logger for this module
logger = get_logger(__name__)

def load_target_data(feature_path: Path, target_col: str = "yield_pct") -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load features and extract the target variable.
    Assumes the feature matrix parquet contains the target column as well.
    """
    if not feature_path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {feature_path}")
    
    df = pd.read_parquet(feature_path)
    
    if target_col not in df.columns:
        # Fallback to 'success_flag' if yield_pct is missing, per spec FR-004
        if "success_flag" in df.columns:
            logger.warning(f"Target column '{target_col}' not found. Falling back to 'success_flag'.")
            target = df["success_flag"]
        else:
            raise ValueError(f"Neither '{target_col}' nor 'success_flag' found in feature matrix.")
    else:
        target = df[target_col]
    
    # Drop rows with missing target values
    mask = target.notna()
    if not mask.all():
        logger.warning(f"Dropping {(~mask).sum()} rows with missing target values.")
    
    return df[mask], target[mask]

def normalize_target(target: pd.Series) -> Tuple[pd.Series, float, float]:
    """
    Z-score normalize the target variable.
    Returns normalized series, mean, and std.
    """
    mean_val = target.mean()
    std_val = target.std()
    if std_val == 0:
        logger.warning("Target standard deviation is zero. Skipping normalization.")
        return target, 0.0, 1.0
    
    normalized = (target - mean_val) / std_val
    return normalized, mean_val, std_val

def train_xgboost_model(X: pd.DataFrame, y: pd.Series, config: Dict[str, Any]) -> xgb.Booster:
    """
    Train an XGBoost model using the provided configuration.
    """
    params = config.get("model_params", {})
    # Ensure objective is set
    if "objective" not in params:
        # Determine objective based on target variance or config
        if y.dtype in [np.int64, np.int32] and len(y.unique()) < 10:
            params["objective"] = "binary:logistic"
        else:
            params["objective"] = "reg:squarederror"
    
    dtrain = xgb.DMatrix(X, label=y)
    
    # Extract training params
    num_boost_round = config.get("num_boost_round", 100)
    early_stopping_rounds = config.get("early_stopping_rounds", 10)
    
    # Train
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=num_boost_round,
        evals=[(dtrain, "train")],
        early_stopping_rounds=early_stopping_rounds,
        verbose_eval=False
    )
    
    return model

def run_training_pipeline(
    feature_path: Path,
    output_model_path: Path,
    output_log_path: Path,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Orchestrate the full training pipeline: load, normalize, train, save.
    Returns a summary dictionary for logging.
    """
    start_time = time.time()
    logger.info(f"Starting training pipeline with features from {feature_path}")
    
    # 1. Load Data
    df, target = load_target_data(feature_path, config.get("target_column", "yield_pct"))
    X = df.drop(columns=[config.get("target_column", "yield_pct"), "success_flag"])
    # Ensure we drop success_flag if it was used as target fallback to avoid leakage
    if "success_flag" in X.columns:
         X = X.drop(columns=["success_flag"])
    
    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features.")
    
    # 2. Normalize Target
    y_norm, mean_val, std_val = normalize_target(target)
    
    # 3. Train Model
    model = train_xgboost_model(X, y_norm, config)
    
    # 4. Evaluate (Simple in-sample check for logging)
    y_pred_norm = model.predict(xgb.DMatrix(X))
    # Inverse transform for metrics if needed, but Spearman is rank-based
    spearman_corr, _ = spearmanr(y_norm, y_pred_norm)
    logger.info(f"Training Spearman Correlation: {spearman_corr:.4f}")
    
    # 5. Save Model
    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(output_model_path))
    logger.info(f"Model saved to {output_model_path}")
    
    # 6. Save Training Log
    end_time = time.time()
    runtime = end_time - start_time
    
    training_log = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "feature_file": str(feature_path),
        "model_file": str(output_model_path),
        "samples": int(X.shape[0]),
        "features": int(X.shape[1]),
        "target_mean": float(mean_val),
        "target_std": float(std_val),
        "spearman_correlation": float(spearman_corr),
        "runtime_seconds": runtime,
        "config_snapshot": config
    }
    
    output_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_log_path, "w") as f:
        json.dump(training_log, f, indent=2)
    logger.info(f"Training log saved to {output_log_path}")
    
    return training_log

def main():
    """
    Entry point for the training stage.
    Expects configuration from src/modeling/config.yaml.
    """
    # Setup logger
    setup_logger()
    logger = get_logger(__name__)
    
    # Load Config
    config = load_config()
    
    # Define paths
    # Assuming data/processed/feature_matrix.parquet based on T024
    feature_path = Path("data/processed/feature_matrix.parquet")
    model_output_path = Path("data/models/xgboost_model.json")
    log_output_path = Path("data/processed/training_log.json")
    
    # Override paths if specified in config
    if "paths" in config:
        if "feature_matrix" in config["paths"]:
            feature_path = Path(config["paths"]["feature_matrix"])
        if "model_output" in config["paths"]:
            model_output_path = Path(config["paths"]["model_output"])
        if "training_log" in config["paths"]:
            log_output_path = Path(config["paths"]["training_log"])
    
    try:
        # Run Pipeline
        log_summary = run_training_pipeline(
            feature_path=feature_path,
            output_model_path=model_output_path,
            output_log_path=log_output_path,
            config=config
        )
        
        # Update State
        update_stage_status("US2", "completed", "Training completed successfully")
        register_artifact("data/models/xgboost_model.json", "model")
        register_artifact("data/processed/training_log.json", "log")
        
        logger.info("Training stage completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        update_stage_status("US2", "failed", f"Missing data: {e}")
        raise
    except Exception as e:
        logger.error(f"Training failed: {e}")
        update_stage_status("US2", "failed", str(e))
        raise

if __name__ == "__main__":
    main()
