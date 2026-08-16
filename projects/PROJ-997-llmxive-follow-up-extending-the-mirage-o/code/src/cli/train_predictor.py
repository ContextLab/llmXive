"""
T021: Train Kernel Ridge Regression (KRR) predictor for policy gap.

Loads the stratified training split from T021A, trains a KRR model
to predict the hardware-measured policy gap (calculated_kl_divergence),
and saves the model artifact to data/models/gap_predictor.pkl.
"""
import os
import sys
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.kernel_ridge import KernelRidge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import json

# Project imports based on provided API surface
# Note: T021A (prepare_data_split.py) is the dependency that produces the input.
# We assume the file exists as per the task description.
from src.config.logging_config import setup_logger, ensure_log_dir
from src.config.env_config import load_config

logger = logging.getLogger(__name__)

# Constants
TRAIN_INPUT_PATH = Path("data/processed/split_train.parquet")
MODEL_OUTPUT_PATH = Path("data/models/gap_predictor.pkl")
METRICS_LOG_PATH = Path("logs/pipeline.log")

# Feature columns expected in the dataset based on T015/T017 schema
FEATURE_COLUMNS = [
    "gradient_norms",
    "local_curvature"
]
TARGET_COLUMN = "calculated_kl_divergence"

# Hyperparameters for KRR (can be tuned later, using defaults for MVP)
KRR_ALPHA = 1.0
KRR_KERNEL = "rbf"
KRR_GAMMA = 0.1

def load_training_data(input_path: Path) -> pd.DataFrame:
    """
    Loads the stratified training split.
    Raises FileNotFoundError if the file does not exist (fail loudly).
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Training split not found at {input_path}. "
            "Ensure T021A (prepare_data_split.py) has been executed first."
        )
    
    logger.info(f"Loading training data from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Validate schema
    required_cols = set(FEATURE_COLUMNS + [TARGET_COLUMN])
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Training data missing required columns: {missing_cols}. "
            f"Expected: {required_cols}, Found: {list(df.columns)}"
        )
    
    # Handle NaNs if any (drop rows with missing target or features)
    initial_count = len(df)
    df = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows with NaN values in features or target.")
    
    if len(df) == 0:
        raise ValueError("No valid training samples remaining after cleaning.")
    
    logger.info(f"Loaded {len(df)} training samples.")
    return df

def prepare_features_and_target(df: pd.DataFrame):
    """
    Extracts features (X) and target (y) from the dataframe.
    Handles potential non-numeric columns if present.
    """
    X = df[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    y = df[TARGET_COLUMN].to_numpy(dtype=np.float32)
    return X, y

def train_krr_model(X: np.ndarray, y: np.ndarray, config: Dict[str, Any]) -> Pipeline:
    """
    Trains a Kernel Ridge Regression model wrapped in a preprocessing pipeline.
    Returns a sklearn Pipeline: [StandardScaler, KernelRidge].
    """
    logger.info(f"Training KRR with alpha={config.get('alpha', KRR_ALPHA)}, "
                f"kernel={config.get('kernel', KRR_KERNEL)}, "
                f"gamma={config.get('gamma', KRR_GAMMA)}")
    
    # Create pipeline: Standardize features before RBF kernel
    # RBF kernel is sensitive to feature scales
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("krr", KernelRidge(
            alpha=config.get("alpha", KRR_ALPHA),
            kernel=config.get("kernel", KRR_KERNEL),
            gamma=config.get("gamma", KRR_GAMMA)
        ))
    ])
    
    model.fit(X, y)
    
    # Evaluate on training set (basic check)
    train_score = model.score(X, y)
    logger.info(f"Training set R^2 score: {train_score:.4f}")
    
    if train_score < 0.0:
        logger.warning("Model R^2 is negative. Features may not be predictive or hyperparameters need tuning.")
    
    return model

def save_model(model: Pipeline, output_path: Path) -> None:
    """
    Saves the trained model to disk using pickle.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {output_path}")

def main():
    """
    Main entry point for T021.
    """
    # Setup logging
    ensure_log_dir(METRICS_LOG_PATH.parent)
    logger = setup_logger("train_predictor", METRICS_LOG_PATH)
    
    # Load configuration (optional, allows overriding hyperparams via .env)
    try:
        config = load_config()
    except Exception as e:
        logger.warning(f"Could not load env config: {e}. Using defaults.")
        config = {}
    
    # 1. Load Data
    try:
        df_train = load_training_data(TRAIN_INPUT_PATH)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 2. Prepare Data
    try:
        X, y = prepare_features_and_target(df_train)
    except Exception as e:
        logger.error(f"Failed to prepare features: {e}")
        sys.exit(1)
    
    # 3. Train Model
    krr_config = {
        "alpha": config.get("KRR_ALPHA", KRR_ALPHA),
        "kernel": config.get("KRR_KERNEL", KRR_KERNEL),
        "gamma": config.get("KRR_GAMMA", KRR_GAMMA)
    }
    
    try:
        model = train_krr_model(X, y, krr_config)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)
    
    # 4. Save Model
    try:
        save_model(model, MODEL_OUTPUT_PATH)
    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        sys.exit(1)
    
    logger.info("T021: Training completed successfully.")

if __name__ == "__main__":
    main()