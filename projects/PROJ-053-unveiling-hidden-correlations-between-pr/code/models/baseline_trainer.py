import os
import sys
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)

def train_linear_baseline(X_train: np.ndarray, y_train: np.ndarray) -> Tuple[LinearRegression, Dict[str, Any]]:
    """
    Train a Linear Regression baseline model.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        
    Returns:
        Tuple of (trained model, metadata dict)
    """
    logger.info("Training Linear Regression Baseline...")
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Cross-validation score (R2)
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
    mean_cv_r2 = float(np.mean(cv_scores))
    
    metadata = {
        "mean_cv_r2": mean_cv_r2,
        "cv_scores": cv_scores.tolist()
    }
    
    logger.info(f"Linear Baseline trained. Mean CV R2: {mean_cv_r2:.4f}")
    return model, metadata

def main():
    """
    CLI entry point for baseline training (for testing).
    Requires preprocessed data to be available or generated on the fly.
    """
    from data.preprocess import validate_and_preprocess
    
    try:
        X_train, X_test, y_train, y_test, metadata = validate_and_preprocess()
        model, info = train_linear_baseline(X_train, y_train)
        print("Baseline training complete.")
        print(f"Info: {info}")
        return 0
    except Exception as e:
        logger.exception(f"Baseline training failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
