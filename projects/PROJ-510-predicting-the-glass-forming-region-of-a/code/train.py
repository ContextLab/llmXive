"""
Train.py - Model Training and Cross-Validation Pipeline

This module handles:
1. Loading processed data
2. Train-test splitting
3. Random Forest model training with 5-fold Cross-Validation
4. Saving cross-validation metrics to JSON
5. Saving the trained model to disk
"""

import logging
import sys
import os
import json
import pickle
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/train.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_PATH = "data/processed/processed_alloys.csv"
MODEL_DIR = "data/models"
MODEL_PATH = os.path.join(MODEL_DIR, "random_forest_model.pkl")
CV_METRICS_PATH = os.path.join(MODEL_DIR, "cv_metrics.json")
RANDOM_STATE = 42
N_FOLDS = 5
TARGET_COLUMN = "critical_cooling_rate"


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Load processed data and perform train-test split.

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Processed data not found at {DATA_PATH}. "
            "Run ingestion.py and features.py first."
        )

    logger.info(f"Loading data from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    # Validate required columns
    required_cols = [TARGET_COLUMN]
    # Check for feature columns (assuming they are all numeric except target)
    feature_cols = [col for col in df.columns if col != TARGET_COLUMN]

    if not feature_cols:
        raise ValueError("No feature columns found in dataset.")

    logger.info(f"Dataset shape: {df.shape}")
    logger.info(f"Features: {feature_cols}")

    X = df[feature_cols]
    y = df[TARGET_COLUMN]

    # Check for zero variance in target (T017 requirement)
    if y.var() == 0:
        raise ValueError("Zero variance in critical_cooling_rate")

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    logger.info(f"Train set size: {len(X_train)}")
    logger.info(f"Test set size: {len(X_test)}")

    return X_train, X_test, y_train, y_test


def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestRegressor:
    """
    Train a Random Forest Regressor.

    Args:
        X_train: Training features
        y_train: Training targets

    Returns:
        Trained RandomForestRegressor model
    """
    logger.info("Initializing RandomForestRegressor")
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1
    )
    logger.info("Fitting model on training data")
    model.fit(X_train, y_train)
    logger.info("Model training complete")
    return model


def run_cross_validation(X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, Any]:
    """
    Perform 5-fold cross-validation and save metrics.

    Args:
        X_train: Training features
        y_train: Training targets

    Returns:
        Dictionary containing fold scores and mean RMSE
    """
    logger.info(f"Running {N_FOLDS}-fold cross-validation")

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    # cross_val_score returns scores (higher is better by default for r2, but we want negative MSE)
    # We use scoring='neg_root_mean_squared_error' to get RMSE directly (negative because sklearn convention)
    try:
        scores = cross_val_score(
            model, X_train, y_train,
            cv=N_FOLDS,
            scoring='neg_root_mean_squared_error',
            n_jobs=-1
        )
    except Exception as e:
        logger.error(f"Cross-validation failed: {e}")
        raise

    # Convert negative RMSE to positive RMSE
    rmse_scores = -scores

    fold_scores = rmse_scores.tolist()
    mean_rmse = float(np.mean(rmse_scores))

    metrics = {
        "fold_scores": fold_scores,
        "mean_rmse": mean_rmse
    }

    logger.info(f"CV Fold Scores: {fold_scores}")
    logger.info(f"Mean CV RMSE: {mean_rmse:.4f}")

    return metrics


def save_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save cross-validation metrics to JSON file.

    Args:
        metrics: Dictionary of metrics
        output_path: Path to save the JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved CV metrics to {output_path}")


def evaluate_on_test(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    """
    Evaluate model on held-out test set.

    Args:
        model: Trained model
        X_test: Test features
        y_test: Test targets

    Returns:
        RMSE on test set
    """
    logger.info("Evaluating model on test set")
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    logger.info(f"Test RMSE: {rmse:.4f}")
    return rmse


def save_model(model: RandomForestRegressor, output_path: str) -> None:
    """
    Save trained model to disk.

    Args:
        model: Trained model
        output_path: Path to save the pickle file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Saved model to {output_path}")


def run_training() -> None:
    """
    Main entry point for the training pipeline.
    """
    logger.info("Starting Training Pipeline")

    # Load data
    X_train, X_test, y_train, y_test = load_data()

    # Run Cross-Validation
    cv_metrics = run_cross_validation(X_train, y_train)
    save_metrics(cv_metrics, CV_METRICS_PATH)

    # Train final model on full training set
    final_model = train_model(X_train, y_train)

    # Evaluate on test set
    test_rmse = evaluate_on_test(final_model, X_test, y_test)

    # Save final model
    save_model(final_model, MODEL_PATH)

    logger.info("Training Pipeline Complete")
    logger.info(f"Final Test RMSE: {test_rmse:.4f}")


if __name__ == "__main__":
    run_training()
