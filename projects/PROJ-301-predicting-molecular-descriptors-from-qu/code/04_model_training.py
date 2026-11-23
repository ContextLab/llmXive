"""
Model Training and Cross-Validation for Molecular Descriptors (User Story 2).

This script trains Random Forest Regressors on 2D and 3D features using 5-fold CV.
It handles both training modes and saves models and metrics to artifacts/.

Execution: python code/04_model_training.py --mode 2d
           python code/04_model_training.py --mode 3d
"""
import argparse
import json
import logging
import os
import pickle
import time
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.stats import zscore
from sklearn.preprocessing import StandardScaler

# Project imports
from config import set_seeds
from utils.logger import configure_logging_for_pipeline, get_logger
from utils.memory_monitor import get_memory_usage_gb, check_memory_limit

# Set up logging
configure_logging_for_pipeline("model_training")
logger = get_logger("model_training")

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_MODELS = PROJECT_ROOT / "artifacts" / "models"
ARTIFACTS_METRICS = PROJECT_ROOT / "artifacts" / "metrics"
MAX_RUNTIME_HOURS = 6
MEMORY_LIMIT_GB = 6.5

# Hyperparameters (concretizing FR-003)
RF_PARAMS = {
    "n_estimators": 500,
    "max_depth": 20,
    "min_samples_split": 2,
    "min_samples_leaf": 1,
    "n_jobs": -1,
    "random_state": 42
}

