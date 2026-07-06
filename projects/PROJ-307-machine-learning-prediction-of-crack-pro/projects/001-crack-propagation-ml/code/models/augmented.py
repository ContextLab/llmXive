"""
Augmented models for crack propagation prediction.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from code.logging_config import get_logger

logger = get_logger(__name__)

def train_random_forest(X: np.ndarray, y: np.ndarray, **params) -> RandomForestRegressor:
    """
    Train a Random Forest model.
    
    Args:
        X: Feature matrix
        y: Target vector
        **params: Additional parameters for RandomForestRegressor
        
    Returns:
        Trained RandomForestRegressor model
    """
    logger.info("Training Random Forest model")
    model = RandomForestRegressor(random_state=42, **params)
    model.fit(X, y)
    logger.info(f"Random Forest trained. R²: {model.score(X, y):.4f}")
    return model

def train_xgboost(X: np.ndarray, y: np.ndarray, **params) -> Any:
    """
    Train an XGBoost model.
    
    Args:
        X: Feature matrix
        y: Target vector
        **params: Additional parameters for XGBRegressor
        
    Returns:
        Trained XGBRegressor model
    """
    try:
        from xgboost import XGBRegressor
        logger.info("Training XGBoost model")
        model = XGBRegressor(random_state=42, **params)
        model.fit(X, y)
        logger.info(f"XGBoost trained. R²: {model.score(X, y):.4f}")
        return model
    except ImportError:
        logger.warning("XGBoost not available, falling back to Random Forest")
        return train_random_forest(X, y, **params)

def train_augmented_model(
    X: np.ndarray, 
    y: np.ndarray, 
    model_type: str = "random_forest",
    **params
) -> Union[RandomForestRegressor, Any]:
    """
    Train an augmented model based on type.
    
    Args:
        X: Feature matrix
        y: Target vector
        model_type: Type of model ("random_forest" or "xgboost")
        **params: Additional parameters
        
    Returns:
        Trained model
    """
    if model_type == "xgboost":
        return train_xgboost(X, y, **params)
    else:
        return train_random_forest(X, y, **params)

def predict(model: Union[RandomForestRegressor, Any], X: np.ndarray) -> np.ndarray:
    """
    Make predictions using the trained model.
    
    Args:
        model: Trained model
        X: Feature matrix
        
    Returns:
        Predictions
    """
    return model.predict(X)

def evaluate_model(model: Union[RandomForestRegressor, Any], X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Evaluate the augmented model.
    
    Args:
        model: Trained model
        X: Feature matrix
        y: Target vector
        
    Returns:
        Dictionary of evaluation metrics
    """
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(np.mean((y - y_pred) ** 2))
    
    logger.info(f"Augmented model evaluation - R²: {r2:.4f}, RMSE: {rmse:.4f}")
    return {
        "r2": r2,
        "rmse": rmse,
        "mse": np.mean((y - y_pred) ** 2)
    }
