"""
Gaussian Process Regressor for UQ.
Implements run_gpr function compatible with pipeline.
"""
import logging
import os
import gc
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.preprocessing import StandardScaler
from utils.logger import get_logger, log_convergence_failure

logger = get_logger(__name__)

def run_gpr(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Optional[pd.DataFrame]:
    """
    Run Gaussian Process Regressor with uncertainty quantification.
    
    Args:
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        
    Returns:
        DataFrame with predictions and uncertainty bounds
    """
    logger.info("Running GPR model...")
    
    try:
        # Handle convergence warnings
        import warnings
        from sklearn.exceptions import ConvergenceWarning
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        
        # Standardize features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Define kernel: Constant * RBF
        kernel = C(1.0) * RBF(1.0)
        
        # Initialize GPR
        gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, random_state=42)
        
        # Train
        gpr.fit(X_train_scaled, y_train)
        
        # Predict with uncertainty (mean and std)
        y_pred_mean, y_pred_std = gpr.predict(X_test_scaled, return_std=True)
        
        # Convert std to 95% confidence interval (approx 1.96 * std)
        # For 95% CI: mean +/- 1.96 * std
        alpha = 1.96
        lower_bound = y_pred_mean - alpha * y_pred_std
        upper_bound = y_pred_mean + alpha * y_pred_std
        
        # Create result DataFrame
        results = pd.DataFrame({
            'prediction': y_pred_mean,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'ground_truth': y_test.values
        })
        
        logger.info(f"GPR completed. Predictions: {len(results)}")
        return results
        
    except Exception as e:
        logger.error(f"GPR failed: {e}")
        log_convergence_failure("GPR", str(e))
        return None

def main():
    """Entry point for testing GPR standalone."""
    # This is a placeholder for standalone testing
    logger.info("GPR module loaded. Run via pipeline.py for full execution.")

if __name__ == "__main__":
    main()
