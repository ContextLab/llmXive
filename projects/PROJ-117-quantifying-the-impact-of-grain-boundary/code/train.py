import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
from xgboost import XGBRegressor
import joblib

# Project imports
from utils import setup_logging, set_random_seed, raise_data_insufficiency
from preprocess import load_parsed_data

# Configure logging
logger = setup_logging("train")

# Constants
DATA_PATH = Path("data/processed/cleaned_dataset.parquet")
MODEL_DIR = Path("models")
ARTIFACTS_DIR = Path("artifacts/reports")
MIN_RECORDS = 500
RANDOM_SEED = 42

def load_data() -> pd.DataFrame:
    """Load the preprocessed dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {DATA_PATH}. Run T011 first.")
    logger.info(f"Loading data from {DATA_PATH}")
    df = pd.read_parquet(DATA_PATH)
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separate features and target.
    Target is 'diffusivity'. Features are all numeric columns except target.
    """
    target_col = 'diffusivity'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")

    # Select numeric columns excluding target
    feature_cols = df.select_dtypes(include=[np.number]).columns.drop(target_col)
    
    X = df[feature_cols]
    y = df[target_col]

    logger.info(f"Features: {list(feature_cols)}")
    logger.info(f"Target: {target_col}")
    return X, y

def split_data(X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Perform 70/15/15 split.
    Train: 70%, Val: 15%, Test: 15%
    """
    # First split: 70% train, 30% temp (val + test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=RANDOM_SEED
    )
    
    # Second split: 50% of temp -> 15% val, 15% test (relative to original)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=RANDOM_SEED
    )

    logger.info(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")
    return X_train, X_test, y_train, y_test

def tune_and_train(X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[XGBRegressor, Dict[str, Any]]:
    """
    Perform RandomizedSearchCV for XGBoost hyperparameter tuning.
    Search space: max_depth [3, 10], learning_rate [0.01, 0.3], n_estimators [50, 300]
    """
    param_dist = {
        'max_depth': [3, 4, 5, 6, 7, 8, 9, 10],
        'learning_rate': [0.01, 0.05, 0.1, 0.2, 0.3],
        'n_estimators': [50, 100, 150, 200, 250, 300],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }

    base_model = XGBRegressor(
        objective='reg:squarederror',
        random_state=RANDOM_SEED,
        n_jobs=2  # CPU constraint
    )

    logger.info("Starting RandomizedSearchCV (k=5)...")
    search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_dist,
        n_iter=20,  # Reasonable number for CPU constraint
        scoring='r2',
        cv=5,
        random_state=RANDOM_SEED,
        n_jobs=2,
        verbose=1
    )

    search.fit(X_train, y_train)

    best_model = search.best_estimator_
    best_params = search.best_params_

    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best CV R2 score: {search.best_score_:.4f}")

    return best_model, best_params

def evaluate_model(model: XGBRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluate model on test set and return metrics."""
    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mape = mean_absolute_percentage_error(y_test, y_pred)

    metrics = {
        'r2': float(r2),
        'rmse': float(rmse),
        'mape': float(mape),
        'test_size': int(len(y_test))
    }

    logger.info(f"Test R2: {r2:.4f}")
    logger.info(f"Test RMSE: {rmse:.4f}")
    logger.info(f"Test MAPE: {mape:.4f}")

    return metrics

def save_artifacts(model: XGBRegressor, metrics: Dict[str, float], best_params: Dict[str, Any]):
    """Save model and metrics to disk."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    model_path = MODEL_DIR / "best_model.json"
    metrics_path = ARTIFACTS_DIR / "training_metrics.json"

    # Save model as JSON (XGBoost native format)
    model.save_model(str(model_path))
    logger.info(f"Model saved to {model_path}")

    # Save metrics
    report = {
        'best_params': best_params,
        'metrics': metrics,
        'model_path': str(model_path),
        'random_seed': RANDOM_SEED
    }

    with open(metrics_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

def main():
    logger.info("Starting Training Pipeline (T012)")
    set_random_seed(RANDOM_SEED)

    try:
        # Load data
        df = load_data()
        
        # Validate record count
        if len(df) < MIN_RECORDS:
            raise_data_insufficiency(len(df), MIN_RECORDS, "Valid records after preprocessing")

        # Prepare features
        X, y = prepare_features(df)
        
        if len(X) < MIN_RECORDS:
            raise_data_insufficiency(len(X), MIN_RECORDS, "Feature matrix rows")

        # Split data
        X_train, X_test, y_train, y_test = split_data(X, y)

        # Tune and train
        model, best_params = tune_and_train(X_train, y_train)

        # Evaluate
        metrics = evaluate_model(model, X_test, y_test)

        # Save artifacts
        save_artifacts(model, metrics, best_params)

        logger.info("Training pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise

if __name__ == "__main__":
    sys.exit(main())