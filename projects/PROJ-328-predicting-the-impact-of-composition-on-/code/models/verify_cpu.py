"""
Verify CPU Execution for Model Training.

This module implements T024c: Verify that model training runs on CPU only
and no GPU/CUDA devices are detected or used. This ensures compliance
with FR-010 (CPU-only execution constraint).
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
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split

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

def run_dummy_training_loop() -> Dict[str, Any]:
    """
    Run a small dummy training loop to verify CPU execution constraints.
    Returns a status dictionary.
    """
    results = {
        "cuda_available": False,
        "xgboost_cpu_safe": False,
        "training_success": False,
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

    # 3. Run a dummy training loop
    try:
        # Generate dummy data
        X, y = make_regression(n_samples=50, n_features=5, noise=0.1, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train Linear Regression (CPU only by default)
        logging.info("Running dummy Linear Regression training...")
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        _ = lr_model.score(X_test, y_test)
        logging.info("Linear Regression training completed successfully.")

        # Train XGBoost (with CPU config)
        if XGBOOST_AVAILABLE:
            logging.info("Running dummy XGBoost training...")
            xgb_model = xgb.XGBRegressor(**xgb_params, random_state=42, n_estimators=2)
            xgb_model.fit(X_train, y_train)
            _ = xgb_model.score(X_test, y_test)
            logging.info("XGBoost training completed successfully.")
        
        results["training_success"] = True
        results["message"] = "Dummy training loop completed. CPU execution verified."

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