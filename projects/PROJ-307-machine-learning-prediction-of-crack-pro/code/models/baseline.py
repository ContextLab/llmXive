"""
Baseline model implementation (Linear Regression on log-log data).
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)

def train_baseline_model(X: np.ndarray, y: np.ndarray) -> LinearRegression:
    """Train a baseline linear regression model."""
    model = LinearRegression()
    model.fit(X, y)
    return model

def evaluate_baseline(model: LinearRegression, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """Evaluate baseline model performance."""
    preds = model.predict(X)
    from sklearn.metrics import r2_score
    r2 = r2_score(y, preds)
    return {"r2": r2}
