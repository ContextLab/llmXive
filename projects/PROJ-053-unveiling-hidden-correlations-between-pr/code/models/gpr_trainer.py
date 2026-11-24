import os
import json
import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.model_selection import KFold

from config import (
    get_processed_data_dir,
    get_results_dir,
    ensure_directories,
    get_logger,
)

logger = get_logger(__name__)

def optimize_hyperparameters(
    X: np.ndarray, y: np.ndarray, n_splits: int = 5
) -> Tuple[Any, float]:
    """
    Optimize GPR hyperparameters using K-Fold cross‑validation.

    Args:
        X: Training features.
        y: Training targets.
        n_splits: Number of CV splits.

    Returns:
        Best kernel configuration and best log marginal likelihood.
    """
    length_scales = [0.1, 0.5, 1.0, 2.0, 5.0]
    best_kernel = None
    best_score = -np.inf

    for ls in length_scales:
        kernel = C(1.0) * RBF(length_scale=ls)
        gpr = GaussianProcessRegressor(kernel=kernel, alpha=1e-10, normalize_y=True)

        kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        scores = []

        for train_idx, val_idx in kfold.split(X):
            X_tr, X_val = X[train_idx], X[val_idx]
            y_tr, y_val = y[train_idx], y[val_idx]

            gpr.fit(X_tr, y_tr)
            score = gpr.score(X_val, y_val)
            scores.append(score)

        mean_score = np.mean(scores)
        if mean_score > best_score:
            best_score = mean_score
            best_kernel = kernel
            logger.info(
                f"New best kernel (length_scale={ls}): CV R² = {mean_score:.4f}"
            )

    return best_kernel, best_score

def train_gpr_model(X_train: np.ndarray, y_train: np.ndarray) -> GaussianProcessRegressor:
    """
    Train a GPR model with optimized hyperparameters.

    Args:
        X_train: Scaled training features.
        y_train: Training targets.

    Returns:
        Trained GaussianProcessRegressor.
    """
    logger.info("Optimizing GPR hyperparameters...")
    kernel, score = optimize_hyperparameters(X_train, y_train)

    logger.info(f"Best kernel found with CV R²: {score:.4f}")
    logger.info("Training final GPR model...")

    gpr = GaussianProcessRegressor(kernel=kernel, alpha=1e-10, normalize_y=True)
    gpr.fit(X_train, y_train)

    logger.info("GPR model training complete.")
    return gpr

def run_stratified_analysis(df: pd.DataFrame, feature_cols: List[str], target_cols: List[str]) -> Dict[str, Any]:
    """
    Perform stratified analysis by alloy_type (if present).
    """
    # Placeholder for future implementation
    return {}

def main():
    """
    Entry point for the GPR training step.
    Loads the processed train/test CSVs, trains a Gaussian Process model on
    the first target column, and saves the model artifact to
    <project>/results/model/gpr_model.joblib.
    """
    logger.info("Starting GPR training step...")
    processed_dir = Path(get_processed_data_dir())
    train_path = processed_dir / "train.csv"
    test_path = processed_dir / "test.csv"

    if not train_path.exists() or not test_path.exists():
        logger.error("Processed train or test CSV not found.")
        raise FileNotFoundError("Processed data files missing.")

    # Load data
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    # Determine target columns (use the first available)
    target_cols = [c for c in ["yield_strength", "ductility"] if c in train_df.columns]
    if not target_cols:
        raise ValueError("No target columns found in training data.")
    target = target_cols[0]

    feature_cols = [c for c in train_df.columns if c not in target_cols]

    X_train = train_df[feature_cols].values
    y_train = train_df[target].values

    # Train GPR
    gpr_model = train_gpr_model(X_train, y_train)

    # Save model
    model_dir = Path(get_results_dir()) / "model"
    ensure_directories([model_dir])
    model_path = model_dir / "gpr_model.joblib"
    joblib.dump(gpr_model, model_path)
    logger.info(f"GPR model saved to {model_path}")

if __name__ == "__main__":
    main()
