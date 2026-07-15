from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import joblib
import numpy as np

from utils.config import get_config, set_random_seed, get_seed
from utils.logging import get_logger
from modeling.train_primary import train_primary
from modeling.train_alternative import train_alternative
from modeling.compare_models import compare_models
from modeling.importance import save_importance
from modeling.collinearity import drop_high_vif_features, compute_vif

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train primary and alternative models for bug prediction."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Directory containing the preprocessed train/test CSV files.",
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("data/model"),
        help="Directory to save trained model artifacts.",
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
        default=0.1,
        help="Regularization strength for L1 logistic regression.",
    )
    return parser.parse_args()


def load_split_data(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """
    Load train and test data from the data directory.
    Expects 'train_data.csv' and 'test_data.csv' to exist.
    Returns X_train, X_test, and feature_names.
    """
    train_path = data_dir / "train_data.csv"
    test_path = data_dir / "test_data.csv"

    if not train_path.exists():
        raise FileNotFoundError(f"Train data file not found at {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Test data file not found at {test_path}")

    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)

    # Identify target column (assumed to be 'bug_label' based on data model)
    target_col = "bug_label"
    if target_col not in df_train.columns:
        raise ValueError(f"Target column '{target_col}' not found in training data.")

    feature_cols = [c for c in df_train.columns if c != target_col]

    X_train = df_train[feature_cols].values
    y_train = df_train[target_col].values
    X_test = df_test[feature_cols].values
    y_test = df_test[target_col].values

    return X_train, X_test, y_train, y_test, feature_cols


def run_training_pipeline(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    feature_names: list[str],
    model_dir: Path,
    alpha: float,
    seed: int,
) -> Dict[str, Any]:
    """
    Execute the full training pipeline:
    1. Collinearity check (VIF) and feature reduction if needed.
    2. Train primary L1 Logistic Regression.
    3. Train alternative Random Forest.
    4. Compare models.
    5. Save artifacts.
    """
    set_random_seed(seed)
    model_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Collinearity Diagnostics
    logger.info("Performing collinearity diagnostics (VIF)...")
    # We need a DataFrame for VIF calculation
    df_train_temp = pd.DataFrame(X_train, columns=feature_names)
    df_test_temp = pd.DataFrame(X_test, columns=feature_names)

    # Compute VIF and drop high VIF features
    # Threshold usually 5 or 10. Using 10 as per common practice.
    X_train_clean, X_test_clean, kept_features = drop_high_vif_features(
        df_train_temp, df_test_temp, y_train, threshold=10.0
    )

    if len(kept_features) == 0:
        raise RuntimeError("All features were dropped due to high collinearity.")

    logger.info(f"Kept features after VIF filtering: {kept_features}")

    # Step 2: Train Primary Model (L1 Logistic Regression)
    logger.info("Training primary L1 Logistic Regression model...")
    primary_model, primary_metrics = train_primary(
        X_train_clean, y_train, X_test_clean, y_test, alpha=alpha, max_iter=100
    )

    # Step 3: Train Alternative Model (Random Forest)
    logger.info("Training alternative Random Forest model...")
    alt_model, alt_metrics = train_alternative(
        X_train_clean, y_train, X_test_clean, y_test, primary_metrics
    )

    # Step 4: Compare Models
    logger.info("Comparing models...")
    comparison = compare_models(
        primary_model, alt_model, X_test_clean, y_test, kept_features
    )

    # Step 5: Save Artifacts
    logger.info("Saving model artifacts...")

    # Save models
    joblib.dump(primary_model, model_dir / "primary.pkl")
    joblib.dump(alt_model, model_dir / "alternative.pkl")

    # Save importance
    save_importance(
        model_dir / "feature_importance.json",
        kept_features,
        primary_model,
        alt_model,
    )

    # Save comparison metrics
    comparison_path = model_dir / "comparison_metrics.json"
    with open(comparison_path, "w") as f:
        import json
        json.dump(comparison, f, indent=2)

    return {
        "primary_metrics": primary_metrics,
        "alternative_metrics": alt_metrics,
        "comparison": comparison,
        "kept_features": kept_features,
    }


def main() -> None:
    args = parse_args()
    set_random_seed(args.seed)

    logger.info(f"Starting training pipeline with seed {args.seed}")
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Model directory: {args.model_dir}")

    try:
        X_train, X_test, y_train, y_test, feature_names = load_split_data(
            args.data_dir
        )

        results = run_training_pipeline(
            X_train,
            X_test,
            y_train,
            y_test,
            feature_names,
            args.model_dir,
            args.alpha,
            args.seed,
        )

        logger.info("Training pipeline completed successfully.")
        logger.info(f"Primary Model ROC-AUC: {results['primary_metrics'].get('roc_auc', 'N/A')}")
        logger.info(f"Alternative Model ROC-AUC: {results['alternative_metrics'].get('roc_auc', 'N/A')}")

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()