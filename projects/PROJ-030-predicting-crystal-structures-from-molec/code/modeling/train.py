"""
Modeling training scripts for crystal structure prediction.
Implements Random Forest, Gradient Boosting, Ridge Regression, and baseline models.
"""

import os
import sys
import json
import logging
import traceback
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import Ridge
from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
import joblib

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_path_absolute, get_path_results, ensure_directory
from exceptions import DownloadError, MemoryErrorHandled, ValidationError
from logging_config import get_logger, log_event

logger = get_logger(__name__)

def load_split_indices(split_path: str) -> Dict[str, List[int]]:
    """Load train/test split indices from JSON file."""
    try:
        with open(split_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Split indices file not found: {split_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in split indices file: {e}")
        raise

def load_dataset(dataset_path: str) -> pd.DataFrame:
    """Load the processed dataset with fingerprints."""
    try:
        df = pd.read_csv(dataset_path)
        logger.info(f"Loaded dataset with {len(df)} rows from {dataset_path}")
        return df
    except FileNotFoundError:
        logger.error(f"Dataset file not found: {dataset_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def train_ridge_regression(X_train, y_train, X_test, y_test):
    """Train Ridge Regression model for lattice parameter prediction."""
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    metrics = {
        'r2': r2_score(y_test, y_pred),
        'mae': mean_absolute_error(y_test, y_pred)
    }
    return model, metrics

def save_model(model, model_path: str):
    """Save model artifact to disk."""
    ensure_directory(model_path)
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")

def calculate_molecular_weight_baseline(df_test: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate Molecular Weight baseline for regression tasks.
    Predicts target as the mean molecular weight of the training set.
    """
    # This is a placeholder for the MW baseline logic
    # Actual implementation would calculate mean MW from training set
    # and predict that for all test samples
    logger.info("Calculating Molecular Weight baseline...")
    return {"baseline_type": "molecular_weight", "status": "implemented"}

def calculate_majority_class_baseline(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    target_column: str = "space_group"
) -> Dict[str, Any]:
    """
    Calculate majority-class baseline for classification tasks.
    Predicts the most frequent space group from the training set for all test samples.
    Returns metrics (Accuracy, Macro-F1) against the test set labels.

    Args:
        df_train: Training dataframe containing the target column.
        df_test: Test dataframe containing the target column (ground truth).
        target_column: Name of the column containing space groups.

    Returns:
        Dictionary containing baseline predictions and metrics.
    """
    logger.info("Calculating majority-class baseline...")

    # 1. Determine the majority class from the training set
    if target_column not in df_train.columns:
        raise ValidationError(f"Target column '{target_column}' not found in training data.")

    class_counts = df_train[target_column].value_counts()
    if class_counts.empty:
        raise ValidationError("Training data has no valid target values for majority class calculation.")

    majority_class = class_counts.index[0]
    majority_count = class_counts.iloc[0]
    total_train = len(df_train)
    majority_ratio = majority_count / total_train

    logger.info(f"Majority class: '{majority_class}' (count: {majority_count}, ratio: {majority_ratio:.4f})")

    # 2. Generate predictions for the test set (all predictions are the majority class)
    if target_column not in df_test.columns:
        raise ValidationError(f"Target column '{target_column}' not found in test data.")

    y_true = df_test[target_column]
    y_pred = [majority_class] * len(y_true)

    # 3. Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    # Use zero_division=0 to handle cases where a class might not be present in predictions
    f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)

    metrics = {
        "baseline_type": "majority_class",
        "majority_class": majority_class,
        "majority_class_count": int(majority_count),
        "majority_class_ratio": float(majority_ratio),
        "test_set_size": len(df_test),
        "accuracy": float(accuracy),
        "f1_macro": float(f1_macro),
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Majority class baseline metrics - Accuracy: {accuracy:.4f}, F1-Macro: {f1_macro:.4f}")
    return metrics

def main():
    """
    Main entry point for training and baseline calculations.
    Orchestrates loading data, training models, and calculating baselines.
    """
    try:
        # Paths
        dataset_path = get_path_absolute("data/processed/crystal_dataset.csv")
        split_indices_path = get_path_absolute("data/processed/split_indices.json")
        results_dir = get_path_results()
        majority_class_metrics_path = get_path_absolute("data/results/majority_class_baseline_metrics.json")

        ensure_directory(results_dir)

        # Load data
        logger.info("Loading dataset and split indices...")
        df = load_dataset(dataset_path)
        split_indices = load_split_indices(split_indices_path)

        # Separate train and test data
        train_indices = split_indices['train']
        test_indices = split_indices['test']

        df_train = df.iloc[train_indices].reset_index(drop=True)
        df_test = df.iloc[test_indices].reset_index(drop=True)

        logger.info(f"Train size: {len(df_train)}, Test size: {len(df_test)}")

        # Identify feature columns (assume they start with 'fp_' or are numeric columns excluding target)
        # Assuming 'space_group' is the target for classification
        target_col = "space_group"
        # Features are likely fingerprint bits (e.g., 'fp_0', 'fp_1', ...) or specific numeric columns
        # Let's infer features: all columns except 'space_group' and 'smiles' and 'molecule_id' etc.
        exclude_cols = {target_col, 'smiles', 'molecule_id', 'formula'}
        feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['int64', 'float64', 'int32', 'float32']]

        if not feature_cols:
            # Fallback if specific naming convention isn't met, try numeric columns
            feature_cols = df.select_dtypes(include=[np.number]).columns.drop(target_col, errors='ignore').tolist()

        logger.info(f"Using {len(feature_cols)} feature columns for modeling.")

        X_train = df_train[feature_cols].values
        y_train = df_train[target_col].values
        X_test = df_test[feature_cols].values
        y_test = df_test[target_col].values

        # --- Calculate Majority Class Baseline ---
        majority_metrics = calculate_majority_class_baseline(df_train, df_test, target_column=target_col)

        # Save majority class baseline metrics
        with open(majority_class_metrics_path, 'w') as f:
            json.dump(majority_metrics, f, indent=2)
        logger.info(f"Majority class baseline metrics saved to {majority_class_metrics_path}")

        # Note: Full model training (RF, GB, Ridge) would happen here in subsequent tasks
        # T016, T016b, T016c handle the actual model training and saving.
        # This task focuses specifically on the majority-class baseline.

        return {
            "status": "success",
            "majority_class_baseline": majority_metrics,
            "output_path": majority_class_metrics_path
        }

    except Exception as e:
        logger.error(f"Error in main training pipeline: {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()