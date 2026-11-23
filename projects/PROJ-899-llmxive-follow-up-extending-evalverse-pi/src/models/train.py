"""
Model training utilities.
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
from sklearn.linear_model import Ridge, Lasso
from xgboost import XGBRegressor
from src.config import get_data_root

logger = logging.getLogger(__name__)

def load_processed_features(input_path: Path) -> pd.DataFrame:
    """Load processed features from CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Features file not found: {input_path}")
    return pd.read_csv(input_path)

def prepare_data(
    features_df: pd.DataFrame,
    target_column: str = "human_score"
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Prepare data for training."""
    feature_cols = [col for col in features_df.columns if col != target_column]
    X = features_df[feature_cols].values
    y = features_df[target_column].values
    return X, y, feature_cols

def train_ridge(X: np.ndarray, y: np.ndarray, alpha: float = 1.0) -> Ridge:
    """Train Ridge regression model."""
    model = Ridge(alpha=alpha)
    model.fit(X, y)
    return model

def train_lasso(X: np.ndarray, y: np.ndarray, alpha: float = 0.1) -> Lasso:
    """Train Lasso regression model."""
    model = Lasso(alpha=alpha)
    model.fit(X, y)
    return model

def train_xgboost(
    X: np.ndarray, 
    y: np.ndarray, 
    n_estimators: int = 100, 
    max_depth: int = 3
) -> XGBRegressor:
    """Train XGBoost model."""
    model = XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42,
        verbosity=0
    )
    model.fit(X, y)
    return model

def save_results(
    model_name: str,
    metrics: Dict[str, float],
    output_path: Path
) -> None:
    """Save training results to JSON/CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([metrics])
    df.to_csv(output_path, index=False)

def main():
    """Main entry point for training."""
    print("Training module initialized.")
