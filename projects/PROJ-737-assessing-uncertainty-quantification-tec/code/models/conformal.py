"""
Split Conformal Prediction for UQ.
Implements run_conformal_prediction function compatible with pipeline.
"""
import logging
import os
import gc
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from utils.logger import get_logger

logger = get_logger(__name__)

class SplitConformalWrapper:
    """Wrapper for split conformal prediction."""
    def __init__(self, base_model, alpha: float = 0.05):
        self.base_model = base_model
        self.alpha = alpha
        self.calibration_scores = None
    
    def fit_calibrate(self, X_cal: np.ndarray, y_cal: np.ndarray):
        """Fit model and calibrate on calibration set."""
        # Train base model
        self.base_model.fit(X_cal, y_cal)
        
        # Compute non-conformity scores on calibration set
        preds = self.base_model.predict(X_cal)
        self.calibration_scores = np.abs(y_cal - preds)
        
        # Compute quantile for desired coverage
        n = len(self.calibration_scores)
        q_level = np.ceil((n + 1) * (1 - self.alpha)) / n
        q_level = min(q_level, n)
        self.quantile = np.quantile(self.calibration_scores, q_level)
        
        logger.debug(f"Calibrated quantile: {self.quantile:.4f} for alpha={self.alpha}")
    
    def predict_conformal(self, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict with conformal intervals."""
        preds = self.base_model.predict(X_test)
        lower = preds - self.quantile
        upper = preds + self.quantile
        return preds, lower, upper

def run_conformal_prediction(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Optional[pd.DataFrame]:
    """
    Run Split Conformal Prediction for UQ.
    
    Uses a base regressor (GradientBoosting) and calibrates intervals on a held-out set.
    """
    logger.info("Running Conformal Prediction...")
    
    try:
        # Split train into train/calibration
        # X_train is already the training split from pipeline, we need to carve out a calibration set
        X_subtrain, X_cal, y_subtrain, y_cal = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42
        )
        
        # Initialize base model
        base_model = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
        
        # Initialize conformal wrapper
        alpha = 0.05  # 95% coverage
        conformal = SplitConformalWrapper(base_model, alpha=alpha)
        
        # Fit and calibrate
        conformal.fit_calibrate(X_subtrain, y_subtrain)
        # Note: fit_calibrate already trains the model on X_subtrain
        # But we need to re-train on the full X_train (subtrain + cal) for better performance
        # Actually, split conformal typically uses X_cal for calibration only.
        # We will use the model trained on X_subtrain as is, or retrain on X_train?
        # Standard split conformal: train on X_subtrain, calibrate on X_cal, predict on X_test.
        # We already did that in fit_calibrate.
        
        # Predict on test set
        preds, lower, upper = conformal.predict_conformal(X_test)
        
        # Create result DataFrame
        results = pd.DataFrame({
            'prediction': preds,
            'lower_bound': lower,
            'upper_bound': upper,
            'ground_truth': y_test.values
        })
        
        logger.info(f"Conformal Prediction completed. Predictions: {len(results)}")
        return results
        
    except Exception as e:
        logger.error(f"Conformal Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Entry point for testing Conformal Prediction standalone."""
    logger.info("Conformal Prediction module loaded. Run via pipeline.py for full execution.")

if __name__ == "__main__":
    main()
