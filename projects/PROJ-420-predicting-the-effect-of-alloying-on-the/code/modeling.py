"""Modeling pipeline for predicting Poisson's ratio of aluminum alloys.

This module implements the core modeling logic including:
- ILR transformation for compositional data
- Dataset splitting (80/20 train/test)
- Cross-validation for hyperparameter tuning
- Random Forest model training and evaluation
- Metric computation and serialization
"""

from __future__ import annotations

import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from compositional import ilr
from joblib import dump, load
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_absolute_error

# Import project utilities
from config import get_config
from logging_config import get_logger, log_operation

# Constants
CONFIG = get_config()
logger = get_logger(__name__)

# Ensure directories exist
DATA_PROCESSED = Path(CONFIG.data_processed)
MODELS_DIR = Path(CONFIG.models)
RESULTS_DIR = Path(CONFIG.results)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_features_and_target(
    parquet_path: str = "data/processed/alloys_clean.parquet"
) -> Tuple[pd.DataFrame, pd.Series]:
    """Load the cleaned dataset and separate features from target.

    Args:
        parquet_path: Path to the cleaned parquet file.

    Returns:
        Tuple of (feature DataFrame, target Series).
    """
    @log_operation("load_features_and_target")
    def _inner():
        full_path = Path(CONFIG.data_root) / parquet_path
        if not full_path.exists():
            raise FileNotFoundError(f"Cleaned dataset not found at {full_path}")

        df = pd.read_parquet(full_path)

        # Features: Cu, Mg, Si, Zn, Mn atomic fractions
        feature_cols = ["Cu", "Mg", "Si", "Zn", "Mn"]
        X = df[feature_cols].copy()
        y = df["poisson_ratio"].copy()

        logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features")
        return X, y

    return _inner()


def apply_ilr_transformation(
    X: pd.DataFrame,
    feature_cols: List[str] = None
) -> pd.DataFrame:
    """Apply Isometric Log-Ratio (ILR) transformation to compositional data.

    Args:
        X: DataFrame with compositional columns (atomic fractions).
        feature_cols: List of compositional column names. Defaults to ['Cu', 'Mg', 'Si', 'Zn', 'Mn'].

    Returns:
        DataFrame with ILR-transformed features.
    """
    @log_operation("apply_ilr_transformation")
    def _inner():
        if feature_cols is None:
            feature_cols = ["Cu", "Mg", "Si", "Zn", "Mn"]

        X_ilr = X[feature_cols].copy()

        # Ensure no zeros (ILR requires positive values)
        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        X_ilr = X_ilr.replace(0, epsilon)

        # Apply ILR transformation
        # compositional.ilr expects a DataFrame or array and returns ILR coordinates
        ilr_coords = ilr(X_ilr.values)

        # Create DataFrame with ILR coordinate names
        ilr_col_names = [f"ilr_{i}" for i in range(ilr_coords.shape[1])]
        X_ilr_transformed = pd.DataFrame(ilr_coords, columns=ilr_col_names, index=X.index)

        logger.info(f"Applied ILR transformation: {len(feature_cols)} -> {len(ilr_col_names)} coordinates")
        return X_ilr_transformed

    return _inner()


def split_dataset(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, Dict[str, List[int]]]:
    """Split dataset into training and test sets.

    Args:
        X: Feature DataFrame.
        y: Target Series.
        test_size: Fraction of data to use for testing.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (X_train, X_test, y_train, y_test, split_indices_dict).
    """
    @log_operation("split_dataset")
    def _inner():
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Save split indices for traceability
        split_indices = {
            "train_indices": X_train.index.tolist(),
            "test_indices": X_test.index.tolist()
        }

        split_path = Path(CONFIG.data_processed) / "split_indices.json"
        with open(split_path, "w") as f:
            json.dump(split_indices, f, indent=2)

        logger.info(f"Split dataset: {len(X_train)} train, {len(X_test)} test samples")
        logger.info(f"Saved split indices to {split_path}")

        return X_train, X_test, y_train, y_test, split_indices

    return _inner()


def load_split_indices(
    indices_path: str = "data/processed/split_indices.json"
) -> Dict[str, List[int]]:
    """Load previously saved split indices.

    Args:
        indices_path: Path to the split indices JSON file.

    Returns:
        Dictionary with 'train_indices' and 'test_indices' keys.
    """
    @log_operation("load_split_indices")
    def _inner():
        full_path = Path(CONFIG.data_root) / indices_path
        if not full_path.exists():
            raise FileNotFoundError(f"Split indices not found at {full_path}")

        with open(full_path, "r") as f:
            indices = json.load(f)

        logger.info(f"Loaded split indices: {len(indices['train_indices'])} train, {len(indices['test_indices'])} test")
        return indices

    return _inner()


