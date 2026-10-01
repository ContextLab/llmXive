"""
Evaluation module for crystal structure prediction models.

Calculates classification metrics (Accuracy, Macro-F1) and regression metrics
(R-squared, MAE) for trained models, comparing them against baseline metrics.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    r2_score,
    mean_absolute_error,
)
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import Ridge
from joblib import load

# Project imports
from config import (
    get_project_root,
    get_path_absolute,
    get_path_results,
    get_path_processed_data,
    get_path_models,
    ensure_directory,
)
from logging_config import get_logger, log_event
from ingestion.models import ModelMetrics

logger = get_logger(__name__)


def load_model(model_path: str):
    """Load a trained model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    return load(model_path)


def load_split_indices(split_path: str) -> Dict[str, List[int]]:
    """Load train/test split indices."""
    with open(split_path, 'r') as f:
        return json.load(f)


def load_dataset(dataset_path: str) -> pd.DataFrame:
    """Load the processed dataset."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    return pd.read_csv(dataset_path)


def load_baseline_metrics(baseline_path: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON."""
    if not os.path.exists(baseline_path):
        logger.warning(f"Baseline metrics file not found: {baseline_path}. Using defaults.")
        return {}
    with open(baseline_path, 'r') as f:
        return json.load(f)


def extract_features_targets(
    df: pd.DataFrame,
    split_indices: Dict[str, List[int]],
    target_col: str,
    feature_col: str = "fingerprint",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Any]:
    """
    Extract features and targets for train/test sets.

    Handles fingerprint string parsing and label encoding for classification.
    """
    train_idx = split_indices['train']
    test_idx = split_indices['test']

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Parse fingerprint strings to numpy arrays
    # Fingerprints are stored as comma-separated strings of 0/1
    def parse_fp(fp_str: str) -> np.ndarray:
        if isinstance(fp_str, str):
            return np.array([int(x) for x in fp_str.split(',')], dtype=np.float32)
        return fp_str

    X_train = np.array([parse_fp(fp) for fp in train_df[feature_col]])
    X_test = np.array([parse_fp(fp) for fp in test_df[feature_col]])

    y_train_raw = train_df[target_col].values
    y_test_raw = test_df[target_col].values

    # Check if target is numeric (regression) or categorical (classification)
    is_numeric = pd.api.types.is_numeric_dtype(df[target_col])

    if is_numeric:
        y_train = y_train_raw.astype(np.float32)
        y_test = y_test_raw.astype(np.float32)
        encoder = None
    else:
        # Classification: encode labels
        encoder = LabelEncoder()
        # Fit on combined to ensure all labels are known
        all_labels = np.concatenate([y_train_raw, y_test_raw])
        encoder.fit(all_labels)
        y_train = encoder.transform(y_train_raw)
        y_test = encoder.transform(y_test_raw)

    return X_train, X_test, y_train, y_test, encoder


def calculate_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, float]:
    """Calculate classification metrics: Accuracy and Macro-F1."""
    acc = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)
    return {
        'accuracy': float(acc),
        'macro_f1': float(f1_macro),
    }


