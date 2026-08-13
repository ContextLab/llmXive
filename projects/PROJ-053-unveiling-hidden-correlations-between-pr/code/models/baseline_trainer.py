import os
import sys
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

logger = logging.getLogger(__name__)

def train_linear_baseline(X_train: np.ndarray, y_train: np.ndarray) -> LinearRegression:
    """
    Train a Linear Regression model on the provided training data.
    
    Args:
        X_train: Scaled training features.
        y_train: Training targets.
        
    Returns:
        Trained LinearRegression model.
    """
    logger.info("Training Linear Regression Baseline...")
    model = LinearRegression()
    model.fit(X_train, y_train)
    logger.info("Linear Regression Baseline training complete.")
    return model

def main():
    """
    Main entry point for baseline training (standalone test).
    In the full pipeline, this is called by main_save.py.
    """
    logger.warning("baseline_trainer.py main() is not intended for standalone execution without data loading.")
    logger.warning("Please use main_save.py for the full pipeline.")

if __name__ == "__main__":
    main()
