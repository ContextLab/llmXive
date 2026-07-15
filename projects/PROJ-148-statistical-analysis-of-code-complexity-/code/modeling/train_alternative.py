from __future__ import annotations

import argparse
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.exceptions import NotFittedError

from utils.logging import get_logger
from utils.config import get_seed

logger = get_logger(__name__)


def load_split_data(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the train and test splits from CSV files.
    Expects data_dir to contain 'train.csv' and 'test.csv'.
    Returns (train_df, test_df).
    """
    train_path = data_dir / "train.csv"
    test_path = data_dir / "test.csv"

    if not train_path.exists():
        raise FileNotFoundError(f"Train data file not found: {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Test data file not found: {test_path}")

    logger.info(f"Loading train data from {train_path}")
    train_df = pd.read_csv(train_path)
    logger.info(f"Train data shape: {train_df.shape}")

    logger.info(f"Loading test data from {test_path}")
    test_df = pd.read_csv(test_path)
    logger.info(f"Test data shape: {test_df.shape}")

    return train_df, test_df


def load_primary_model_metrics(model_dir: Path) -> float:
    """
    Load the primary model's ROC-AUC score from the evaluation metrics JSON.
    Expects model_dir to contain 'metrics.json' with a 'primary_roc_auc' key.
    """
    metrics_path = model_dir / "metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Primary model metrics file not found: {metrics_path}. "
            "Ensure the primary model has been trained and evaluated first."
        )

    with open(metrics_path, 'r') as f:
        metrics = json.load(f)

    if 'primary_roc_auc' not in metrics:
        raise ValueError(
            f"'primary_roc_auc' not found in {metrics_path}. "
            "Ensure the primary model evaluation script wrote this key."
        )

    primary_roc_auc = metrics['primary_roc_auc']
    logger.info(f"Loaded primary model ROC-AUC: {primary_roc_auc:.4f}")
    return primary_roc_auc


def train_alternative(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    primary_roc_auc: float,
    feature_cols: list,
    target_col: str,
    n_estimators: int = 100,
    max_depth: int = 10,
    random_state: int = 42
) -> Tuple[Any, float]:
    """
    Train a Random Forest alternative model and assert its ROC-AUC is within ±0.05 of the primary model.

    Parameters
    ----------
    train_df : pd.DataFrame
        Training data.
    test_df : pd.DataFrame
        Test data.
    primary_roc_auc : float
        ROC-AUC score of the primary model.
    feature_cols : list
        List of column names to use as features.
    target_col : str
        Name of the target column.
    n_estimators : int
        Number of trees in the forest.
    max_depth : int
        Maximum depth of the tree.
    random_state : int
        Random seed for reproducibility.

    Returns
    -------
    Tuple[RandomForestClassifier, float]
        The trained model and its ROC-AUC score.
    """
    logger.info("Preparing features and target for training...")
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    # Handle potential missing values in features
    if X_train.isnull().any().any() or X_test.isnull().any().any():
        logger.warning("Missing values detected in features. Filling with median.")
        median_fill = X_train.median()
        X_train = X_train.fillna(median_fill)
        X_test = X_test.fillna(median_fill)

    logger.info(f"Training Random Forest with n_estimators={n_estimators}, max_depth={max_depth}")
    rf_model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        verbose=1
    )
    rf_model.fit(X_train, y_train)

    logger.info("Evaluating alternative model on test set...")
    y_pred_proba = rf_model.predict_proba(X_test)[:, 1]

    # Ensure binary classification for roc_auc_score
    if len(np.unique(y_test)) < 2:
        raise ValueError(
            f"Test set must contain at least two classes for ROC-AUC calculation. "
            f"Found unique values: {np.unique(y_test)}"
        )

    alternative_roc_auc = roc_auc_score(y_test, y_pred_proba)
    logger.info(f"Alternative model (Random Forest) ROC-AUC: {alternative_roc_auc:.4f}")
    logger.info(f"Primary model ROC-AUC: {primary_roc_auc:.4f}")

    diff = abs(alternative_roc_auc - primary_roc_auc)
    logger.info(f"Difference in ROC-AUC: {diff:.4f}")

    # Assert the requirement: ROC-AUC within ±0.05 of primary
    tolerance = 0.05
    if diff > tolerance:
        error_msg = (
            f"Alternative model ROC-AUC ({alternative_roc_auc:.4f}) is not within "
            f"±{tolerance} of primary model ROC-AUC ({primary_roc_auc:.4f}). "
            f"Difference: {diff:.4f}"
        )
        logger.error(error_msg)
        raise AssertionError(error_msg)

    logger.info(f"Success: Alternative model ROC-AUC is within ±{tolerance} of primary model.")

    return rf_model, alternative_roc_auc


def main():
    parser = argparse.ArgumentParser(
        description="Train alternative Random Forest model and compare with primary."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Directory containing train.csv and test.csv"
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        required=True,
        help="Directory containing primary model metrics (metrics.json) and where to save alternative model."
    )
    parser.add_argument(
        "--target-col",
        type=str,
        default="bug_label",
        help="Name of the target column."
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="Number of trees in the Random Forest."
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum depth of the tree."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed. If None, uses global config seed."
    )
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Resolve paths
    data_dir = args.data_dir
    model_dir = args.model_dir
    model_dir.mkdir(parents=True, exist_ok=True)

    # Get random seed
    seed = args.seed if args.seed is not None else get_seed()
    logger.info(f"Using random seed: {seed}")

    try:
        # 1. Load data
        train_df, test_df = load_split_data(data_dir)

        # Determine feature columns (exclude target and metadata columns)
        exclude_cols = {args.target_col, 'project_name', 'project_id', 'file_path'}
        feature_cols = [c for c in train_df.columns if c not in exclude_cols]
        logger.info(f"Using {len(feature_cols)} features: {feature_cols}")

        # 2. Load primary model metrics
        primary_roc_auc = load_primary_model_metrics(model_dir)

        # 3. Train alternative model
        rf_model, alternative_roc_auc = train_alternative(
            train_df=train_df,
            test_df=test_df,
            primary_roc_auc=primary_roc_auc,
            feature_cols=feature_cols,
            target_col=args.target_col,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            random_state=seed
        )

        # 4. Save the alternative model
        model_path = model_dir / "alternative.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(rf_model, f)
        logger.info(f"Alternative model saved to {model_path}")

        # 5. Save alternative model metrics
        metrics = {
            "model_type": "RandomForest",
            "n_estimators": args.n_estimators,
            "max_depth": args.max_depth,
            "roc_auc": float(alternative_roc_auc),
            "primary_roc_auc": float(primary_roc_auc),
            "difference": float(abs(alternative_roc_auc - primary_roc_auc)),
            "tolerance": 0.05,
            "seed": seed
        }
        metrics_path = model_dir / "alternative_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Alternative model metrics saved to {metrics_path}")

        print(f"Task T021 completed successfully. Alternative ROC-AUC: {alternative_roc_auc:.4f}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()