"""Modeling pipeline for Poisson's ratio prediction.

Implements:
- Data splitting (80/20)
- ILR transformation for compositional data
- Random Forest training with cross-validation
- Test set evaluation
- Model serialization and metrics tracking
"""

from __future__ import annotations

import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from compositional import ilr
from joblib import dump, load
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import cross_val_score, train_test_split, RepeatedKFold
from sklearn.metrics import mean_absolute_error

from config import get_config
from logging_config import get_logger, log_operation

logger = get_logger("modeling")
config = get_config()


def load_features_and_target(
    parquet_path: Optional[str] = None,
    ilr_transform: bool = False,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Load cleaned data and prepare features/target.

    Args:
        parquet_path: Path to cleaned parquet file. Defaults to config path.
        ilr_transform: Whether to apply ILR transformation to compositional features.

    Returns:
        Tuple of (features DataFrame, target Series)
    """
    if parquet_path is None:
        parquet_path = config.data_processed / "alloys_clean.parquet"

    logger.log("load_features_and_target", path=parquet_path, ilr_transform=ilr_transform)

    df = pd.read_parquet(parquet_path)

    # Define compositional elements
    compositional_cols = ["Cu", "Mg", "Si", "Zn", "Mn"]

    # Ensure all compositional columns exist
    missing_cols = [col for col in compositional_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing compositional columns: {missing_cols}")

    # Prepare features
    if ilr_transform:
        # Apply ILR transformation to compositional data
        ilr_features = ilr(df[compositional_cols].values)
        feature_cols = [f"ilr_{i}" for i in range(ilr_features.shape[1])]
        features = pd.DataFrame(ilr_features, columns=feature_cols, index=df.index)
    else:
        features = df[compositional_cols].copy()

    # Target variable
    target = df["poisson_ratio"].copy()

    return features, target


def apply_ilr_transformation(
    features: pd.DataFrame,
    compositional_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Apply ILR transformation to compositional features.

    Args:
        features: DataFrame with compositional columns.
        compositional_cols: List of compositional column names. Defaults to standard elements.

    Returns:
        DataFrame with ILR-transformed features.
    """
    if compositional_cols is None:
        compositional_cols = ["Cu", "Mg", "Si", "Zn", "Mn"]

    logger.log("apply_ilr_transformation", columns=compositional_cols)

    # Ensure all columns exist
    missing_cols = [col for col in compositional_cols if col not in features.columns]
    if missing_cols:
        raise ValueError(f"Missing compositional columns: {missing_cols}")

    # Apply ILR
    ilr_features = ilr(features[compositional_cols].values)
    feature_cols = [f"ilr_{i}" for i in range(ilr_features.shape[1])]

    return pd.DataFrame(ilr_features, columns=feature_cols, index=features.index)


def load_split_indices(
    indices_path: Optional[str] = None,
) -> Dict[str, List[int]]:
    """Load train/test split indices from JSON file.

    Args:
        indices_path: Path to split indices JSON. Defaults to config path.

    Returns:
        Dictionary with 'train_indices' and 'test_indices' lists.
    """
    if indices_path is None:
        indices_path = config.data_processed / "split_indices.json"

    logger.log("load_split_indices", path=indices_path)

    with open(indices_path, "r") as f:
        indices = json.load(f)

    return indices


def save_split_indices(
    train_indices: List[int],
    test_indices: List[int],
    indices_path: Optional[str] = None,
) -> None:
    """Save train/test split indices to JSON file.

    Args:
        train_indices: List of training set indices.
        test_indices: List of test set indices.
        indices_path: Path to save split indices JSON.
    """
    if indices_path is None:
        indices_path = config.data_processed / "split_indices.json"

    logger.log("save_split_indices", path=indices_path, train_count=len(train_indices), test_count=len(test_indices))

    indices = {
        "train_indices": train_indices,
        "test_indices": test_indices,
    }

    with open(indices_path, "w") as f:
        json.dump(indices, f, indent=2)


def split_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
    indices_path: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split data into training and test sets.

    Args:
        df: Input DataFrame.
        test_size: Fraction of data for test set.
        random_state: Random seed for reproducibility.
        indices_path: Path to save split indices.

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    logger.log("split_data", test_size=test_size, random_state=random_state)

    # Get indices
    train_indices, test_indices = train_test_split(
        df.index.tolist(),
        test_size=test_size,
        random_state=random_state,
    )

    # Save indices
    if indices_path:
        save_split_indices(train_indices, test_indices, indices_path)

    # Split data
    X_train = df.loc[train_indices]
    X_test = df.loc[test_indices]

    # Separate target if it's in the dataframe
    if "poisson_ratio" in df.columns:
        y_train = X_train["poisson_ratio"]
        y_test = X_test["poisson_ratio"]
        X_train = X_train.drop(columns=["poisson_ratio"])
        X_test = X_test.drop(columns=["poisson_ratio"])
    else:
        # Assume target is separate or handled elsewhere
        raise ValueError("poisson_ratio column not found in DataFrame")

    return X_train, X_test, y_train, y_test


def train_random_forest_with_cv(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    cv_folds: int = 5,
    cv_repeats: int = 3,
    hyperparameters: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None,
) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """Train Random Forest with cross-validation for hyperparameter tuning.

    Args:
        X_train: Training features.
        y_train: Training target.
        cv_folds: Number of CV folds.
        cv_repeats: Number of CV repeats.
        hyperparameters: Dictionary of hyperparameters to use.
        output_path: Path to save best hyperparameters.

    Returns:
        Tuple of (trained model, best hyperparameters dict)
    """
    logger.log("train_random_forest_with_cv", cv_folds=cv_folds, cv_repeats=cv_repeats)

    # Default hyperparameters
    if hyperparameters is None:
        hyperparameters = {
            "n_estimators": 100,
            "max_depth": None,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "random_state": 42,
        }

    # Define CV strategy
    rkf = RepeatedKFold(n_splits=cv_folds, n_repeats=cv_repeats, random_state=42)

    # Create model
    model = RandomForestRegressor(**hyperparameters)

    # Perform cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=rkf, scoring="neg_mean_absolute_error")
    cv_mae = -cv_scores.mean()
    cv_std = cv_scores.std()

    logger.log("cv_results", cv_mae=cv_mae, cv_std=cv_std, folds=cv_folds, repeats=cv_repeats)

    # Train final model on full training set
    model.fit(X_train, y_train)

    # Save hyperparameters if path provided
    if output_path:
        with open(output_path, "w") as f:
            json.dump(hyperparameters, f, indent=2)

    return model, {"cv_mae": cv_mae, "cv_std": cv_std, "hyperparameters": hyperparameters}


def evaluate_model_on_test(
    model: RandomForestRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    residuals_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate model on held-out test set.

    Args:
        model: Trained model.
        X_test: Test features.
        y_test: Test target.
        residuals_path: Path to save residuals.

    Returns:
        Dictionary with evaluation metrics.
    """
    logger.log("evaluate_model_on_test")

    # Predict
    y_pred = model.predict(X_test)

    # Calculate metrics
    mae = mean_absolute_error(y_test, y_pred)

    # Calculate residuals
    residuals = y_test.values - y_pred

    metrics = {
        "test_mae": mae,
        "test_size": len(y_test),
    }

    # Save residuals if path provided
    if residuals_path:
        residuals_data = {
            "residuals": residuals.tolist(),
            "indices": y_test.index.tolist(),
        }
        with open(residuals_path, "w") as f:
            json.dump(residuals_data, f, indent=2)

    logger.log("test_results", test_mae=mae, test_size=len(y_test))

    return metrics


def save_model(
    model: RandomForestRegressor,
    model_path: Optional[str] = None,
) -> None:
    """Save trained model to disk.

    Args:
        model: Trained model.
        model_path: Path to save model.
    """
    if model_path is None:
        model_path = config.models / "rf_model.pkl"

    logger.log("save_model", path=model_path)

    # Ensure directory exists
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)

    with open(model_path, "wb") as f:
        pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_model(
    model_path: Optional[str] = None,
) -> RandomForestRegressor:
    """Load trained model from disk.

    Args:
        model_path: Path to model file.

    Returns:
        Loaded model.
    """
    if model_path is None:
        model_path = config.models / "rf_model.pkl"

    logger.log("load_model", path=model_path)

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    return model


def save_model_metrics(
    metrics: Dict[str, Any],
    metrics_path: Optional[str] = None,
) -> None:
    """Save model metrics to JSON file.

    Args:
        metrics: Dictionary of metrics.
        metrics_path: Path to save metrics.
    """
    if metrics_path is None:
        metrics_path = config.results / "model_metrics.json"

    logger.log("save_model_metrics", path=metrics_path)

    # Ensure directory exists
    Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)


def save_residuals(
    residuals: np.ndarray,
    indices: List[int],
    residuals_path: Optional[str] = None,
) -> None:
    """Save residuals to JSON file.

    Args:
        residuals: Array of residuals.
        indices: Corresponding indices.
        residuals_path: Path to save residuals.
    """
    if residuals_path is None:
        residuals_path = config.results / "residuals.json"

    logger.log("save_residuals", path=residuals_path, count=len(residuals))

    # Ensure directory exists
    Path(residuals_path).parent.mkdir(parents=True, exist_ok=True)

    data = {
        "residuals": residuals.tolist(),
        "indices": indices,
    }

    with open(residuals_path, "w") as f:
        json.dump(data, f, indent=2)


def save_methodological_flags(
    cv_mae: float,
    threshold: float = 0.05,
    flags_path: Optional[str] = None,
) -> None:
    """Save methodological flags based on CV MAE.

    Args:
        cv_mae: Cross-validation MAE.
        threshold: Threshold for flagging.
        flags_path: Path to save flags.
    """
    if flags_path is None:
        flags_path = config.results / "methodological_flags.json"

    logger.log("save_methodological_flags", path=flags_path, cv_mae=cv_mae, threshold=threshold)

    # Ensure directory exists
    Path(flags_path).parent.mkdir(parents=True, exist_ok=True)

    flags = {
        "mae_flag": cv_mae > threshold,
        "cv_mae": cv_mae,
    }

    with open(flags_path, "w") as f:
        json.dump(flags, f, indent=2)


def aggregate_model_metrics(
    cv_results: Dict[str, Any],
    test_results: Dict[str, Any],
    metrics_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Aggregate CV and test metrics into a single file.

    Args:
        cv_results: Cross-validation results.
        test_results: Test set results.
        metrics_path: Path to save aggregated metrics.

    Returns:
        Dictionary of aggregated metrics.
    """
    if metrics_path is None:
        metrics_path = config.results / "model_metrics.json"

    logger.log("aggregate_model_metrics", path=metrics_path)

    # Ensure directory exists
    Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)

    aggregated = {
        "cv_mae": cv_results.get("cv_mae"),
        "cv_ci_lower": cv_results.get("cv_mae") - 1.96 * cv_results.get("cv_std", 0),
        "cv_ci_upper": cv_results.get("cv_mae") + 1.96 * cv_results.get("cv_std", 0),
        "test_mae": test_results.get("test_mae"),
    }

    with open(metrics_path, "w") as f:
        json.dump(aggregated, f, indent=2)

    return aggregated


def run_modeling_pipeline(
    data_path: Optional[str] = None,
    split_path: Optional[str] = None,
    model_path: Optional[str] = None,
    metrics_path: Optional[str] = None,
    residuals_path: Optional[str] = None,
    flags_path: Optional[str] = None,
    cv_hyperparams_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the complete modeling pipeline.

    Args:
        data_path: Path to cleaned data parquet.
        split_path: Path to save/load split indices.
        model_path: Path to save model.
        metrics_path: Path to save metrics.
        residuals_path: Path to save residuals.
        flags_path: Path to save methodological flags.
        cv_hyperparams_path: Path to save CV hyperparameters.

    Returns:
        Dictionary with pipeline results.
    """
    logger.log("run_modeling_pipeline")

    # Load data
    features, target = load_features_and_target(data_path, ilr_transform=True)

    # Combine for splitting
    df = features.copy()
    df["poisson_ratio"] = target

    # Split data
    X_train, X_test, y_train, y_test = split_data(
        df,
        test_size=0.2,
        random_state=42,
        indices_path=split_path,
    )

    # Train with CV
    model, cv_results = train_random_forest_with_cv(
        X_train,
        y_train,
        output_path=cv_hyperparams_path,
    )

    # Save model
    save_model(model, model_path)

    # Evaluate on test set
    test_results = evaluate_model_on_test(model, X_test, y_test, residuals_path)

    # Save residuals
    if residuals_path:
        residuals = y_test.values - model.predict(X_test)
        save_residuals(residuals, y_test.index.tolist(), residuals_path)

    # Save methodological flags
    if flags_path:
        save_methodological_flags(cv_results["cv_mae"], flags_path=flags_path)

    # Aggregate metrics
    aggregated = aggregate_model_metrics(cv_results, test_results, metrics_path)

    logger.log("pipeline_complete", metrics=aggregated)

    return {
        "model": model,
        "cv_results": cv_results,
        "test_results": test_results,
        "aggregated_metrics": aggregated,
    }


def main() -> None:
    """Main entry point for modeling pipeline."""
    logger.log("main")

    # Parse arguments
    parser = argparse.ArgumentParser(description="Run modeling pipeline")
    parser.add_argument("--data", type=str, help="Path to cleaned data parquet")
    parser.add_argument("--split", type=str, help="Path to save/load split indices")
    parser.add_argument("--model", type=str, help="Path to save model")
    parser.add_argument("--metrics", type=str, help="Path to save metrics")
    parser.add_argument("--residuals", type=str, help="Path to save residuals")
    parser.add_argument("--flags", type=str, help="Path to save methodological flags")
    parser.add_argument("--cv-hyperparams", type=str, help="Path to save CV hyperparameters")

    args = parser.parse_args()

    # Run pipeline
    results = run_modeling_pipeline(
        data_path=args.data,
        split_path=args.split,
        model_path=args.model,
        metrics_path=args.metrics,
        residuals_path=args.residuals,
        flags_path=args.flags,
        cv_hyperparams_path=args.cv_hyperparams,
    )

    print(f"Pipeline completed. Test MAE: {results['test_results']['test_mae']:.4f}")


if __name__ == "__main__":
    main()