def train_random_forest_with_cv(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_splits: int = 5,
    cv_param_grid: Optional[Dict[str, List[Any]]] = None
) -> Tuple[RandomForestRegressor, Dict[str, Any], Dict[str, float]]:
    """Train Random Forest with cross-validation for hyperparameter tuning.

    Args:
        X_train: Training features.
        y_train: Training targets.
        n_splits: Number of CV folds.
        cv_param_grid: Dictionary of hyperparameters to search.

    Returns:
        Tuple of (best_model, best_params, cv_metrics).
    """
    @log_operation("train_random_forest_with_cv")
    def _inner():
        if cv_param_grid is None:
            cv_param_grid = {
                "n_estimators": [50, 100, 200],
                "max_depth": [5, 10, 15, None],
                "min_samples_split": [2, 5, 10]
            }

        best_score = float("inf")
        best_params = None
        best_model = None
        cv_scores = []

        logger.info(f"Starting {n_splits}-fold cross-validation with {len(cv_param_grid['n_estimators']) * len(cv_param_grid['max_depth']) * len(cv_param_grid['min_samples_split'])} combinations")

        # Grid search over hyperparameters
        for n_est in cv_param_grid["n_estimators"]:
            for max_dep in cv_param_grid["max_depth"]:
                for min_split in cv_param_grid["min_samples_split"]:
                    params = {
                        "n_estimators": n_est,
                        "max_depth": max_dep,
                        "min_samples_split": min_split,
                        "random_state": 42,
                        "n_jobs": -1
                    }

                    model = RandomForestRegressor(**params)

                    # Use negative MAE from cross_val_score (sklearn returns negative for minimization metrics)
                    # We need MAE, so we'll compute it manually or use a custom scorer
                    # For simplicity, we'll use negative mean absolute error
                    from sklearn.metrics import make_scorer, mean_absolute_error
                    mae_scorer = make_scorer(mean_absolute_error, greater_is_better=False)

                    scores = cross_val_score(
                        model, X_train, y_train,
                        cv=n_splits,
                        scoring=mae_scorer,
                        n_jobs=-1
                    )

                    # Convert negative MAE to positive
                    mae_scores = -scores
                    mean_mae = mae_scores.mean()

                    cv_scores.append({
                        "params": params,
                        "mean_mae": mean_mae,
                        "std_mae": mae_scores.std(),
                        "scores": mae_scores.tolist()
                    })

                    if mean_mae < best_score:
                        best_score = mean_mae
                        best_params = params
                        best_model = model

        # Compute confidence interval (95%)
        all_maes = [item["mean_mae"] for item in cv_scores]
        # Actually, we want the CV scores of the best model
        best_cv_entry = next(item for item in cv_scores if item["params"] == best_params)
        cv_mean = best_cv_entry["mean_mae"]
        cv_std = best_cv_entry["std_mae"]
        n = n_splits
        # 95% CI using t-distribution approximation (for small n)
        from scipy import stats
        t_val = stats.t.ppf(0.975, df=n-1)
        ci_margin = t_val * (cv_std / np.sqrt(n))

        cv_metrics = {
            "cv_mae": float(cv_mean),
            "cv_ci_lower": float(cv_mean - ci_margin),
            "cv_ci_upper": float(cv_mean + ci_margin),
            "cv_std": float(cv_std),
            "n_splits": n_splits
        }

        logger.info(f"Best CV MAE: {cv_mean:.4f} (95% CI: [{cv_mean - ci_margin:.4f}, {cv_mean + ci_margin:.4f}])")
        logger.info(f"Best params: {best_params}")

        return best_model, best_params, cv_metrics

    return _inner()


def evaluate_model_on_test(
    model: RandomForestRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, float]:
    """Evaluate model on held-out test set.

    Args:
        model: Trained Random Forest model.
        X_test: Test features.
        y_test: Test targets.

    Returns:
        Dictionary with evaluation metrics.
    """
    @log_operation("evaluate_model_on_test")
    def _inner():
        y_pred = model.predict(X_test)
        test_mae = mean_absolute_error(y_test, y_pred)

        metrics = {
            "test_mae": float(test_mae),
            "n_test_samples": len(y_test)
        }

        logger.info(f"Test set MAE: {test_mae:.4f}")

        return metrics

    return _inner()


def save_model(
    model: RandomForestRegressor,
    model_path: str = "models/rf_model.pkl"
) -> None:
    """Save trained model to disk.

    Args:
        model: Trained Random Forest model.
        model_path: Path to save the model.
    """
    @log_operation("save_model")
    def _inner():
        full_path = Path(CONFIG.models_root) / model_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        dump(model, full_path, compress=3, protocol=3)
        logger.info(f"Model saved to {full_path}")

    return _inner()


