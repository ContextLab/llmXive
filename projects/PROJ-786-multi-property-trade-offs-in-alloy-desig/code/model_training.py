"""
Model Training Module for Multi-Property Trade-Offs in Alloy Design.

Implements GradientBoostingRegressor models for Bulk and Shear Moduli prediction
with CPU constraints (n_jobs=2) and memory limits.
"""
import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.exceptions import ConvergenceWarning
import warnings

# Project imports
from config import load_environment, parse_cli_args, get_config, verify_config
from utils.logging_config import get_logger, log_info_with_context, log_error_with_context

# Suppress sklearn convergence warnings for cleaner logs
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# Constants
DEFAULT_INPUT_PATH = "data/processed/encoded_alloys.csv"
DEFAULT_OUTPUT_DIR = "data/processed"
DEFAULT_OUTPUT_FILE = "model_metrics.json"
DEFAULT_MODEL_DIR = "models"
DEFAULT_TEST_SIZE = 0.2
DEFAULT_RANDOM_STATE = 42
DEFAULT_N_JOBS = 2
MAX_MEMORY_GB = 7

logger = get_logger(__name__)


def load_encoded_data(input_path: str) -> pd.DataFrame:
    """
    Load the encoded alloy dataset from CSV.

    Args:
        input_path: Path to the encoded CSV file.

    Returns:
        DataFrame containing encoded features and target properties.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        log_error_with_context(logger, f"Input file not found: {input_path}", "DataLoadingError")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    required_cols = ["bulk_modulus", "shear_modulus"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        log_error_with_context(
            logger,
            f"Missing required columns: {missing_cols}",
            "DataValidationError"
        )
        raise ValueError(f"Missing required columns: {missing_cols}")

    log_info_with_context(logger, f"Loaded {len(df)} rows from {input_path}")
    return df


def prepare_features_targets(
    df: pd.DataFrame,
    target_col: str
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Separate features from the target variable.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.

    Returns:
        Tuple of (features, targets, feature_names).
    """
    feature_cols = [col for col in df.columns if col not in ["bulk_modulus", "shear_modulus"]]
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")

    X = df[feature_cols].values
    y = df[target_col].values

    # Handle any remaining NaNs in features by imputing with median
    if np.isnan(X).any():
        median_vals = np.nanmedian(X, axis=0)
        X = np.nan_to_num(X, nan=median_vals)

    if np.isnan(y).any():
        log_warning_with_context(logger, "Target variable contains NaNs. Dropping those rows.")
        valid_mask = ~np.isnan(df[target_col].values)
        X = X[valid_mask]
        y = y[valid_mask]

    return X, y, feature_cols


def train_model(
    X: np.ndarray,
    y: np.ndarray,
    target_name: str,
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_jobs: int = DEFAULT_N_JOBS
) -> Dict[str, Any]:
    """
    Train a GradientBoostingRegressor model and evaluate it.

    Args:
        X: Feature matrix.
        y: Target vector.
        target_name: Name of the property being predicted.
        test_size: Fraction of data for testing.
        random_state: Random seed for reproducibility.
        n_jobs: Number of parallel jobs.

    Returns:
        Dictionary containing model metrics and trained model.
    """
    log_info_with_context(logger, f"Training model for {target_name}...")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Initialize model with constraints
    # max_memory is not a direct parameter in sklearn, but we limit complexity
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        subsample=0.8,
        random_state=random_state,
        n_jobs=n_jobs
    )

    # Train
    model.fit(X_train, y_train)

    # Predict
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    # Calculate metrics
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    test_mse = mean_squared_error(y_test, y_test_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)

    # Cross-validation score (5-fold)
    # Note: This might be slow for large datasets, but we limit n_jobs
    cv_scores = cross_val_score(
        model, X_train, y_train, cv=5, scoring='r2', n_jobs=n_jobs
    )
    cv_r2_mean = cv_scores.mean()
    cv_r2_std = cv_scores.std()

    results = {
        "target": target_name,
        "train_r2": float(train_r2),
        "test_r2": float(test_r2),
        "test_mse": float(test_mse),
        "test_mae": float(test_mae),
        "cv_r2_mean": float(cv_r2_mean),
        "cv_r2_std": float(cv_r2_std),
        "n_train_samples": len(y_train),
        "n_test_samples": len(y_test),
        "n_features": X.shape[1]
    }

    log_info_with_context(
        logger,
        f"{target_name} Model Results: Test R²={test_r2:.4f}, CV R²={cv_r2_mean:.4f}±{cv_r2_std:.4f}"
    )

    return {
        "metrics": results,
        "model": model
    }


