"""
Baseline model for crack propagation prediction.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from code.logging_config import get_logger

logger = get_logger(__name__)

def train_baseline_model(X: np.ndarray, y: np.ndarray) -> LinearRegression:
    """
    Train a baseline linear regression model.
    
    Args:
        X: Feature matrix (log-transformed delta_K)
        y: Target vector (log-transformed da/dN)
        
    Returns:
        Trained LinearRegression model
    """
    logger.info("Training baseline model")
    model = LinearRegression()
    model.fit(X, y)
    logger.info(f"Baseline model trained. R²: {model.score(X, y):.4f}")
    return model

def evaluate_baseline(model: LinearRegression, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Evaluate the baseline model.
    
    Args:
        model: Trained LinearRegression model
        X: Feature matrix
        y: Target vector
        
    Returns:
        Dictionary of evaluation metrics
    """
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(np.mean((y - y_pred) ** 2))
    
    logger.info(f"Baseline evaluation - R²: {r2:.4f}, RMSE: {rmse:.4f}")
    return {
        "r2": r2,
        "rmse": rmse,
        "mse": np.mean((y - y_pred) ** 2)
    }
