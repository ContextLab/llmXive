import os
import sys
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.kernel_ridge import KernelRidge
from sklearn.preprocessing import StandardScaler

# Import project logging config
from src.config.logging_config import setup_logger, ensure_log_dir

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIN_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "split_train.parquet"
MODEL_OUTPUT_PATH = PROJECT_ROOT / "data" / "models" / "gap_predictor.pkl"
LOG_DIR = PROJECT_ROOT / "logs"

logger = logging.getLogger(__name__)

def load_training_data() -> pd.DataFrame:
    """
    Loads the stratified training dataset from the parquet file.
    Raises FileNotFoundError if the file does not exist.
    """
    if not TRAIN_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found at {TRAIN_DATA_PATH}. "
            "Ensure T021A (prepare_data_split.py) has been run successfully."
        )
    
    logger.info(f"Loading training data from {TRAIN_DATA_PATH}")
    df = pd.read_parquet(TRAIN_DATA_PATH)
    
    # Validate expected columns based on T015 schema
    required_cols = ['gradient_norms', 'local_curvature', 'calculated_kl_divergence']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in training data: {missing}")
    
    logger.info(f"Loaded {len(df)} samples for training.")
    return df

def prepare_features_and_target(df: pd.DataFrame) -> tuple:
    """
    Separates features (X) and target (y) from the dataframe.
    Features: gradient_norms, local_curvature
    Target: calculated_kl_divergence
    
    Returns:
        X (np.ndarray): Feature matrix
        y (np.ndarray): Target vector
    """
    feature_cols = ['gradient_norms', 'local_curvature']
    target_col = 'calculated_kl_divergence'
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    logger.info(f"Prepared feature matrix shape: {X.shape}, target shape: {y.shape}")
    return X, y

def train_krr_model(X: np.ndarray, y: np.ndarray) -> tuple:
    """
    Trains a Kernel Ridge Regression model.
    
    Args:
        X: Feature matrix
        y: Target vector
        
    Returns:
        model: Trained KernelRidge instance
        scaler: Fitted StandardScaler instance
    """
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Initialize KRR with default RBF kernel (alpha=1.0, gamma=0.1)
    # These can be tuned later, but defaults are a safe starting point
    model = KernelRidge(alpha=1.0, kernel='rbf', gamma=0.1)
    
    logger.info("Training Kernel Ridge Regression model...")
    model.fit(X_scaled, y)
    logger.info("Training complete.")
    
    return model, scaler

def save_model(model: KernelRidge, scaler: StandardScaler, output_path: Path) -> None:
    """
    Saves the trained model and scaler to a pickle file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    artifact = {
        'model': model,
        'scaler': scaler,
        'feature_cols': ['gradient_norms', 'local_curvature'],
        'target_col': 'calculated_kl_divergence'
    }
    
    logger.info(f"Saving model artifact to {output_path}")
    with open(output_path, 'wb') as f:
        pickle.dump(artifact, f)
    
    logger.info(f"Model saved successfully to {output_path}")

def main():
    """
    Main entry point for the training pipeline.
    """
    # Setup logging
    ensure_log_dir(LOG_DIR)
    logger.addHandler(logging.FileHandler(LOG_DIR / "pipeline.log"))
    logger.setLevel(logging.INFO)
    
    try:
        # 1. Load Data
        df = load_training_data()
        
        # 2. Prepare Features and Target
        X, y = prepare_features_and_target(df)
        
        # 3. Train Model
        model, scaler = train_krr_model(X, y)
        
        # 4. Save Artifact
        save_model(model, scaler, MODEL_OUTPUT_PATH)
        
        logger.info("T021: Training pipeline completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"T021: Training pipeline failed with error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())