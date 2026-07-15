from __future__ import annotations

import argparse
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Tuple

import pandas as pd
import numpy as np
import joblib

from utils.config import get_config, set_random_seed
from utils.logging import get_logger
from modeling.train_primary import train_primary
from modeling.train_alternative import train_alternative
from modeling.importance import save_importance

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train primary and alternative bug prediction models."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Path to directory containing train/test split CSVs.",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="data/model",
        help="Path to directory where models and metrics will be saved.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=1.0,
        help="Regularization strength for L1 logistic regression.",
    )
    return parser.parse_args()


def load_split_data(data_dir: Path) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Load the preprocessed train and test datasets.
    Expects:
      - train.csv: features + target
      - test.csv: features + target
    Returns:
      X_train, y_train, X_test, y_test
    """
    train_path = data_dir / "train.csv"
    test_path = data_dir / "test.csv"

    if not train_path.exists():
        raise FileNotFoundError(f"Train data file not found: {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Test data file not found: {test_path}")

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    # Assume 'bug_label' is the target column
    target_col = "bug_label"
    feature_cols = [c for c in train_df.columns if c != target_col]

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    logger.info(f"Loaded train data: {X_train.shape}, test data: {X_test.shape}")
    return X_train, y_train, X_test, y_test


def run_training_pipeline(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_dir: Path,
    alpha: float,
    seed: int,
) -> Dict[str, Any]:
    """
    Execute the full training workflow:
    1. Train primary (L1 Logistic Regression)
    2. Train alternative (Random Forest)
    3. Extract and save importance
    4. Persist models
    """
    set_random_seed(seed)
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Training primary model (L1 Logistic Regression)...")
    primary_model, primary_metrics = train_primary(
        X_train, y_train, X_test, y_test, alpha=alpha, seed=seed
    )

    logger.info("Training alternative model (Random Forest)...")
    alternative_model, alternative_metrics = train_alternative(
        X_train, y_train, X_test, y_test, seed=seed
    )

    logger.info("Extracting feature importance...")
    importance_data = {
        "primary_coefficients": dict(zip(X_train.columns, primary_model.coef_[0])),
        "alternative_importance": dict(
            zip(X_train.columns, alternative_model.feature_importances_)
        ),
    }
    save_importance(importance_data, model_dir / "importance.json")

    logger.info("Persisting models...")
    joblib.dump(primary_model, model_dir / "primary.pkl")
    joblib.dump(alternative_model, model_dir / "alternative.pkl")

    # Save metrics
    metrics_path = model_dir / "training_metrics.json"
    metrics_data = {
        "primary": primary_metrics,
        "alternative": alternative_metrics,
    }
    with open(metrics_path, "w") as f:
        json.dump(metrics_data, f, indent=2)

    logger.info(f"Training complete. Models saved to {model_dir}")
    return metrics_data


def main() -> int:
    args = parse_args()
    config = get_config()
    set_random_seed(args.seed)

    logger.info(f"Starting training pipeline with seed {args.seed}")
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Model output directory: {args.model_dir}")

    data_dir = Path(args.data_dir)
    model_dir = Path(args.model_dir)

    try:
        X_train, y_train, X_test, y_test = load_split_data(data_dir)
        run_training_pipeline(
            X_train, y_train, X_test, y_test, model_dir, args.alpha, args.seed
        )
        return 0
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())