def load_features_and_labels(mode: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load features and labels for the specified mode (2d or 3d).

    Returns:
        X: Feature matrix (2D or 3D)
        y: Labels (dipole, HOMO, LUMO)
        indices: Original indices from the split
    """
    logger.info(f"Loading data for mode: {mode}")

    # Load indices
    with open(DATA_PROCESSED / "split_indices_train.json", "r") as f:
        train_indices = json.load(f)
    with open(DATA_PROCESSED / "split_indices_test.json", "r") as f:
        test_indices = json.load(f)

    # Load labels
    import pandas as pd
    labels_df = pd.read_parquet(DATA_PROCESSED / "molecules_cleaned.parquet")
    # Filter to train set
    train_labels_df = labels_df.iloc[train_indices]

    # Extract target columns
    # Assuming the cleaned parquet has columns: 'dipole', 'homo', 'lumo'
    target_cols = ['dipole', 'homo', 'lumo']
    y = train_labels_df[target_cols].values
    indices = train_indices

    # Load features
    if mode == "2d":
        X = np.load(DATA_PROCESSED / "features_2d.npy")
        # Ensure X is indexed by train_indices if it's the full set
        # Based on T011, features_2d.npy is saved for the sampled subset
        # If the subset IS the train set, we use it directly.
        # If features are full population, we index: X = X[train_indices]
        # T011 says: "Generate 2D Morgan fingerprints... Save 2D features to data/processed/features_2d.npy"
        # and "Split Construction... Save train indices".
        # Assumption: The features file corresponds to the full cleaned dataset, and we index.
        # However, T011 also says "Memory-Aware Sampling... to ensure the dataset fits within memory".
        # If sampling happened BEFORE feature generation, features_2d.npy might already be the sample.
        # Let's assume the safe path: The features file corresponds to the rows in molecules_cleaned.parquet.
        # If the sampling step in T011 created a subset, the indices should align.
        # To be safe, we assume features_2d.npy has shape (N_samples, n_features) where N_samples matches the rows used for labels.
        # If T011 generated features ONLY for the sample, then X is already the train set (or the subset).
        # Let's check shape alignment.
        if X.shape[0] != len(indices):
            # If mismatch, assume X is full population and we need to index
            if X.shape[0] == len(labels_df):
                X = X[indices]
            else:
                raise ValueError(f"Feature shape {X.shape[0]} does not match indices count {len(indices)} or full dataset.")
    else:
        # Load 3D features (pickle)
        with open(DATA_PROCESSED / "features_3d.pkl", "rb") as f:
            features_3d = pickle.load(f)
        # Convert to numpy array if it's a list of arrays or similar
        if isinstance(features_3d, list):
            X = np.array(features_3d)
        else:
            X = features_3d

        if X.shape[0] != len(indices):
            if X.shape[0] == len(labels_df):
                X = X[indices]
            else:
                raise ValueError(f"Feature shape {X.shape[0]} does not match indices count {len(indices)}.")

    logger.info(f"Loaded {mode} features: {X.shape}, Labels: {y.shape}")
    return X, y, indices

def train_model(X: np.ndarray, y: np.ndarray, n_folds: int = 5) -> Tuple[Dict[str, Any], np.ndarray, np.ndarray]:
    """
    Train a Random Forest model using K-Fold Cross Validation.

    Returns:
        metrics: Dictionary of per-fold metrics
        y_pred: Predictions for all samples (concatenated from folds)
        y_true: True labels
    """
    logger.info(f"Starting {n_folds}-fold CV training...")
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)

    fold_maes = []
    fold_rmses = []
    fold_r2s = []
    y_pred_all = np.zeros_like(y)
    y_true_all = y.copy()

    start_time = time.time()

    for fold_idx, (train_idx, val_idx) in enumerate(kf.split(X)):
        logger.info(f"Processing fold {fold_idx + 1}/{n_folds}")

        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # Optional: Scaling if needed (RF usually doesn't need it, but good for 3D graph features if normalized)
        # scaler = StandardScaler()
        # X_train = scaler.fit_transform(X_train)
        # X_val = scaler.transform(X_val)

        model = RandomForestRegressor(**RF_PARAMS)
        model.fit(X_train, y_train)

        y_pred_val = model.predict(X_val)
        y_pred_all[val_idx] = y_pred_val

        mae = mean_absolute_error(y_val, y_pred_val)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))
        r2 = model.score(X_val, y_val)

        fold_maes.append(mae)
        fold_rmses.append(rmse)
        fold_r2s.append(r2)

        # Memory check
        mem_gb = get_memory_usage_gb()
        if mem_gb > MEMORY_LIMIT_GB:
            logger.warning(f"Memory usage {mem_gb:.2f}GB exceeds limit. Consider downsampling.")

        # Runtime check
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_HOURS * 3600:
            logger.error("Runtime exceeded 6 hours. Stopping.")
            break

    # Aggregate metrics
    metrics = {
        "mean_mae": float(np.mean(fold_maes)),
        "std_mae": float(np.std(fold_maes)),
        "mean_rmse": float(np.mean(fold_rmses)),
        "std_rmse": float(np.std(fold_rmses)),
        "mean_r2": float(np.mean(fold_r2s)),
        "fold_maes": [float(m) for m in fold_maes],
        "fold_rmses": [float(r) for r in fold_rmses],
        "fold_r2s": [float(r) for r in fold_r2s],
        "runtime_hours": float((time.time() - start_time) / 3600)
    }

    logger.info(f"CV completed. Mean MAE: {metrics['mean_mae']:.4f}")
    return metrics, y_pred_all, y_true_all

def train_model_2d(X: np.ndarray, y: np.ndarray) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """Train 2D model and save artifacts."""
    metrics, y_pred, y_true = train_model(X, y)

    # Train final model on full training set (for saving)
    model = RandomForestRegressor(**RF_PARAMS)
    model.fit(X, y)

    # Save model
    os.makedirs(ARTIFACTS_MODELS, exist_ok=True)
    with open(ARTIFACTS_MODELS / "model_2d.pkl", "wb") as f:
        pickle.dump(model, f)

    # Save metrics
    os.makedirs(ARTIFACTS_METRICS, exist_ok=True)
    with open(ARTIFACTS_METRICS / "cv_2d_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return model, metrics

def train_model_3d(X: np.ndarray, y: np.ndarray) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """Train 3D model and save artifacts."""
    metrics, y_pred, y_true = train_model(X, y)

    # Train final model on full training set
    model = RandomForestRegressor(**RF_PARAMS)
    model.fit(X, y)

    # Save model
    with open(ARTIFACTS_MODELS / "model_3d.pkl", "wb") as f:
        pickle.dump(model, f)

    # Save metrics
    with open(ARTIFACTS_METRICS / "cv_3d_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return model, metrics

def aggregate_cv_metrics():
    """
    Aggregate CV metrics from both models into a single report.
    Implements T017.
    """
    logger.info("Aggregating CV metrics...")

    cv_2d = {}
    cv_3d = {}

    try:
        with open(ARTIFACTS_METRICS / "cv_2d_metrics.json", "r") as f:
            cv_2d = json.load(f)
    except FileNotFoundError:
        logger.warning("cv_2d_metrics.json not found. Skipping aggregation for 2D.")

    try:
        with open(ARTIFACTS_METRICS / "cv_3d_metrics.json", "r") as f:
            cv_3d = json.load(f)
    except FileNotFoundError:
        logger.warning("cv_3d_metrics.json not found. Skipping aggregation for 3D.")

    combined = {
        "model_2d": cv_2d,
        "model_3d": cv_3d,
        "aggregated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(ARTIFACTS_METRICS / "cv_metrics.json", "w") as f:
        json.dump(combined, f, indent=2)

    # Stability verification (T017)
    stability_report = {}
    for model_name, data in [("model_2d", cv_2d), ("model_3d", cv_3d)]:
        if not data or "fold_maes" not in data:
            continue
        fold_maes = data["fold_maes"]
        mean_mae = np.mean(fold_maes)
        std_mae = np.std(fold_maes)
        ratio = std_mae / mean_mae if mean_mae > 0 else 0
        passed = ratio <= 0.05
        stability_report[model_name] = {
            "fold_maes": fold_maes,
            "stability_ratio": float(ratio),
            "passed": passed
        }
        if not passed:
            logger.warning(f"{model_name} stability ratio {ratio:.4f} > 5%. Stability check failed.")

    with open(ARTIFACTS_METRICS / "stability_report.json", "w") as f:
        json.dump(stability_report, f, indent=2)

    logger.info("Aggregation and stability check complete.")

def monitor_runtime_and_train(mode: str):
    """Wrapper to monitor runtime and train the specified model."""
    start_time = time.time()
    X, y, _ = load_features_and_labels(mode)

    if mode == "2d":
        train_model_2d(X, y)
    elif mode == "3d":
        train_model_3d(X, y)

    elapsed = time.time() - start_time
    if elapsed > MAX_RUNTIME_HOURS * 3600:
        logger.error("Training exceeded 6 hours.")
        with open(ARTIFACTS_METRICS / "runtime_failure.json", "w") as f:
            json.dump({
                "status": "failed",
                "reason": "runtime_exceeded",
                "duration_hours": elapsed / 3600
            }, f)
    else:
        logger.info(f"Training completed in {elapsed/3600:.2f} hours.")

def main():
    """Entry point for the training pipeline."""
    parser = argparse.ArgumentParser(description="Train molecular descriptor models.")
    parser.add_argument("--mode", type=str, choices=["2d", "3d", "all"], default="all",
                        help="Which model to train: 2d, 3d, or both (all)")
    parser.add_argument("--aggregate", action="store_true", default=False,
                        help="Run aggregation step (T017)")
    args = parser.parse_args()

    set_seeds(42)

    if args.mode in ["2d", "all"]:
        monitor_runtime_and_train("2d")
    if args.mode in ["3d", "all"]:
        monitor_runtime_and_train("3d")

    if args.aggregate or args.mode == "all":
        aggregate_cv_metrics()

    logger.info("Training pipeline finished.")

if __name__ == "__main__":
    main()
