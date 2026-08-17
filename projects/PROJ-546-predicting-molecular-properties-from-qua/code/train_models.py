"""
Train two Random Forest models (Semi-Empirical vs DFT) using locked split indices.

This module implements User Story 2 (US2) for comparative modeling. It trains
Random Forest regressors on semi-empirical (DFTB+) and high-level DFT (Psi4)
descriptors using the exact same k-fold splits to enable a paired t-test.

The split indices are locked via a fixed random_state and stratification strategy
defined in T020b (dft_calculator.py) to ensure the paired comparison is valid.
"""

import argparse
import csv
import json
import logging
import os
import sys
import pickle
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler
import joblib

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paths
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

DESCRIPTORS_SEMI_PATH = DATA_DIR / "descriptors_semi.csv"
DESCRIPTORS_DFT_PATH = DATA_DIR / "descriptors_dft.csv"
LOCKED_INDICES_PATH = DATA_DIR / "locked_splits.pkl"

OUTPUT_METRICS_PATH = REPORTS_DIR / "training_metrics.json"
OUTPUT_SEMI_MODEL_PATH = MODELS_DIR / "rf_semi.pkl"
OUTPUT_DFT_MODEL_PATH = MODELS_DIR / "rf_dft.pkl"

LOG_FILE = LOGS_DIR / "training.log"

# Configuration
RANDOM_STATE = 42  # Must match T020b
N_FOLDS = 5
N_ESTIMATORS = 100
TARGET_COLUMN = "experimental_barrier"


