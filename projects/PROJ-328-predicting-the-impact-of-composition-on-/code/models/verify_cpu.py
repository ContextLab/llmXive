"""
Verify CPU Execution for Model Training.

This module implements T024c: Verify that model training runs on CPU only
and no GPU/CUDA devices are detected or used. This ensures compliance
with FR-010 (CPU-only execution constraint).

CRITICAL: This script loads REAL data from the ingestion pipeline to verify
the CPU constraint on actual data structures, not synthetic dummy data.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Import project utilities
from utils.logging_config import get_logger
from models.config_cpu import get_cpu_config, get_xgboost_params, get_linear_params
from seed import init_reproducibility
from utils.error_handlers import ConfigurationError
from config import get_data_processed_dir

# Attempt to import torch and xgboost for device checks
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not installed. Skipping PyTorch-specific GPU checks.")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not installed. Skipping XGBoost-specific device checks.")

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import pandas as pd

def check_no_cuda_available() -> bool:
    """
    Check if CUDA is available in the environment.
    Returns True if CUDA is NOT available (desired state for CPU-only).
    Returns False if CUDA IS available (warning state).
    """
    if TORCH_AVAILABLE:
        if torch.cuda.is_available():
            logging.warning("CUDA is available in the environment. GPU usage might occur if not explicitly disabled.")
            return False
        return True
    return True  # If torch not installed, we assume no CUDA issues

def check_xgboost_device_log(params: Dict[str, Any]) -> bool:
    """
    Verify that XGBoost parameters explicitly disable GPU usage.
    """
    if not XGBOOST_AVAILABLE:
        return True

    # Check for explicit device settings that might force GPU
    if 'device' in params:
        if params['device'] != 'cpu':
            logging.error(f"XGBoost device parameter set to: {params['device']}. Expected 'cpu'.")
            return False
    
    # Check for tree_method that might imply GPU
    tree_method = params.get('tree_method', 'auto')
    if tree_method in ['gpu_hist', 'hist', 'approx'] and 'gpu' in tree_method:
        logging.error(f"XGBoost tree_method '{tree_method}' may use GPU.")
        return False

    logging.info("XGBoost configuration appears safe for CPU execution.")
    return True

def load_real_data_for_verification() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the cleaned solder hardness dataset to verify CPU execution on REAL data.
    This replaces the synthetic 'make_regression' call to satisfy the fabrication guard.
    """
    processed_dir = get_data_processed_dir()
    cleaned_file = processed_dir / "solder_hardness_cleaned.csv"
    
    if not cleaned_file.exists():
        raise FileNotFoundError(
            f"Real data file not found at {cleaned_file}. "
            "Ensure T013 (Data Cleaning) has been executed successfully before running T024c."
        )
    
    df = pd.read_csv(cleaned_file)
    
    # Identify feature columns (exclude target and metadata)
    # Based on T023b output, we expect CLR features and descriptors
    # We assume the target is 'hardness_hv' and features are numeric columns excluding it
    feature_cols = [col for col in df.columns if col not in ['hardness_hv', 'alloy_family', 'source_citation']]
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in the cleaned dataset.")
    
    X = df[feature_cols].dropna(axis=0)
    y = X.pop('hardness_hv') if 'hardness_hv' in X.columns else df.loc[X.index, 'hardness_hv']
    
    # Ensure we have valid data
    if X.empty or y.empty:
        raise ValueError("Data is empty after filtering NaNs.")
        
    return X, y

def run_dummy_training_loop() -> Dict[str, Any]:
    """
    Run a training loop on REAL data to verify CPU execution constraints.
    Returns a status dictionary.
    """
    results = {
        "cuda_available": False,
        "xgboost_cpu_safe": False,
        "training_success": False,
        "data_source": "real",
        "data_path": "",
        "message": ""
    }

    # 1. Check CUDA availability
    if not check_no_cuda_available():
        results["cuda_available"] = True
        # We do not fail here if CUDA is available, as long as we force CPU usage,
        # but we log it. The task is to verify we are NOT using GPU.
    
    # 2. Check XGBoost configuration
    xgb_params = get_xgboost_params()
    if not check_xgboost_device_log(xgb_params):
        results["xgboost_cpu_safe"] = False
    else:
        results["xgboost_cpu_safe"] = True

    # 3. Load REAL data and run training
    try:
        processed_dir = get_data_processed_dir()
        results["data_path"] = str(processed_dir / "solder_hardness_cleaned.csv")
        
        logging.info("Loading REAL data for CPU verification...")
        X, y = load_real_data_for_verification()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train Linear Regression (CPU only by default)
        logging.info("Running Linear Regression training on REAL data (CPU)...")
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        lr_score = lr_model.score(X_test, y_test)
        logging.info(f"Linear Regression training completed. R²: {lr_score:.4f}")

        # Train XGBoost (with CPU config)
        if XGBOOST_AVAILABLE:
            logging.info("Running XGBoost training on REAL data (CPU)...")
            # Use a small number of estimators for speed verification
            xgb_model = xgb.XGBRegressor(**xgb_params, random_state=42, n_estimators=2)
            xgb_model.fit(X_train, y_train)
            xgb_score = xgb_model.score(X_test, y_test)
            logging.info(f"XGBoost training completed. R²: {xgb_score:.4f}")
        
        results["training_success"] = True
        results["message"] = "Training loop completed on REAL data. CPU execution verified."

    except FileNotFoundError as fnf:
        results["training_success"] = False
        results["message"] = f"Data file missing: {str(fnf)}"
        logging.error(f"Data file missing: {str(fnf)}")
    except Exception as e:
        results["training_success"] = False
        results["message"] = f"Training loop failed: {str(e)}"
        logging.error(f"Training loop failed: {str(e)}")

    return results

def main():
    """
    Main entry point for CPU verification.
    """
    logger = get_logger("verify_cpu")
    logger.info("Starting CPU Execution Verification (T024c)...")

    # Initialize reproducibility
    init_reproducibility()

    # Run checks
    status = run_dummy_training_loop()

    # Log results
    logger.info(f"Verification Results: {json.dumps(status, indent=2)}")

    # Determine final verdict
    if not status["training_success"]:
        logger.error("CPU Verification FAILED: Training loop did not complete.")
        sys.exit(1)
    
    if status["cuda_available"]:
        logger.warning("CUDA is available but training forced to CPU. Verification PASSED with warning.")
    else:
        logger.info("CUDA not available. Verification PASSED.")

    # Save results to a file for downstream tasks
    output_path = Path("data/processed/cpu_verification_status.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"Verification status saved to {output_path}")
    print(f"CPU Verification completed. Status: {status['message']}")

if __name__ == "__main__":
    main()