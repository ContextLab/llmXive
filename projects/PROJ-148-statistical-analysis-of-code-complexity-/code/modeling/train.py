"""
Unified training script for the code complexity bug prediction pipeline.
Orchestrates the training of both primary and alternative models,
computes importance metrics, compares model performance, and persists artifacts.

This script reconciles the run-book (quickstart.md) which invokes this path,
with the existing implementation split across train_primary.py, train_alternative.py,
importance.py, compare_models.py, and persist_models.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from utils.config import set_random_seed, get_seed
from utils.logging import get_logger
from modeling.train_primary import train_primary
from modeling.train_alternative import train_alternative
from modeling.importance import save_importance
from modeling.compare_models import compare_models
from modeling.persist_models import main as persist_models_main

logger = get_logger(__name__)


def run_training_pipeline(
    train_path: str,
    test_path: str,
    output_dir: str,
    seed: int = 42
) -> dict:
    """
    Execute the full training pipeline:
    1. Train primary model (L1 Logistic Regression)
    2. Train alternative model (Random Forest)
    3. Extract and save feature importances
    4. Compare models (ROC-AUC, Spearman correlation)
    5. Persist model artifacts

    Args:
        train_path: Path to training CSV
        test_path: Path to test CSV
        output_dir: Directory to save results and models
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing evaluation metrics and paths to artifacts
    """
    set_random_seed(seed)
    logger.info(f"Starting training pipeline with seed {seed}")

    # Load data
    logger.info(f"Loading training data from {train_path}")
    train_df = pd.read_csv(train_path)
    logger.info(f"Loading test data from {test_path}")
    test_df = pd.read_csv(test_path)

    if train_df.empty or test_df.empty:
        raise ValueError("Training or test data is empty. Check data pipeline outputs.")

    # Identify features and target
    # Assuming 'bug_label' is the target column based on project specs
    target_col = "bug_label"
    feature_cols = [c for c in train_df.columns if c != target_col]

    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Train Primary Model
    logger.info("Training primary L1-regularized logistic regression model...")
    primary_model, primary_metrics = train_primary(
        X_train, y_train, X_test, y_test,
        max_iter=100,
        seed=seed
    )
    logger.info(f"Primary model ROC-AUC: {primary_metrics['roc_auc']:.4f}")

    # 2. Train Alternative Model
    logger.info("Training alternative Random Forest model...")
    alt_model, alt_metrics = train_alternative(
        X_train, y_train, X_test, y_test,
        n_estimators=100,
        max_depth=10,
        seed=seed
    )
    logger.info(f"Alternative model ROC-AUC: {alt_metrics['roc_auc']:.4f}")

    # 3. Extract and Save Importances
    logger.info("Extracting and saving feature importances...")
    importance_path = output_path / "feature_importance.json"
    save_importance(
        primary_model, alt_model, feature_cols,
        output_path=str(importance_path)
    )
    logger.info(f"Importances saved to {importance_path}")

    # 4. Compare Models
    logger.info("Comparing model performance...")
    comparison_results = compare_models(
        primary_metrics, alt_metrics,
        primary_model, alt_model,
        X_train, y_train, X_test, y_test,
        feature_names=feature_cols
    )
    comparison_path = output_path / "model_comparison.json"
    import json
    with open(comparison_path, "w") as f:
        json.dump(comparison_results, f, indent=2, default=str)
    logger.info(f"Comparison results saved to {comparison_path}")

    # 5. Persist Models
    logger.info("Persisting model artifacts...")
    # We need to temporarily set up args for persist_models_main
    # Or call the internal logic directly if available.
    # Based on API surface, persist_models.py has a main() that expects args.
    # We will construct the paths and call it via argument parsing simulation or direct logic.
    # Since the API surface only shows 'main', we will assume it handles the file saving.
    # To be safe and avoid arg parsing overhead, we will save the models ourselves here
    # using the logic implied by persist_models, or call main with a constructed namespace.
    
    # Re-implementing the save logic here to ensure it runs without CLI args:
    primary_pkl = output_path / "primary.pkl"
    alt_pkl = output_path / "alternative.pkl"
    
    import joblib
    joblib.dump(primary_model, primary_pkl)
    joblib.dump(alt_model, alt_pkl)
    
    logger.info(f"Primary model saved to {primary_pkl}")
    logger.info(f"Alternative model saved to {alt_pkl}")

    return {
        "primary_roc_auc": primary_metrics["roc_auc"],
        "alternative_roc_auc": alt_metrics["roc_auc"],
        "spearman_corr": comparison_results.get("spearman_correlation"),
        "primary_model_path": str(primary_pkl),
        "alternative_model_path": str(alt_pkl),
        "comparison_path": str(comparison_path)
    }


def main():
    parser = argparse.ArgumentParser(
        description="Train and evaluate code complexity bug prediction models."
    )
    parser.add_argument(
        "--train-data",
        type=str,
        required=True,
        help="Path to the training CSV file (e.g., data/splits/train.csv)"
    )
    parser.add_argument(
        "--test-data",
        type=str,
        required=True,
        help="Path to the test CSV file (e.g., data/splits/test.csv)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/model",
        help="Directory to save model artifacts and metrics"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    try:
        results = run_training_pipeline(
            train_path=args.train_data,
            test_path=args.test_data,
            output_dir=args.output_dir,
            seed=args.seed
        )
        logger.info("Training pipeline completed successfully.")
        logger.info(f"Results: {results}")
        return 0
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())