def save_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save model metrics to a JSON file.

    Args:
        metrics: Dictionary of metrics to save.
        output_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    log_info_with_context(logger, f"Metrics saved to {output_path}")


def save_models(model_results: Dict[str, Dict], output_dir: str) -> None:
    """
    Save trained models to disk using joblib (if available) or pickle.

    Args:
        model_results: Dictionary containing trained models.
        output_dir: Directory to save model files.
    """
    try:
        import joblib
        use_joblib = True
    except ImportError:
        import pickle as joblib
        use_joblib = False

    os.makedirs(output_dir, exist_ok=True)

    for target_name, result in model_results.items():
        model_path = os.path.join(output_dir, f"{target_name}_model.pkl")
        if use_joblib:
            joblib.dump(result["model"], model_path)
        else:
            with open(model_path, 'wb') as f:
                joblib.dump(result["model"], f)
        log_info_with_context(logger, f"Model saved to {model_path}")


def run_training_pipeline(
    input_path: str = DEFAULT_INPUT_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    model_dir: str = DEFAULT_MODEL_DIR,
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_jobs: int = DEFAULT_N_JOBS
) -> Dict[str, Any]:
    """
    Execute the full model training pipeline for Bulk and Shear Moduli.

    Args:
        input_path: Path to encoded data.
        output_dir: Directory for metrics output.
        model_dir: Directory for model storage.
        test_size: Test set fraction.
        random_state: Random seed.
        n_jobs: Number of parallel jobs.

    Returns:
        Dictionary containing all training results.
    """
    log_info_with_context(logger, "Starting model training pipeline...")

    # Load data
    df = load_encoded_data(input_path)

    # Prepare and train for Bulk Modulus
    X_bulk, y_bulk, feature_names = prepare_features_targets(df, "bulk_modulus")
    bulk_result = train_model(
        X_bulk, y_bulk, "bulk_modulus", test_size, random_state, n_jobs
    )

    # Prepare and train for Shear Modulus
    X_shear, y_shear, _ = prepare_features_targets(df, "shear_modulus")
    shear_result = train_model(
        X_shear, y_shear, "shear_modulus", test_size, random_state, n_jobs
    )

    # Aggregate metrics
    all_metrics = {
        "bulk_modulus": bulk_result["metrics"],
        "shear_modulus": shear_result["metrics"],
        "training_config": {
            "test_size": test_size,
            "random_state": random_state,
            "n_jobs": n_jobs,
            "input_file": input_path
        }
    }

    # Save outputs
    metrics_path = os.path.join(output_dir, DEFAULT_OUTPUT_FILE)
    save_metrics(all_metrics, metrics_path)

    save_models({
        "bulk_modulus": bulk_result,
        "shear_modulus": shear_result
    }, model_dir)

    log_info_with_context(logger, "Model training pipeline completed successfully.")
    return all_metrics


def main() -> int:
    """Main entry point for the model training script."""
    # Load environment and config
    load_environment()
    args = parse_cli_args()
    config = get_config()
    verify_config(config)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Train alloy property prediction models.")
    parser.add_argument(
        "--input",
        type=str,
        default=args.get("input", DEFAULT_INPUT_PATH),
        help="Path to encoded data CSV"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=args.get("output_dir", DEFAULT_OUTPUT_DIR),
        help="Directory for metrics output"
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default=args.get("model_dir", DEFAULT_MODEL_DIR),
        help="Directory for model files"
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=args.get("test_size", DEFAULT_TEST_SIZE),
        help="Fraction of data for testing"
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=args.get("random_state", DEFAULT_RANDOM_STATE),
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=args.get("n_jobs", DEFAULT_N_JOBS),
        help="Number of parallel jobs (CPU constraint)"
    )
    parsed_args = parser.parse_args()

    # Ensure n_jobs respects hardware constraint
    if parsed_args.n_jobs > 2:
        log_warning_with_context(
            logger,
            f"n_jobs={parsed_args.n_jobs} exceeds recommended 2 for CPU constraint. Setting to 2."
        )
        parsed_args.n_jobs = 2

    try:
        run_training_pipeline(
            input_path=parsed_args.input,
            output_dir=parsed_args.output_dir,
            model_dir=parsed_args.model_dir,
            test_size=parsed_args.test_size,
            random_state=parsed_args.random_state,
            n_jobs=parsed_args.n_jobs
        )
        return 0
    except Exception as e:
        log_error_with_context(logger, str(e), "TrainingError")
        return 1


if __name__ == "__main__":
    sys.exit(main())