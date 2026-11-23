"""
T021: Train Kernel Ridge Regression (KRR) predictor for policy gap.

Loads the stratified training data (output of T021A), trains a KRR model
to predict the calculated KL divergence (gap) from training-side features
(gradient norms, local curvature), and saves the model artifact.
"""
import os
import sys
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.kernel_ridge import KernelRidge
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Project imports
from src.config.logging_config import setup_logger, ensure_log_dir

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRAIN_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "split_train.parquet"
MODEL_OUTPUT_PATH = PROJECT_ROOT / "data" / "models" / "gap_predictor.pkl"
LOG_PATH = PROJECT_ROOT / "logs" / "pipeline.log"

# Ensure log directory exists
ensure_log_dir(LOG_PATH.parent)
logger = setup_logger(__name__, LOG_PATH)


def load_training_data(path: Path) -> pd.DataFrame:
    """
    Load the stratified training dataset from Parquet.
    
    Args:
        path: Path to the split_train.parquet file.
        
    Returns:
        DataFrame containing training samples.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Training data file not found: {path}")
    
    df = pd.read_parquet(path)
    
    required_cols = ["gradient_norms", "local_curvature", "calculated_kl_divergence"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in training data: {missing}")
        
    logger.info(f"Loaded {len(df)} training samples from {path}")
    return df


def prepare_features_and_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract feature matrix X and target vector y from the dataframe.
    
    Features are flattened from list columns if necessary, but assuming
    scalar inputs based on typical feature extraction.
    
    Args:
        df: DataFrame with feature columns.
        
    Returns:
        Tuple of (X, y) as numpy arrays.
    """
    # Extract features. Assuming gradient_norms and local_curvature are scalars.
    # If they are lists, we would need to flatten or select specific stats.
    # Based on T012/T014, they are likely scalars (L2 norm, Hutchinson estimate).
    X = df[["gradient_norms", "local_curvature"]].values.astype(np.float32)
    y = df["calculated_kl_divergence"].values.astype(np.float32)
    
    logger.info(f"Prepared features: shape {X.shape}, target: shape {y.shape}")
    return X, y


def train_krr_model(X: np.ndarray, y: np.ndarray, alpha: float = 1.0) -> KernelRidge:
    """
    Train a Kernel Ridge Regression model.
    
    Args:
        X: Feature matrix (n_samples, n_features).
        y: Target vector (n_samples,).
        alpha: Regularization parameter for KRR.
        
    Returns:
        Trained KernelRidge model.
    """
    # Scale features for better kernel performance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Initialize and train KRR with RBF kernel
    # Using RBF kernel as it's standard for non-linear regression in this context
    model = KernelRidge(kernel="rbf", alpha=alpha, gamma=0.1)
    model.fit(X_scaled, y)
    
    logger.info("KRR model trained successfully with RBF kernel.")
    
    # Return a dict containing model and scaler for proper unpickling
    return {"model": model, "scaler": scaler}


def save_model(model_artifact: Dict[str, Any], output_path: Path) -> None:
    """
    Save the trained model and scaler to a pickle file.
    
    Args:
        model_artifact: Dict containing 'model' and 'scaler'.
        output_path: Path to save the pickle file.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
    with open(output_path, "wb") as f:
        pickle.dump(model_artifact, f)
        
    logger.info(f"Model saved to {output_path}")


def main() -> int:
    """
    Main entry point for the training script.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        logger.info("Starting T021: Train Predictor Model")
        
        # 1. Load Data
        train_df = load_training_data(TRAIN_DATA_PATH)
        
        if len(train_df) == 0:
            logger.error("Training data is empty. Cannot train model.")
            return 1
        
        # 2. Prepare Features
        X, y = prepare_features_and_target(train_df)
        
        # 3. Train Model
        # Alpha can be tuned, defaulting to 1.0 as a starting point
        model_artifact = train_krr_model(X, y, alpha=1.0)
        
        # 4. Save Model
        save_model(model_artifact, MODEL_OUTPUT_PATH)
        
        logger.info("T021 completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during training: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())