def setup_logger() -> logging.Logger:
    """Configure logging for the training pipeline."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("train_models")
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger


def load_data_semi() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load semi-empirical descriptors and target.

    Returns:
        X: Feature matrix (numpy array)
        y: Target vector (numpy array)
        feature_names: List of column names (excluding target)
    """
    if not DESCRIPTORS_SEMI_PATH.exists():
        raise FileNotFoundError(f"Semi-empirical descriptors not found at {DESCRIPTORS_SEMI_PATH}. "
                                "Run T013c4 (descriptor_pipeline) first.")

    features = []
    targets = []
    feature_names = []

    with open(DESCRIPTORS_SEMI_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("Empty CSV or missing headers in descriptors_semi.csv")

        # Assume all columns except target are features
        target_col = TARGET_COLUMN
        if target_col not in reader.fieldnames:
            raise ValueError(f"Target column '{target_col}' not found in {DESCRIPTORS_SEMI_PATH}")

        feature_names = [col for col in reader.fieldnames if col != target_col]

        for row in reader:
            features.append([float(row[col]) for col in feature_names])
            targets.append(float(row[target_col]))

    logger.info(f"Loaded {len(features)} samples with {len(feature_names)} features from semi-empirical data.")
    return np.array(features), np.array(targets), feature_names


def load_data_dft() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load DFT descriptors and target.

    Returns:
        X: Feature matrix (numpy array)
        y: Target vector (numpy array)
    """
    if not DESCRIPTORS_DFT_PATH.exists():
        raise FileNotFoundError(f"DFT descriptors not found at {DESCRIPTORS_DFT_PATH}. "
                                "Run T020b (dft_calculator) first.")

    features = []
    targets = []

    with open(DESCRIPTORS_DFT_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("Empty CSV or missing headers in descriptors_dft.csv")

        target_col = TARGET_COLUMN
        if target_col not in reader.fieldnames:
            raise ValueError(f"Target column '{target_col}' not found in {DESCRIPTORS_DFT_PATH}")

        # Ensure feature order matches semi-empirical (assuming same column order for now)
        # In a robust pipeline, we might align by name, but T020b ensures consistency.
        feature_names_dft = [col for col in reader.fieldnames if col != target_col]

        for row in reader:
            features.append([float(row[col]) for col in feature_names_dft])
            targets.append(float(row[target_col]))

    logger.info(f"Loaded {len(features)} samples with {len(feature_names_dft)} features from DFT data.")
    return np.array(features), np.array(targets)


def load_locked_splits() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load the locked split indices generated by T020b.

    Returns:
        train_indices: Array of training indices
        test_indices: Array of test indices
        stratify_labels: Array of stratification labels (binned target)
    """
    if not LOCKED_INDICES_PATH.exists():
        raise FileNotFoundError(f"Locked splits not found at {LOCKED_INDICES_PATH}. "
                                "Run T020b (dft_calculator) to generate splits first.")

    with open(LOCKED_INDICES_PATH, 'rb') as f:
        data = pickle.load(f)

    train_indices = data['train_indices']
    test_indices = data['test_indices']
    stratify_labels = data['stratify_labels']

    logger.info(f"Loaded locked splits: {len(train_indices)} train, {len(test_indices)} test.")
    return train_indices, test_indices, stratify_labels


def train_and_evaluate_fold(
    X_semi: np.ndarray,
    y_semi: np.ndarray,
    X_dft: np.ndarray,
    y_dft: np.ndarray,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    n_estimators: int = N_ESTIMATORS
) -> Dict[str, float]:
    """
    Train a single fold for both models and return MAE.

    Args:
        X_semi, y_semi: Semi-empirical data
        X_dft, y_dft: DFT data
        train_idx, test_idx: Indices for this fold
        n_estimators: Number of trees

    Returns:
        Dictionary with 'mae_semi' and 'mae_dft'
    """
    # Split data
    X_semi_train, X_semi_test = X_semi[train_idx], X_semi[test_idx]
    y_semi_train, y_semi_test = y_semi[train_idx], y_semi[test_idx]

    X_dft_train, X_dft_test = X_dft[train_idx], X_dft[test_idx]
    y_dft_train, y_dft_test = y_dft[train_idx], y_dft[test_idx]

    # Scale features
    scaler_semi = StandardScaler()
    X_semi_train_scaled = scaler_semi.fit_transform(X_semi_train)
    X_semi_test_scaled = scaler_semi.transform(X_semi_test)

    scaler_dft = StandardScaler()
    X_dft_train_scaled = scaler_dft.fit_transform(X_dft_train)
    X_dft_test_scaled = scaler_dft.transform(X_dft_test)

    # Train Semi-Empirical RF
    rf_semi = RandomForestRegressor(n_estimators=n_estimators, random_state=RANDOM_STATE, n_jobs=-1)
    rf_semi.fit(X_semi_train_scaled, y_semi_train)
    y_semi_pred = rf_semi.predict(X_semi_test_scaled)
    mae_semi = mean_absolute_error(y_semi_test, y_semi_pred)

    # Train DFT RF
    rf_dft = RandomForestRegressor(n_estimators=n_estimators, random_state=RANDOM_STATE, n_jobs=-1)
    rf_dft.fit(X_dft_train_scaled, y_dft_train)
    y_dft_pred = rf_dft.predict(X_dft_test_scaled)
    mae_dft = mean_absolute_error(y_dft_test, y_dft_pred)

    logger.info(f"Fold MAE - Semi: {mae_semi:.4f}, DFT: {mae_dft:.4f}")

    return {
        "mae_semi": mae_semi,
        "mae_dft": mae_dft
    }


def train_models() -> Dict[str, Any]:
    """
    Main training loop: runs k-fold cross-validation with locked splits.

    Returns:
        Dictionary containing fold results and final aggregated metrics.
    """
    # Load data
    logger.info("Loading semi-empirical descriptors...")
    X_semi, y_semi, feature_names = load_data_semi()

    logger.info("Loading DFT descriptors...")
    X_dft, y_dft = load_data_dft()

    # Ensure data alignment
    if len(X_semi) != len(X_dft):
        raise ValueError(f"Data mismatch: Semi has {len(X_semi)} samples, DFT has {len(X_dft)}. "
                         "Ensure T020b and T013c4 processed the same subset.")

    logger.info("Loading locked split indices...")
    train_indices, test_indices, stratify_labels = load_locked_splits()

    # Prepare for cross-validation using the locked single split structure
    # Note: T020b generates a single train/test split for the subset selection.
    # However, US2 requires k-fold CV. We must re-generate folds based on the
    # locked subset indices to ensure the *same* molecules are used in both models.
    # The "locked split" in T020b usually refers to the subset selection.
    # For the CV itself, we use StratifiedKFold with the SAME random_state on the
    # subset data to ensure alignment between Semi and DFT folds.

    n_samples = len(y_semi)
    # Create a fixed array of indices for the subset
    subset_indices = np.arange(n_samples)

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    fold_results = []

    logger.info(f"Starting {N_FOLDS}-fold cross-validation with random_state={RANDOM_STATE}...")

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(subset_indices, stratify_labels)):
        logger.info(f"Processing fold {fold_idx + 1}/{N_FOLDS}...")

        # Map subset indices back to the original arrays (which are already the subset)
        # Since X_semi and X_dft are already the subset from T020b/T013c4,
        # train_idx and test_idx from skf directly index into X_semi/X_dft.
        fold_metrics = train_and_evaluate_fold(
            X_semi, y_semi,
            X_dft, y_dft,
            train_idx, test_idx,
            n_estimators=N_ESTIMATORS
        )
        fold_results.append(fold_metrics)

    # Aggregate results
    mae_semi_list = [r["mae_semi"] for r in fold_results]
    mae_dft_list = [r["mae_dft"] for r in fold_results]

    mean_mae_semi = np.mean(mae_semi_list)
    std_mae_semi = np.std(mae_semi_list)
    mean_mae_dft = np.mean(mae_dft_list)
    std_mae_dft = np.std(mae_dft_list)

    logger.info(f"Final Mean MAE (Semi): {mean_mae_semi:.4f} (+/- {std_mae_semi:.4f})")
    logger.info(f"Final Mean MAE (DFT): {mean_mae_dft:.4f} (+/- {std_mae_dft:.4f})")

    # Train final models on full subset for saving
    logger.info("Training final models on full subset...")
    scaler_semi_final = StandardScaler()
    X_semi_scaled_final = scaler_semi_final.fit_transform(X_semi)
    rf_semi_final = RandomForestRegressor(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1)
    rf_semi_final.fit(X_semi_scaled_final, y_semi)

    scaler_dft_final = StandardScaler()
    X_dft_scaled_final = scaler_dft_final.fit_transform(X_dft)
    rf_dft_final = RandomForestRegressor(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1)
    rf_dft_final.fit(X_dft_scaled_final, y_dft)

    # Save models and scalers
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump({
        "model": rf_semi_final,
        "scaler": scaler_semi_final,
        "feature_names": feature_names
    }, OUTPUT_SEMI_MODEL_PATH)
    logger.info(f"Saved Semi-Empirical model to {OUTPUT_SEMI_MODEL_PATH}")

    joblib.dump({
        "model": rf_dft_final,
        "scaler": scaler_dft_final,
        "feature_names": feature_names # Assuming same feature order
    }, OUTPUT_DFT_MODEL_PATH)
    logger.info(f"Saved DFT model to {OUTPUT_DFT_MODEL_PATH}")

    return {
        "fold_results": fold_results,
        "mean_mae_semi": float(mean_mae_semi),
        "std_mae_semi": float(std_mae_semi),
        "mean_mae_dft": float(mean_mae_dft),
        "std_mae_dft": float(std_mae_dft),
        "n_folds": N_FOLDS,
        "random_state": RANDOM_STATE
    }


def main():
    """Entry point for the training script."""
    global logger
    logger = setup_logger()

    try:
        results = train_models()

        # Save results to JSON
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_METRICS_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Training metrics saved to {OUTPUT_METRICS_PATH}")

        print(f"Training complete. Mean MAE Semi: {results['mean_mae_semi']:.4f}, DFT: {results['mean_mae_dft']:.4f}")

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()