def calculate_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, float]:
    """Calculate regression metrics: R-squared and MAE."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    return {
        'r_squared': float(r2),
        'mae': float(mae),
    }


def evaluate_model(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    is_classification: bool,
    encoder: Optional[Any] = None,
) -> Dict[str, float]:
    """Evaluate a single model and return metrics."""
    start_time = time.time()
    y_pred = model.predict(X_test)
    inference_time = time.time() - start_time

    if is_classification:
        # If encoded, we don't need to inverse transform for metrics calculation
        # sklearn metrics work on integer labels
        metrics = calculate_classification_metrics(y_test, y_pred)
    else:
        metrics = calculate_regression_metrics(y_test, y_pred)

    metrics['inference_time_seconds'] = float(inference_time)
    return metrics


def run_evaluation():
    """
    Main evaluation pipeline.

    Loads trained models, calculates metrics, compares against baselines,
    and saves results to data/results/model_evaluation.json.
    """
    project_root = get_project_root()
    logger.info("Starting model evaluation pipeline...")

    # Paths
    split_path = get_path_absolute(get_path_processed_data(), "split_indices.json")
    dataset_path = get_path_absolute(get_path_processed_data(), "grouped_dataset.csv")
    models_dir = get_path_absolute(get_path_models(), "")
    results_dir = get_path_results()
    ensure_directory(results_dir)

    # Baseline paths (generated by T017 and T017b)
    mw_baseline_path = get_path_absolute(results_dir, "mw_baseline_metrics.json")
    majority_baseline_path = get_path_absolute(results_dir, "majority_class_baseline_metrics.json")

    # Load data
    logger.info(f"Loading split indices from {split_path}")
    split_indices = load_split_indices(split_path)

    logger.info(f"Loading dataset from {dataset_path}")
    df = load_dataset(dataset_path)

    # Define targets
    # Based on task description: Space Group (classification) and Lattice Parameters (regression)
    # We assume the dataset has columns 'space_group' and 'lattice_params' (or similar)
    # Let's check the actual column names in the dataset
    # For this implementation, we assume 'space_group' and 'lattice_params' exist
    # If not, we adapt based on actual columns

    if 'space_group' not in df.columns:
        # Try to find a column with 'space' in name
        space_cols = [c for c in df.columns if 'space' in c.lower()]
        if space_cols:
            space_group_col = space_cols[0]
        else:
            raise ValueError("Could not find space group column in dataset")
    else:
        space_group_col = 'space_group'

    if 'lattice_params' not in df.columns:
        # Try to find a column with 'lattice' in name
        lattice_cols = [c for c in df.columns if 'lattice' in c.lower()]
        if lattice_cols:
            lattice_col = lattice_cols[0]
        else:
            raise ValueError("Could not find lattice parameters column in dataset")
    else:
        lattice_col = 'lattice_params'

    results = {
        'classification': {},
        'regression': {},
        'baselines': {},
        'comparison': {},
    }

    # --- Classification Evaluation (Space Group) ---
    logger.info(f"Evaluating classification model for target: {space_group_col}")
    try:
        X_train, X_test, y_train, y_test, encoder = extract_features_targets(
            df, split_indices, space_group_col
        )
        is_classification = True

        # Load and evaluate Random Forest
        rf_model_path = os.path.join(models_dir, "rf_model.pkl")
        if os.path.exists(rf_model_path):
            logger.info(f"Loading Random Forest model from {rf_model_path}")
            rf_model = load_model(rf_model_path)
            rf_metrics = evaluate_model(rf_model, X_test, y_test, is_classification, encoder)
            results['classification']['random_forest'] = rf_metrics
            logger.info(f"RF Classification Metrics: {rf_metrics}")
        else:
            logger.warning(f"Random Forest model not found at {rf_model_path}")

        # Load and evaluate Gradient Boosting
        gb_model_path = os.path.join(models_dir, "gb_model.pkl")
        if os.path.exists(gb_model_path):
            logger.info(f"Loading Gradient Boosting model from {gb_model_path}")
            gb_model = load_model(gb_model_path)
            gb_metrics = evaluate_model(gb_model, X_test, y_test, is_classification, encoder)
            results['classification']['gradient_boosting'] = gb_metrics
            logger.info(f"GB Classification Metrics: {gb_metrics}")
        else:
            logger.warning(f"Gradient Boosting model not found at {gb_model_path}")

        # Load baseline metrics
        majority_baseline = load_baseline_metrics(majority_baseline_path)
        if majority_baseline:
            results['baselines']['majority_class'] = majority_baseline
            # Compare
            if 'random_forest' in results['classification']:
                rf_acc = results['classification']['random_forest'].get('accuracy', 0)
                maj_acc = majority_baseline.get('accuracy', 0)
                results['comparison']['rf_vs_majority'] = {
                    'rf_accuracy': rf_acc,
                    'majority_accuracy': maj_acc,
                    'lift': rf_acc - maj_acc,
                }
        else:
            logger.warning("Majority class baseline metrics not found. Skipping comparison.")

    except Exception as e:
        logger.error(f"Error during classification evaluation: {e}", exc_info=True)
        results['classification']['error'] = str(e)

    # --- Regression Evaluation (Lattice Parameters) ---
    logger.info(f"Evaluating regression model for target: {lattice_col}")
    try:
        X_train, X_test, y_train, y_test, _ = extract_features_targets(
            df, split_indices, lattice_col
        )
        is_classification = False

        # Load and evaluate Ridge Regression
        ridge_model_path = os.path.join(models_dir, "ridge_model.pkl")
        if os.path.exists(ridge_model_path):
            logger.info(f"Loading Ridge Regression model from {ridge_model_path}")
            ridge_model = load_model(ridge_model_path)
            ridge_metrics = evaluate_model(ridge_model, X_test, y_test, is_classification)
            results['regression']['ridge'] = ridge_metrics
            logger.info(f"Ridge Regression Metrics: {ridge_metrics}")
        else:
            logger.warning(f"Ridge Regression model not found at {ridge_model_path}")

        # Load baseline metrics
        mw_baseline = load_baseline_metrics(mw_baseline_path)
        if mw_baseline:
            results['baselines']['molecular_weight'] = mw_baseline
            # Compare
            if 'ridge' in results['regression']:
                ridge_r2 = results['regression']['ridge'].get('r_squared', 0)
                mw_r2 = mw_baseline.get('r_squared', 0)
                results['comparison']['ridge_vs_mw'] = {
                    'ridge_r_squared': ridge_r2,
                    'mw_r_squared': mw_r2,
                    'lift_r2': ridge_r2 - mw_r2,
                }
        else:
            logger.warning("Molecular weight baseline metrics not found. Skipping comparison.")

    except Exception as e:
        logger.error(f"Error during regression evaluation: {e}", exc_info=True)
        results['regression']['error'] = str(e)

    # Save results
    output_path = os.path.join(results_dir, "model_evaluation.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Evaluation complete. Results saved to {output_path}")
    return results


def main():
    """Entry point for the evaluation script."""
    setup_logging = True  # Assuming logging is already configured globally or here
    run_evaluation()


if __name__ == "__main__":
    main()