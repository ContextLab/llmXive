import os
import json
import logging
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import KFold
from sklearn.metrics import spearmanr
from scipy.stats import spearmanr as scipy_spearmanr

from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import update_stage_status, register_artifact
from src.modeling.config import load_config
from src.data.preprocessing import load_feature_matrix

logger = get_logger(__name__)

# Constants
TRAINING_TIMEOUT_SECONDS = 1800  # 30 minutes
MODEL_OUTPUT_PATH = "data/models/xgboost_model.json"
LOG_OUTPUT_PATH = "data/processed/training_log.json"

def load_target_data(feature_path: str, target_col: str = "yield_pct") -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load feature matrix and extract target variable.
    Ensures target is numeric and handles missing values.
    """
    logger.info(f"Loading features from {feature_path}")
    df = load_feature_matrix(feature_path)

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in feature matrix. Available: {df.columns.tolist()}")

    # Drop rows with missing target
    initial_count = len(df)
    df = df.dropna(subset=[target_col])
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing target values.")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")
    return X, y

def normalize_target(y: pd.Series) -> Tuple[pd.Series, float, float]:
    """
    Z-score normalize the target variable.
    Returns normalized series, mean, and std.
    """
    mean_val = y.mean()
    std_val = y.std()
    if std_val == 0:
        logger.warning("Target standard deviation is zero. Skipping normalization.")
        return y, mean_val, 1.0
    y_norm = (y - mean_val) / std_val
    logger.info(f"Target normalized: mean={mean_val:.4f}, std={std_val:.4f}")
    return y_norm, mean_val, std_val

def train_xgboost_model(
    X: pd.DataFrame,
    y: pd.Series,
    config: Dict[str, Any],
    cv_folds: int = 5
) -> Tuple[xgb.Booster, Dict[str, Any]]:
    """
    Train XGBoost model with Cross-Validation (LOSO logic placeholder for now,
    using standard KFold as LOSO requires scaffold info which is assumed in config).
    Enforces runtime timeout.
    """
    start_time = time.time()
    params = config.get("model_params", {})
    # Default params if not specified
    default_params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "max_depth": 6,
        "eta": 0.3,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "seed": 42,
        "nthread": -1
    }
    default_params.update(params)
    params = default_params

    dtrain = xgb.DMatrix(X, label=y)

    cv_results = xgb.cv(
        params,
        dtrain,
        num_boost_round=config.get("num_boost_round", 100),
        nfold=cv_folds,
        stratified=False,
        seed=42,
        verbose_eval=False,
        early_stopping_rounds=10
    )

    # Check runtime
    elapsed = time.time() - start_time
    if elapsed > TRAINING_TIMEOUT_SECONDS:
        raise TimeoutError(f"Training exceeded timeout of {TRAINING_TIMEOUT_SECONDS}s after {elapsed:.1f}s")

    # Train final model on full data
    bst = xgb.train(params, dtrain, num_boost_round=int(cv_results["test-rmse-mean"].idxmax()) + 1)

    # Calculate Spearman correlation on training data (as a sanity check)
    preds = bst.predict(dtrain)
    spearman_corr, p_value = scipy_spearmanr(y, preds)

    metrics = {
        "best_iteration": int(cv_results["test-rmse-mean"].idxmax()),
        "final_rmse": float(cv_results["test-rmse-mean"].max()),
        "spearman_correlation": float(spearman_corr),
        "spearman_p_value": float(p_value),
        "training_time_seconds": float(elapsed)
    }

    logger.info(f"Training complete. Spearman ρ: {spearman_corr:.4f}, Time: {elapsed:.2f}s")
    return bst, metrics

def run_training_pipeline(
    config_path: str = "src/modeling/config.yaml",
    feature_path: str = "data/processed/feature_matrix.parquet",
    output_model_path: str = MODEL_OUTPUT_PATH,
    output_log_path: str = LOG_OUTPUT_PATH
) -> Dict[str, Any]:
    """
    Orchestrate the training pipeline: load, normalize, train, save.
    Integrates logging and state updates.
    """
    stage_name = "training"
    try:
        # Setup logger for this stage
        logger.info(f"Starting {stage_name} pipeline")
        update_stage_status(stage_name, "running")

        # Load config
        config = load_config(config_path)

        # Load data
        X, y = load_target_data(feature_path)

        # Normalize target
        y_norm, mean, std = normalize_target(y)

        # Train model
        model, metrics = train_xgboost_model(X, y_norm, config)

        # Save model
        model_dir = Path(output_model_path).parent
        model_dir.mkdir(parents=True, exist_ok=True)
        model.save_model(output_model_path)
        logger.info(f"Model saved to {output_model_path}")

        # Prepare log data
        log_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H-%M-%S"),
            "config_path": config_path,
            "feature_path": feature_path,
            "target_normalization": {"mean": float(mean), "std": float(std)},
            "metrics": metrics,
            "model_path": output_model_path
        }

        # Save logs
        log_dir = Path(output_log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(output_log_path, "w") as f:
            json.dump(log_data, f, indent=2)
        logger.info(f"Training log saved to {output_log_path}")

        # Register artifacts with state manager
        register_artifact("model", output_model_path, description="Trained XGBoost model")
        register_artifact("training_log", output_log_path, description="Training metrics and metadata")

        update_stage_status(stage_name, "completed")
        return log_data

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        logger.error(traceback.format_exc())
        update_stage_status(stage_name, "failed", error_message=str(e))
        raise

def main():
    """Entry point for the training script."""
    setup_logger("train", level=logging.INFO)
    try:
        run_training_pipeline()
        logger.info("Training pipeline finished successfully.")
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
