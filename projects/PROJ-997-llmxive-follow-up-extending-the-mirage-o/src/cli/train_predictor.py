import os
import sys
import logging
import argparse
import joblib
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
from sklearn.kernel_ridge import KernelRidge
from sklearn.preprocessing import StandardScaler

# Add project root to path if running as script
_project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_project_root))

from src.config.logging_config import setup_logger
from src.config.env_config import load_config

logger = setup_logger("train_predictor", log_file="logs/pipeline.log")

def load_train_data(data_path: str) -> pd.DataFrame:
    """
    Load the stratified training parquet file.
    Expects columns: gradient_norms, local_curvature, calculated_kl_divergence
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Training data not found at {data_path}")
    
    logger.info(f"Loading training data from {data_path}")
    df = pd.read_parquet(path)
    
    required_cols = ['gradient_norms', 'local_curvature', 'calculated_kl_divergence']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in training data: {missing}")
    
    logger.info(f"Loaded {len(df)} samples. Columns: {list(df.columns)}")
    return df

def prepare_features_targets(df: pd.DataFrame):
    """
    Separate features (X) and target (y).
    X: gradient_norms, local_curvature
    y: calculated_kl_divergence
    """
    feature_cols = ['gradient_norms', 'local_curvature']
    target_col = 'calculated_kl_divergence'
    
    X = df[feature_cols].values.astype(np.float64)
    y = df[target_col].values.astype(np.float64)
    
    return X, y

def train_kernel_ridge(X: np.ndarray, y: np.ndarray, alpha: float = 1.0) -> tuple:
    """
    Train a KernelRidge model with RBF kernel.
    Returns the trained model and the scaler used for normalization.
    """
    logger.info("Training KernelRidge model...")
    
    # Normalize features for better RBF kernel performance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = KernelRidge(kernel='rbf', alpha=alpha, gamma=0.1)
    model.fit(X_scaled, y)
    
    logger.info(f"Training complete. Alpha: {alpha}")
    return model, scaler

def save_model(model, scaler, output_path: str):
    """
    Save the trained model and scaler to disk.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    artifact = {
        'model': model,
        'scaler': scaler,
        'feature_cols': ['gradient_norms', 'local_curvature'],
        'target_col': 'calculated_kl_divergence'
    }
    
    joblib.dump(artifact, str(path))
    logger.info(f"Model saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train the Gap Prediction Model (KRR)")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/train.parquet",
        help="Path to the stratified training parquet file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/models/gap_predictor.pkl",
        help="Path to save the trained model artifact"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=1.0,
        help="Regularization parameter for KernelRidge"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting predictor training pipeline...")
    
    try:
        # 1. Load Data
        df = load_train_data(args.input)
        
        # 2. Prepare Features and Targets
        X, y = prepare_features_targets(df)
        logger.info(f"Feature matrix shape: {X.shape}, Target vector shape: {y.shape}")
        
        # 3. Train Model
        model, scaler = train_kernel_ridge(X, y, alpha=args.alpha)
        
        # 4. Save Artifact
        save_model(model, scaler, args.output)
        
        logger.info("Training pipeline completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data schema error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()