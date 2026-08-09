"""
Model training module for Random Forest and TabPFN baselines.

Implements 5-fold cross-validation for Random Forest training with
performance metrics (RMSE, MAE, R²) and execution time tracking.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_validate
from sklearn.metrics import make_scorer, mean_squared_error, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from code.utils.timer import Timer, timed_operation
from code.utils.logger import get_logger
from code.utils.config import get_config

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

logger = get_logger(__name__)


def load_training_data(data_path: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load processed data from CSV and separate features and targets.

    Args:
        data_path: Path to the processed CSV file.

    Returns:
        Tuple of (features, targets, feature_names)
    """
    import pandas as pd

    df = pd.read_csv(data_path)

    # Identify target column (biomass)
    target_col = "biomass_kg_per_m2"
    if target_col not in df.columns:
        # Try common variations
        possible_targets = ["biomass", "dry_biomass", "target"]
        found = False
        for t in possible_targets:
            if t in df.columns:
                target_col = t
                found = True
                break
        if not found:
            raise ValueError(f"Could not find biomass target column in {data_path}. Available columns: {df.columns.tolist()}")

    # Separate features and target
    # Exclude non-feature columns
    exclude_cols = [target_col, "site_id", "scene_id", "cloud_flag"]
    feature_cols = [col for col in df.columns if col not in exclude_cols]

    if len(feature_cols) == 0:
        raise ValueError(f"No feature columns found in {data_path}")

    features = df[feature_cols].values
    targets = df[target_col].values
    feature_names = feature_cols

    logger.info(f"Loaded {features.shape[0]} samples with {features.shape[1]} features")
    return features, targets, feature_names


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Compute regression metrics: RMSE, MAE, R².

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        Dictionary with metric names and values.
    """
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2)
    }


def train_random_forest_cv(
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    random_state: int = 42,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Train a Random Forest model using 5-fold cross-validation.

    Args:
        X: Feature matrix.
        y: Target vector.
        n_splits: Number of CV folds.
        random_state: Random seed for reproducibility.
        n_estimators: Number of trees in the forest.
        max_depth: Maximum tree depth.
        output_path: Path to save results JSON.

    Returns:
        Dictionary containing metrics per fold and aggregate statistics.
    """
    logger.info(f"Starting Random Forest CV with {n_splits} folds")

    # Define scoring metrics
    scoring = {
        "rmse": make_scorer(mean_squared_error, squared=False),
        "mae": make_scorer(mean_absolute_error),
        "r2": make_scorer(r2_score)
    }

    # Create the model
    rf_model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        verbose=1
    )

    # Create pipeline with scaling (optional but good practice)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", rf_model)
    ])

    # Setup KFold
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    # Run cross-validation
    with timed_operation("Random Forest 5-Fold CV") as timer:
        cv_results = cross_validate(
            pipeline,
            X,
            y,
            cv=kfold,
            scoring=scoring,
            return_train_score=False,
            n_jobs=-1,
            verbose=1
        )

    # Organize results
    fold_metrics = []
    for i in range(n_splits):
        fold_data = {
            "fold": i + 1,
            "rmse": float(cv_results["test_rmse"][i]),
            "mae": float(cv_results["test_mae"][i]),
            "r2": float(cv_results["test_r2"][i])
        }
        fold_metrics.append(fold_data)

    # Aggregate statistics
    aggregate = {
        "rmse_mean": float(np.mean(cv_results["test_rmse"])),
        "rmse_std": float(np.std(cv_results["test_rmse"])),
        "mae_mean": float(np.mean(cv_results["test_mae"])),
        "mae_std": float(np.std(cv_results["test_mae"])),
        "r2_mean": float(np.mean(cv_results["test_r2"])),
        "r2_std": float(np.std(cv_results["test_r2"]))
    }

    result = {
        "model_type": "RandomForest",
        "n_splits": n_splits,
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "random_state": random_state,
        "execution_time_seconds": timer.elapsed_wall,
        "fold_metrics": fold_metrics,
        "aggregate_metrics": aggregate
    }

    logger.info(f"Random Forest CV completed. R²: {aggregate['r2_mean']:.4f} ± {aggregate['r2_std']:.4f}")

    # Save results if path provided
    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {output_path}")

    return result


def main():
    """
    Main entry point for Random Forest training script.
    """
    parser = argparse.ArgumentParser(description="Train Random Forest with 5-fold CV")
    parser.add_argument(
        "--data",
        type=str,
        default="data/processed/biomass_data.csv",
        help="Path to processed data CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/final/model_results/random_forest_cv_results.json",
        help="Path to save results JSON"
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="Number of trees in the forest"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum tree depth (None for unlimited)"
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed"
    )
    parser.add_argument(
        "--n-splits",
        type=int,
        default=5,
        help="Number of CV folds"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger.info("Starting Random Forest training pipeline")

    # Load data
    try:
        X, y, feature_names = load_training_data(args.data)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Train model
    try:
        results = train_random_forest_cv(
            X=X,
            y=y,
            n_splits=args.n_splits,
            random_state=args.random_state,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            output_path=args.output
        )
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

    logger.info("Random Forest training completed successfully")
    return results


if __name__ == "__main__":
    main()
