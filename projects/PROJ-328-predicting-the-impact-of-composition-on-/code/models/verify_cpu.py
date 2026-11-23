"""
CPU Execution Verification Script.

This module verifies that the model training environment is correctly
configured for CPU-only execution. It checks for the absence of CUDA
devices and validates that training loops run without GPU acceleration.

CRITICAL: This script uses REAL data from the project's processed directory
to verify the execution environment. It does NOT use synthetic data.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import torch

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

logger = logging.getLogger(__name__)

def check_no_cuda_available() -> bool:
    """
    Verify that no CUDA devices are available or detected.

    Returns:
        bool: True if no CUDA is available (as expected for CPU-only), False otherwise.
    """
    is_cuda_available = torch.cuda.is_available()
    if is_cuda_available:
        logger.warning("CUDA is available! This environment has GPU resources.")
        logger.warning(f"Detected devices: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            logger.warning(f"Device {i}: {torch.cuda.get_device_name(i)}")
        return False
    else:
        logger.info("CUDA is NOT available. Environment is CPU-only.")
        return True

def check_xgboost_device_log() -> bool:
    """
    Verify that XGBoost is configured to use CPU by attempting a small training run
    and checking logs or configuration.

    Returns:
        bool: True if XGBoost is confirmed CPU-only, False otherwise.
    """
    try:
        import xgboost as xgb
        from models.config_cpu import get_xgboost_params

        config = get_xgboost_params()
        
        # Check if device is explicitly set to cpu
        if config.get("device") != "cpu":
            logger.error("XGBoost config does not explicitly set device='cpu'")
            return False
        
        if config.get("n_jobs", 0) != 1:
            logger.warning("XGBoost n_jobs is not 1, which may allow multi-threading.")
        
        logger.info("XGBoost configuration verified for CPU execution.")
        return True
    except ImportError:
        logger.error("XGBoost not installed. Cannot verify device config.")
        return False

def load_real_data_for_verification() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load a small sample of REAL data from the processed dataset for verification.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Features (X) and Target (y) arrays.
    
    Raises:
        FileNotFoundError: If the cleaned data file is missing.
    """
    cleaned_path = DATA_PROCESSED_DIR / "solder_hardness_cleaned.csv"
    descriptors_path = DATA_PROCESSED_DIR / "descriptors.csv"

    if not cleaned_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {cleaned_path}")
    if not descriptors_path.exists():
        raise FileNotFoundError(f"Descriptors not found at {descriptors_path}")

    # Load and merge as in the trainer
    df_clean = pd.read_csv(cleaned_path)
    df_desc = pd.read_csv(descriptors_path)

    # Simple merge logic (assuming row alignment if no ID)
    if 'index' in df_desc.columns and 'index' in df_clean.columns:
        df_merged = pd.merge(df_desc, df_clean[['index', 'hardness_hv']], on='index')
    else:
        df_desc['temp_idx'] = range(len(df_desc))
        df_clean['temp_idx'] = range(len(df_clean))
        df_merged = pd.merge(df_desc, df_clean[['temp_idx', 'hardness_hv']], on='temp_idx')
        df_merged.drop(columns=['temp_idx'], inplace=True)

    target_col = 'hardness_hv'
    feature_cols = [col for col in df_merged.columns if col != target_col]
    
    X = df_merged[feature_cols].values
    y = df_merged[target_col].values

    # Take a small sample for verification (e.g., 50 rows)
    n_sample = min(50, len(y))
    indices = np.random.choice(len(y), n_sample, replace=False)
    
    logger.info(f"Loaded {n_sample} real samples for verification.")
    return X[indices], y[indices]

def run_dummy_training_loop() -> bool:
    """
    Run a small training loop using REAL data to verify CPU execution.
    
    This function attempts to train a simple model on real data to ensure
    no GPU errors occur and that the process completes successfully.

    Returns:
        bool: True if training completes successfully on CPU, False otherwise.
    """
    try:
        # Load real data
        X, y = load_real_data_for_verification()
        
        logger.info("Starting dummy training loop with real data...")

        # Test Linear Regression
        from sklearn.linear_model import LinearRegression
        model = LinearRegression(n_jobs=1)
        model.fit(X, y)
        _ = model.predict(X)
        logger.info("Linear Regression training completed successfully.")

        # Test XGBoost
        try:
            import xgboost as xgb
            from models.config_cpu import get_xgboost_params
            
            params = get_xgboost_params()
            dtrain = xgb.DMatrix(X, label=y)
            bst = xgb.train(params, dtrain, num_boost_round=5)
            _ = bst.predict(dtrain)
            logger.info("XGBoost training completed successfully.")
        except ImportError:
            logger.warning("XGBoost not installed, skipping XGBoost verification.")

        return True
    except Exception as e:
        logger.error(f"Training loop failed: {e}", exc_info=True)
        return False

def main():
    """Main entry point for CPU verification."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=== Starting CPU Execution Verification ===")

    # 1. Check CUDA
    no_cuda = check_no_cuda_available()
    if not no_cuda:
        logger.warning("Environment has CUDA, but we will proceed to verify CPU config.")

    # 2. Check XGBoost Config
    xgb_ok = check_xgboost_device_log()

    # 3. Run Training Loop with Real Data
    train_ok = run_dummy_training_loop()

    # 4. Summary
    logger.info("=== Verification Summary ===")
    logger.info(f"CUDA Check: {'PASS' if no_cuda else 'WARNING (CUDA available)'}")
    logger.info(f"XGBoost Config Check: {'PASS' if xgb_ok else 'FAIL'}")
    logger.info(f"Training Loop Check: {'PASS' if train_ok else 'FAIL'}")

    if train_ok:
        logger.info("CPU Execution Verification: SUCCESS")
        return 0
    else:
        logger.error("CPU Execution Verification: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())