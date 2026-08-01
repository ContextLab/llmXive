import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import cross_val_score
import xgboost as xgb

from src.config import get_processed_data_dir, get_state_root
from src.utils import write_json

logger = logging.getLogger(__name__)

def load_processed_features(file_path: Optional[str] = None) -> pd.DataFrame:
    if file_path is None:
        file_path = get_processed_data_dir() / "features.csv"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Processed features file not found: {file_path}")
    return pd.read_csv(file_path)

def prepare_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    # Assume columns 'optical_flow_mean', 'optical_flow_var', 'audio_spectral', 'audio_zcr' exist
    feature_cols = [c for c in df.columns if c not in ['clip_id', 'human_score']]
    X = df[feature_cols].values
    y = df['human_score'].values
    return X, y, feature_cols

def train_ridge(X: np.ndarray, y: np.ndarray, alpha: float = 1.0) -> Ridge:
    model = Ridge(alpha=alpha)
    model.fit(X, y)
    return model

def train_lasso(X: np.ndarray, y: np.ndarray, alpha: float = 0.1) -> Lasso:
    model = Lasso(alpha=alpha, max_iter=10000)
    model.fit(X, y)
    return model

def train_xgboost(X: np.ndarray, y: np.ndarray, n_estimators: int = 100) -> xgb.XGBRegressor:
    model = xgb.XGBRegressor(n_estimators=n_estimators, random_state=42)
    model.fit(X, y)
    return model

def save_results(results: Dict[str, Any], output_file: Optional[str] = None):
    if output_file is None:
        output_file = get_state_root() / "model_results.json"
    write_json(output_file, results)

def main():
    """
    Main training pipeline entry point.
    Loads data, trains models, and saves results.
    """
    logger.info("Starting model training...")
    
    # Load data
    df = load_processed_features()
    X, y, feature_cols = prepare_data(df)
    
    # Train models
    ridge_model = train_ridge(X, y)
    lasso_model = train_lasso(X, y)
    xgb_model = train_xgboost(X, y)
    
    # Calculate simple scores (R^2)
    scores = {
        "ridge_r2": ridge_model.score(X, y),
        "lasso_r2": lasso_model.score(X, y),
        "xgb_r2": xgb_model.score(X, y)
    }
    
    logger.info(f"Training complete. Scores: {scores}")
    save_results(scores)

if __name__ == "__main__":
    main()
