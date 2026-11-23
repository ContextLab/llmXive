import os
import sys
import json
import time
import traceback
from typing import Dict, Any, Tuple, Optional, List

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
import joblib

from utils.logging import get_logger, set_seeds, get_seed
from utils.timer import start_phase, stop_phase
from utils.config import get_config

logger = get_logger(__name__)

# Constants
DATA_PATH = "data/processed/hea_descriptors.csv"
OUTPUT_DIR = "output"
MODELS_DIR = "output/models"
SPLIT_INFO_PATH = os.path.join(OUTPUT_DIR, "split_info.json")
METRICS_PATH = os.path.join(OUTPUT_DIR, "metrics.json")
MODEL_PATH = os.path.join(MODELS_DIR, "model.joblib")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

def load_processed_data(path: str = DATA_PATH) -> pd.DataFrame:
    """Load the processed descriptor data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found: {path}")
    logger.info(f"Loading processed data from {path}")
    return pd.read_csv(path)

def prepare_features_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Separate features (descriptors) and target (yield strength)."""
    # Target column is expected to be 'yield_strength_mpa' based on T010/T015
    target_col = 'yield_strength_mpa'
    if target_col not in df.columns:
        # Fallback if column name differs, though spec implies normalization happened
        possible_targets = [c for c in df.columns if 'yield' in c.lower() or 'strength' in c.lower()]
        if possible_targets:
            target_col = possible_targets[0]
            logger.warning(f"Target column '{target_col}' not found, using {target_col}")
        else:
            raise ValueError("Could not identify target column in dataframe")

    features = [c for c in df.columns if c != target_col and c not in ['composition', 'phase', 'phase_type']]
    # Ensure we have features
    if not features:
        raise ValueError("No feature columns found in dataframe")

    X = df[features].values
    y = df[target_col].values
    return X, y, features

def create_stratified_split(X: np.ndarray, y: np.ndarray, test_size: float = 0.2, seed: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a stratified train/test split.
    Note: True stratification on continuous targets is often done by binning.
    Here we bin the target into quantiles for stratification purposes.
    """
    # Bin y into 10 quantiles for stratification
    y_bins = pd.qcut(y, q=10, labels=False, duplicates='drop')
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y_bins
    )
    logger.info(f"Train set size: {len(X_train)}, Test set size: {len(X_test)}")
    return X_train, X_test, y_train, y_test

def save_split_info(X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray, features: List[str], path: str = SPLIT_INFO_PATH):
    """Save split metadata."""
    info = {
        "train_size": len(X_train),
        "test_size": len(X_test),
        "features": features,
        "seed": get_seed()
    }
    with open(path, 'w') as f:
        json.dump(info, f, indent=2)
    logger.info(f"Split info saved to {path}")

def train_linear_regression(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, features: List[str]) -> Dict[str, Any]:
    """Train Linear Regression baseline."""
    phase_name = "Linear Regression Training"
    start_phase(phase_name)
    logger.info("Training Linear Regression baseline...")
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    metrics = {
        "r2": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }
    
    stop_phase(phase_name)
    return {"model": model, "metrics": metrics, "type": "linear"}

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, features: List[str]) -> Dict[str, Any]:
    """
    Train Random Forest with fixed hyperparameters and parallelism.
    n_estimators=500, max_features='sqrt', random_state=42, n_jobs=-1
    """
    phase_name = "Random Forest Training"
    start_phase(phase_name)
    logger.info("Training Random Forest (n_estimators=500, n_jobs=-1)...")
    
    # CRITICAL: n_jobs=-1 for maximum CPU utilization
    # random_state=42 ensures deterministic behavior
    model = RandomForestRegressor(
        n_estimators=500,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1,  # Use all available CPUs
        verbose=1   # Log progress
    )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    metrics = {
        "r2": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }
    
    stop_phase(phase_name)
    return {"model": model, "metrics": metrics, "type": "rf"}

def train_gradient_boosting(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, features: List[str]) -> Dict[str, Any]:
    """
    Train Gradient Boosting with 5-fold CV and grid search.
    trees: 10-50, max_depth <= 10.
    """
    phase_name = "Gradient Boosting Training"
    start_phase(phase_name)
    logger.info("Training Gradient Boosting with GridSearchCV...")
    
    param_grid = {
        'n_estimators': [10, 20, 30, 40, 50],
        'max_depth': [3, 5, 7, 10],
        'learning_rate': [0.1, 0.05]
    }
    
    gb_base = GradientBoostingRegressor(random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    # Note: y for StratifiedKFold needs to be binned for regression
    y_bins = pd.qcut(y_train, q=5, labels=False, duplicates='drop')
    
    grid_search = GridSearchCV(
        gb_base,
        param_grid,
        cv=cv,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    logger.info(f"Best GB params: {grid_search.best_params_}")
    
    y_pred = best_model.predict(X_test)
    metrics = {
        "r2": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }
    
    stop_phase(phase_name)
    return {"model": best_model, "metrics": metrics, "type": "gb", "best_params": grid_search.best_params_}

def evaluate_model(model_dict: Dict[str, Any], X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
    """Re-evaluate model (wrapper for consistency)."""
    model = model_dict['model']
    y_pred = model.predict(X_test)
    metrics = {
        "r2": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }
    return {**model_dict, "metrics": metrics}

def run_training_pipeline():
    """Execute the full training pipeline."""
    logger.info("Starting training pipeline...")
    set_seeds(42)
    
    try:
        # 1. Load Data
        df = load_processed_data()
        X, y, features = prepare_features_target(df)
        
        # 2. Split Data
        X_train, X_test, y_train, y_test = create_stratified_split(X, y)
        save_split_info(X_train, X_test, y_train, y_test, features)
        
        # 3. Train Models
        results = {}
        
        # Linear
        lr_result = train_linear_regression(X_train, y_train, X_test, y_test, features)
        results['linear'] = lr_result
        
        # Random Forest (Parallelized)
        rf_result = train_random_forest(X_train, y_train, X_test, y_test, features)
        results['rf'] = rf_result
        
        # Gradient Boosting
        gb_result = train_gradient_boosting(X_train, y_train, X_test, y_test, features)
        results['gb'] = gb_result
        
        # 4. Save Metrics
        metrics_output = {
            "linear": results['linear']['metrics'],
            "rf": results['rf']['metrics'],
            "gb": results['gb']['metrics'],
            "best_model": "rf" if results['rf']['metrics']['r2'] > results['gb']['metrics']['r2'] else "gb"
        }
        
        with open(METRICS_PATH, 'w') as f:
            json.dump(metrics_output, f, indent=2)
        logger.info(f"Metrics saved to {METRICS_PATH}")
        
        # 5. Save Best Model
        best_key = metrics_output['best_model']
        best_model_obj = results[best_key]['model']
        joblib.dump(best_model_obj, MODEL_PATH)
        logger.info(f"Best model ({best_key}) saved to {MODEL_PATH}")
        
        # 6. Return summary
        return metrics_output
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        traceback.print_exc()
        raise

def main():
    """Entry point for the training script."""
    run_training_pipeline()

if __name__ == "__main__":
    main()