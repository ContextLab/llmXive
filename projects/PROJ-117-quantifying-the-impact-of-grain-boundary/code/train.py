"""
Train a gradient-boosted tree model (XGBoost) to predict atomic diffusivity
based on grain boundary descriptors.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import uniform, randint

# Project imports
from utils import setup_logging, set_random_seed
from error_handling import exit_on_insufficiency
from preprocess import load_parsed_data

# Configure logging
logger = setup_logging()

# Constants
DATA_PATH = Path("data/processed/cleaned_dataset.parquet")
MODEL_PATH = Path("models/best_model.json")
METRICS_PATH = Path("artifacts/reports/training_metrics.json")
RANDOM_STATE = 42
MIN_RECORDS = 500

# Feature columns (derived from T010/T011)
# Assuming these are present in cleaned_dataset.parquet based on T010/T011 specs
FEATURE_COLS = [
    "misorientation_angle",
    "sigma_value",
    "boundary_plane_normal_h",
    "boundary_plane_normal_k",
    "boundary_plane_normal_l",
    "boundary_width",
    "excess_volume",
    "temperature",
    "simulation_method_dft",
    "simulation_method_md",
    "simulation_method_kmc",
    "potential_id_encoded"
]
TARGET_COL = "diffusivity"

def load_and_prepare_data() -> Tuple[pd.DataFrame, pd.Series]:
    """Load cleaned data and prepare features/target."""
    logger.info(f"Loading data from {DATA_PATH}")
    
    if not DATA_PATH.exists():
        logger.error(f"Data file not found: {DATA_PATH}. Run preprocessing first.")
        sys.exit(1)
    
    df = pd.read_parquet(DATA_PATH)
    
    # Validate data sufficiency
    if len(df) < MIN_RECORDS:
        logger.error(f"Data Insufficiency: Retrieved {len(df)} < {MIN_RECORDS}")
        exit_on_insufficiency(len(df), MIN_RECORDS)
    
    # Ensure required columns exist
    missing_cols = set(FEATURE_COLS + [TARGET_COL]) - set(df.columns)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)
    
    X = df[FEATURE_COLS].fillna(0)  # Handle any remaining NaNs
    y = df[TARGET_COL].fillna(0)
    
    return X, y

def split_data(X: pd.DataFrame, y: pd.Series) -> Tuple:
    """Perform 70/15/15 train/validation/test split."""
    set_random_seed(RANDOM_STATE)
    
    # First split: 70% train, 30% temp
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=RANDOM_STATE
    )
    
    # Second split: 50% of temp for validation, 50% for test (15% each of total)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=RANDOM_STATE
    )
    
    logger.info(f"Data split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    return X_train, X_val, X_test, y_train, y_val, y_test

def tune_hyperparameters(X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series) -> xgb.XGBRegressor:
    """Perform RandomizedSearchCV for hyperparameter tuning."""
    logger.info("Starting hyperparameter tuning...")
    
    # Define search space
    param_dist = {
        "max_depth": randint(3, 10),
        "learning_rate": uniform(0.01, 0.29),  # [0.01, 0.3)
        "n_estimators": randint(50, 250),      # [50, 300) -> adjusted for speed
        "subsample": uniform(0.6, 0.4),
        "colsample_bytree": uniform(0.6, 0.4)
    }
    
    # Base XGBoost model
    base_model = xgb.XGBRegressor(
        objective="reg:squarederror",
        random_state=RANDOM_STATE,
        n_jobs=2,  # CPU constraint
        verbosity=1
    )
    
    # RandomizedSearchCV
    search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_dist,
        n_iter=10,  # Reduced for CPU constraints
        scoring="r2",
        cv=3,       # Reduced CV for speed
        verbose=1,
        random_state=RANDOM_STATE,
        n_jobs=2
    )
    
    search.fit(X_train, y_train)
    
    logger.info(f"Best params: {search.best_params_}")
    logger.info(f"Best CV R2 score: {search.best_score_:.4f}")
    
    return search.best_estimator_

def evaluate_model(model: xgb.XGBRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluate model on test set and return metrics."""
    logger.info("Evaluating model on test set...")
    
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # MAPE calculation (handle zero values)
    mask = y_test != 0
    if mask.sum() > 0:
        mape = np.mean(np.abs((y_test[mask] - y_pred[mask]) / y_test[mask])) * 100
    else:
        mape = 0.0
    
    metrics = {
        "r2": float(r2),
        "rmse": float(rmse),
        "mape": float(mape)
    }
    
    logger.info(f"Test Metrics -> R2: {r2:.4f}, RMSE: {rmse:.4f}, MAPE: {mape:.2f}%")
    return metrics

def save_model_and_metrics(model: xgb.XGBRegressor, metrics: Dict[str, float]) -> None:
    """Save model and metrics to disk."""
    # Ensure directories exist
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model.save_model(str(MODEL_PATH))
    logger.info(f"Model saved to {MODEL_PATH}")
    
    # Save metrics
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {METRICS_PATH}")

def main():
    """Main training pipeline."""
    logger.info("Starting training pipeline (T012)...")
    
    # 1. Load data
    X, y = load_and_prepare_data()
    
    # 2. Split data
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
    
    # 3. Tune hyperparameters
    best_model = tune_hyperparameters(X_train, y_train, X_val, y_val)
    
    # 4. Evaluate on test set
    metrics = evaluate_model(best_model, X_test, y_test)
    
    # 5. Save artifacts
    save_model_and_metrics(best_model, metrics)
    
    logger.info("Training pipeline completed successfully.")

if __name__ == "__main__":
    main()
