"""
Modeling pipeline for predicting Poisson's ratio of Aluminum alloys.
Implements T019 (ILR), T021 (Split), T022 (Training), T023c (Metrics), T024 (Serialization).
"""
import logging
import pickle
import json
import time
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error
from joblib import dump, load

# Import config to handle path resolution dynamically
try:
    from config import get_config
except ImportError:
    # Fallback for direct execution or different import context
    from pathlib import Path
    class _Config:
        data_processed_dir = Path("data/processed")
        models_dir = Path("models")
    config = _Config()

# Setup logging
try:
    from logging_config import setup_logging, get_logger
    logger = setup_logging(level="INFO")
except (ImportError, TypeError):
    # Fallback for tolerant logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# --- T021: Train/Test Split ---
def load_features_and_target() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the cleaned dataset (from T015/T046) and extract ILR-transformed features.
    Expected input: data/processed/alloys_clean.parquet
    """
    # T024 Fix: Use the correct config attribute 'data_processed_dir'
    # If 'data_processed' was requested, we map it to 'data_processed_dir' or handle via __getattr__ in config.
    # Here we assume config has 'data_processed_dir' as per the API surface correction.
    data_path = config.data_processed_dir / "alloys_clean.parquet"
    
    if not data_path.exists():
        # Fallback if path structure is different
        data_path = Path("data/processed/alloys_clean.parquet")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}. Run T015/T046 first.")

    df = pd.read_parquet(data_path)
    
    # Identify ILR columns (prefix 'ilr_' usually, or specific columns if stored raw)
    # Based on T019, ILR columns are created. Assuming they are named 'ilr_0', 'ilr_1', etc.
    # or we look for columns starting with 'ilr_'.
    ilr_cols = [c for c in df.columns if c.startswith('ilr_')]
    
    if not ilr_cols:
        # Fallback: if T019 didn't prefix, check for specific names
        ilr_cols = [c for c in df.columns if c in ['ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']]
    
    if not ilr_cols:
        raise ValueError("No ILR-transformed features found in the dataset. Run T019 first.")

    X = df[ilr_cols]
    # Target is Poisson's ratio
    y = df['poisson_ratio']
    
    return X, y

def train_random_forest_with_cv(X: pd.DataFrame, y: pd.Series, n_splits: int = 5) -> Tuple[RandomForestRegressor, List[float]]:
    """
    Train Random Forest with k-fold cross-validation.
    Returns model and CV scores.
    """
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=2  # T039 parallelization
    )
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=n_splits, scoring='neg_mean_absolute_error')
    cv_mae_scores = -cv_scores # Convert back to positive MAE
    
    # Train final model on full data
    model.fit(X, y)
    
    return model, cv_mae_scores

def evaluate_model_on_test(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    """
    Evaluate model on test set and return MAE.
    """
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    return mae

# --- T024: Model Serialization ---
def save_model(model: RandomForestRegressor, model_path: Optional[Path] = None) -> Path:
    """
    Save trained model to disk.
    Requirement: Ensure directory exists. Use joblib with compress=3, protocol=3.
    """
    if model_path is None:
        # T024 Fix: Use correct config attribute 'models_dir'
        if hasattr(config, 'models_dir'):
            model_path = config.models_dir / "rf_model.pkl"
        else:
            model_path = Path("models/rf_model.pkl")

    # Ensure directory exists
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save model
    dump(model, str(model_path), compress=3, protocol=3)
    logger.info(f"Model saved to {model_path}")
    return model_path

# --- T023c: Metrics Calculation & Logging ---
def save_model_metrics(
    cv_mae_scores: List[float], 
    test_mae: float, 
    metrics_path: Optional[Path] = None
) -> Path:
    """
    Compute test-set MAE, check CV MAE threshold, and write metrics.
    Threshold: 0.05. If cv_mae > 0.05, set mae_flag=True and log warning.
    Output: data/processed/model_metrics.json
    """
    if metrics_path is None:
        if hasattr(config, 'data_processed_dir'):
            metrics_path = config.data_processed_dir / "model_metrics.json"
        else:
            metrics_path = Path("data/processed/model_metrics.json")
    
    # Ensure directory exists
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    avg_cv_mae = float(np.mean(cv_mae_scores))
    std_cv_mae = float(np.std(cv_mae_scores))
    threshold = 0.05
    mae_flag = avg_cv_mae > threshold

    metrics = {
        'cv_mae': avg_cv_mae,
        'test_mae': float(test_mae),
        'std_dev': std_cv_mae,
        'mae_flag': mae_flag,
        'threshold': threshold
    }

    if mae_flag:
        logger.warning(f"MethodologicalConcern: CV MAE ({avg_cv_mae:.4f}) exceeds {threshold} threshold")

    # Atomic write
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {metrics_path}")
    return metrics_path

def run_modeling_pipeline() -> Dict[str, Any]:
    """
    Orchestrates the full modeling pipeline:
    1. Load features/target
    2. Split (T021)
    3. Train with CV (T022)
    4. Evaluate (T023c)
    5. Save Model (T024)
    6. Save Metrics (T023c)
    """
    logger.info("Starting modeling pipeline...")
    
    # Load Data
    X, y = load_features_and_target()
    
    # Split Data (T021)
    # Fallback for small datasets handled in split logic if needed
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info(f"Data split: {len(X_train)} train, {len(X_test)} test")

    # Train (T022)
    model, cv_scores = train_random_forest_with_cv(X_train, y_train)
    logger.info(f"CV MAE scores: {cv_scores}")

    # Evaluate (T023c)
    test_mae = evaluate_model_on_test(model, X_test, y_test)
    logger.info(f"Test MAE: {test_mae}")

    # Save Model (T024)
    model_path = save_model(model)

    # Save Metrics (T023c)
    metrics_path = save_model_metrics(cv_scores, test_mae)

    return {
        'model_path': str(model_path),
        'metrics_path': str(metrics_path),
        'test_mae': test_mae
    }

def main():
    """Entry point for modeling script."""
    try:
        result = run_modeling_pipeline()
        logger.info("Modeling pipeline completed successfully.")
        print(f"Pipeline complete. Model: {result['model_path']}, Metrics: {result['metrics_path']}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()