def load_model(
    model_path: str = "models/rf_model.pkl"
) -> RandomForestRegressor:
    """Load trained model from disk.

    Args:
        model_path: Path to the saved model.

    Returns:
        Loaded Random Forest model.
    """
    @log_operation("load_model")
    def _inner():
        full_path = Path(CONFIG.models_root) / model_path
        if not full_path.exists():
            raise FileNotFoundError(f"Model not found at {full_path}")

        model = load(full_path)
        logger.info(f"Model loaded from {full_path}")
        return model

    return _inner()


def save_best_hyperparameters(
    best_params: Dict[str, Any],
    cv_metrics: Dict[str, float],
    output_path: str = "results/cv_best_hyperparameters.json"
) -> None:
    """Save best hyperparameters and CV metrics to JSON.

    Args:
        best_params: Dictionary of best hyperparameters found during CV.
        cv_metrics: Dictionary of CV metrics (MAE, CI, etc.).
        output_path: Path to save the hyperparameters file.
    """
    @log_operation("save_best_hyperparameters")
    def _inner():
        full_path = Path(CONFIG.results_root) / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "best_hyperparameters": best_params,
            "cv_metrics": cv_metrics
        }

        with open(full_path, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Best hyperparameters saved to {full_path}")
        logger.info(f"  n_estimators: {best_params.get('n_estimators')}")
        logger.info(f"  max_depth: {best_params.get('max_depth')}")
        logger.info(f"  min_samples_split: {best_params.get('min_samples_split')}")

    return _inner()


def load_best_hyperparameters(
    input_path: str = "results/cv_best_hyperparameters.json"
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """Load best hyperparameters and CV metrics from JSON.

    Args:
        input_path: Path to the hyperparameters file.

    Returns:
        Tuple of (best_params, cv_metrics).
    """
    @log_operation("load_best_hyperparameters")
    def _inner():
        full_path = Path(CONFIG.results_root) / input_path
        if not full_path.exists():
            raise FileNotFoundError(f"Hyperparameters file not found at {full_path}")

        with open(full_path, "r") as f:
            data = json.load(f)

        best_params = data["best_hyperparameters"]
        cv_metrics = data["cv_metrics"]

        logger.info(f"Loaded hyperparameters from {full_path}")
        return best_params, cv_metrics

    return _inner()


def save_model_metrics(
    cv_metrics: Dict[str, float],
    test_metrics: Dict[str, float],
    output_path: str = "results/model_metrics.json"
) -> None:
    """Save combined model metrics to JSON.

    Args:
        cv_metrics: Cross-validation metrics.
        test_metrics: Test set metrics.
        output_path: Path to save the metrics file.
    """
    @log_operation("save_model_metrics")
    def _inner():
        full_path = Path(CONFIG.results_root) / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "cv_mae": cv_metrics.get("cv_mae"),
            "cv_ci_lower": cv_metrics.get("cv_ci_lower"),
            "cv_ci_upper": cv_metrics.get("cv_ci_upper"),
            "test_mae": test_metrics.get("test_mae"),
            "n_test_samples": test_metrics.get("n_test_samples")
        }

        with open(full_path, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Model metrics saved to {full_path}")

    return _inner()


def save_residuals(
    y_true: pd.Series,
    y_pred: pd.Series,
    output_path: str = "results/residuals.json"
) -> None:
    """Save residuals (observed - predicted) to JSON.

    Args:
        y_true: True target values.
        y_pred: Predicted target values.
        output_path: Path to save the residuals file.
    """
    @log_operation("save_residuals")
    def _inner():
        full_path = Path(CONFIG.results_root) / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        residuals = (y_true - y_pred).tolist()
        indices = y_true.index.tolist()

        output_data = {
            "residuals": residuals,
            "indices": indices
        }

        with open(full_path, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Residuals saved to {full_path}")

    return _inner()


def save_methodological_flags(
    cv_mae: float,
    output_path: str = "results/methodological_flags.json"
) -> None:
    """Save methodological flags based on CV MAE threshold.

    Args:
        cv_mae: Cross-validation MAE value.
        output_path: Path to save the flags file.
    """
    @log_operation("save_methodological_flags")
    def _inner():
        full_path = Path(CONFIG.results_root) / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Flag if CV MAE > 0.05 (threshold from spec)
        mae_flag = cv_mae > 0.05

        output_data = {
            "mae_flag": mae_flag,
            "cv_mae": cv_mae
        }

        with open(full_path, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Methodological flags saved to {full_path}")
        logger.info(f"  MAE flag (MAE > 0.05): {mae_flag}")

    return _inner()


def aggregate_model_metrics(
    cv_metrics_path: str = "results/cv_metrics.json",
    test_metrics_path: str = "results/model_metrics.json",
    output_path: str = "results/model_metrics.json"
) -> None:
    """Aggregate model metrics from CV and test evaluation.

    Args:
        cv_metrics_path: Path to CV metrics file.
        test_metrics_path: Path to test metrics file.
        output_path: Path to save the aggregated metrics.
    """
    @log_operation("aggregate_model_metrics")
    def _inner():
        # Read CV metrics
        cv_full_path = Path(CONFIG.results_root) / cv_metrics_path
        with open(cv_full_path, "r") as f:
            cv_data = json.load(f)

        # Read test metrics (already has test_mae)
        test_full_path = Path(CONFIG.results_root) / test_metrics_path
        with open(test_full_path, "r") as f:
            test_data = json.load(f)

        # Combine into single file
        aggregated = {
            "cv_mae": cv_data.get("cv_mae"),
            "cv_ci_lower": cv_data.get("cv_ci_lower"),
            "cv_ci_upper": cv_data.get("cv_ci_upper"),
            "test_mae": test_data.get("test_mae"),
            "n_test_samples": test_data.get("n_test_samples")
        }

        full_output_path = Path(CONFIG.results_root) / output_path
        with open(full_output_path, "w") as f:
            json.dump(aggregated, f, indent=2)

        logger.info(f"Aggregated model metrics saved to {full_output_path}")

    return _inner()


def run_modeling_pipeline(
    parquet_path: str = "data/processed/alloys_clean.parquet",
    model_path: str = "models/rf_model.pkl",
    cv_metrics_path: str = "results/cv_metrics.json",
    hyperparams_path: str = "results/cv_best_hyperparameters.json",
    metrics_path: str = "results/model_metrics.json",
    residuals_path: str = "results/residuals.json",
    flags_path: str = "results/methodological_flags.json"
) -> Dict[str, Any]:
    """Run the complete modeling pipeline.

    Args:
        parquet_path: Path to cleaned data.
        model_path: Path to save/load model.
        cv_metrics_path: Path to save CV metrics.
        hyperparams_path: Path to save best hyperparameters.
        metrics_path: Path to save aggregated metrics.
        residuals_path: Path to save residuals.
        flags_path: Path to save methodological flags.

    Returns:
        Dictionary with pipeline results.
    """
    @log_operation("run_modeling_pipeline")
    def _inner():
        logger.info("Starting modeling pipeline...")

        # Step 1: Load data
        X, y = load_features_and_target(parquet_path)

        # Step 2: Split dataset
        X_train, X_test, y_train, y_test, split_indices = split_dataset(X, y)

        # Step 3: Apply ILR transformation
        X_train_ilr = apply_ilr_transformation(X_train)
        X_test_ilr = apply_ilr_transformation(X_test)

        # Step 4: Train with CV
        best_model, best_params, cv_metrics = train_random_forest_with_cv(
            X_train_ilr, y_train
        )

        # Step 5: Save CV metrics
        cv_full_path = Path(CONFIG.results_root) / cv_metrics_path
        with open(cv_full_path, "w") as f:
            json.dump(cv_metrics, f, indent=2)
        logger.info(f"CV metrics saved to {cv_full_path}")

        # Step 6: Save best hyperparameters
        save_best_hyperparameters(best_params, cv_metrics, hyperparams_path)

        # Step 7: Evaluate on test set
        test_metrics = evaluate_model_on_test(best_model, X_test_ilr, y_test)

        # Step 8: Save model
        save_model(best_model, model_path)

        # Step 9: Save residuals
        y_pred_test = best_model.predict(X_test_ilr)
        save_residuals(y_test, pd.Series(y_pred_test, index=y_test.index), residuals_path)

        # Step 10: Save methodological flags
        save_methodological_flags(cv_metrics["cv_mae"], flags_path)

        # Step 11: Save aggregated metrics
        save_model_metrics(cv_metrics, test_metrics, metrics_path)

        logger.info("Modeling pipeline completed successfully!")

        return {
            "best_params": best_params,
            "cv_metrics": cv_metrics,
            "test_metrics": test_metrics
        }

    return _inner()


def main() -> int:
    """Main entry point for the modeling pipeline."""
    try:
        results = run_modeling_pipeline()
        print(f"Pipeline completed. Best CV MAE: {results['cv_metrics']['cv_mae']:.4f}")
        print(f"Test MAE: {results['test_metrics']['test_mae']:.4f}")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())