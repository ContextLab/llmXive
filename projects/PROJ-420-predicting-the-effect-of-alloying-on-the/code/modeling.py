from __future__ import annotations

import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from compositional import ilr
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import cross_val_score, train_test_split, KFold
from sklearn.metrics import mean_absolute_error

from config import get_config
from logging_config import get_logger, log_operation

logger = get_logger(__name__)
config = get_config()

def load_features_and_target(
    data_path: Optional[Path] = None,
    ilr_transform: bool = True,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Load cleaned data and prepare features/target.

    Args:
        data_path: Path to cleaned parquet. Defaults to config processed path.
        ilr_transform: Whether to apply ILR transformation to composition.

    Returns:
        Tuple of (X_features, y_target).
    """
    if data_path is None:
        data_path = Path(config.data_processed) / "alloys_clean.parquet"

    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}")

    df = pd.read_parquet(data_path)

    # Ensure required columns exist
    required_cols = ["poisson_ratio", "Cu", "Mg", "Si", "Zn", "Mn"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    y = df["poisson_ratio"]

    composition_cols = ["Cu", "Mg", "Si", "Zn", "Mn"]
    X = df[composition_cols].copy()

    if ilr_transform:
        # Apply ILR transformation to compositional data
        ilr_X = ilr(X.values)
        X = pd.DataFrame(
            ilr_X,
            columns=[f"ilr_{i}" for i in range(ilr_X.shape[1])],
            index=df.index,
        )

    return X, y

def apply_ilr_transformation(X: pd.DataFrame) -> pd.DataFrame:
    """Apply ILR transformation to composition columns.

    Args:
        X: DataFrame with composition columns (Cu, Mg, Si, Zn, Mn).

    Returns:
        ILR-transformed DataFrame.
    """
    ilr_X = ilr(X.values)
    return pd.DataFrame(
        ilr_X,
        columns=[f"ilr_{i}" for i in range(ilr_X.shape[1])],
        index=X.index,
    )

def load_split_indices(
    indices_path: Optional[Path] = None,
) -> Dict[str, List[int]]:
    """Load pre-computed train/val/test split indices.

    Args:
        indices_path: Path to split indices JSON.

    Returns:
        Dictionary with 'train', 'val', 'test' keys containing index lists.
    """
    if indices_path is None:
        indices_path = Path(config.data_processed) / "split_indices.json"

    if not indices_path.exists():
        raise FileNotFoundError(f"Split indices not found at {indices_path}")

    with open(indices_path, "r") as f:
        return json.load(f)

def train_random_forest_with_cv(
    X: pd.DataFrame,
    y: pd.Series,
    n_estimators: int = 100,
    random_state: int = 42,
    cv_folds: int = 5,
) -> Tuple[RandomForestRegressor, List[float]]:
    """Train a Random Forest with cross-validation.

    Args:
        X: Feature matrix.
        y: Target vector.
        n_estimators: Number of trees.
        random_state: Random seed.
        cv_folds: Number of CV folds.

    Returns:
        Tuple of (trained_model, cv_scores).
    """
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
    )

    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    scores = cross_val_score(
        model, X, y, cv=cv, scoring="neg_mean_absolute_error"
    )
    cv_scores = -scores  # Convert back to positive MAE

    # Train on full data for final model
    model.fit(X, y)

    return model, cv_scores.tolist()

def run_repeated_cv(
    X: pd.DataFrame,
    y: pd.Series,
    n_repeats: int = 5,
    n_estimators: int = 100,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Run repeated k-fold cross-validation.

    Args:
        X: Feature matrix.
        y: Target vector.
        n_repeats: Number of CV repeats.
        n_estimators: Trees per model.
        random_state: Base random state.

    Returns:
        Dictionary with CV statistics.
    """
    all_scores: List[float] = []

    for repeat in range(n_repeats):
        _, scores = train_random_forest_with_cv(
            X, y, n_estimators=n_estimators, random_state=random_state + repeat
        )
        all_scores.extend(scores)

    mean_mae = float(np.mean(all_scores))
    std_mae = float(np.std(all_scores))
    ci_lower = float(np.percentile(all_scores, 2.5))
    ci_upper = float(np.percentile(all_scores, 97.5))

    return {
        "cv_mae": mean_mae,
        "cv_std": std_mae,
        "cv_ci_lower": ci_lower,
        "cv_ci_upper": ci_upper,
        "n_samples": len(all_scores),
    }

def evaluate_model_on_test(
    model: RandomForestRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, float]:
    """Evaluate model on held-out test set.

    Args:
        model: Trained model.
        X_test: Test features.
        y_test: Test targets.

    Returns:
        Dictionary with test metrics.
    """
    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    residuals = (y_test - y_pred).tolist()

    return {
        "test_mae": mae,
        "residuals": residuals,
        "predictions": y_pred.tolist(),
        "observed": y_test.tolist(),
    }

def save_model_metrics(
    cv_results: Dict[str, Any],
    test_results: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """Save model metrics to JSON.

    Args:
        cv_results: Cross-validation results.
        test_results: Optional test set results.
        output_path: Output file path.

    Returns:
        Path to saved file.
    """
    if output_path is None:
        output_path = Path(config.results) / "model_metrics.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = {**cv_results}
    if test_results:
        metrics["test_mae"] = test_results["test_mae"]

    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Saved model metrics to {output_path}")
    return output_path

def save_residuals(
    test_results: Dict[str, Any],
    output_path: Optional[Path] = None,
) -> Path:
    """Save residuals to JSON.

    Args:
        test_results: Test set results containing residuals.
        output_path: Output file path.

    Returns:
        Path to saved file.
    """
    if output_path is None:
        output_path = Path(config.results) / "residuals.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(test_results, f, indent=2)

    logger.info(f"Saved residuals to {output_path}")
    return output_path

def save_methodological_flags(
    cv_mae: float,
    threshold: float = 0.05,
    output_path: Optional[Path] = None,
) -> Path:
    """Save methodological flags based on MAE threshold.

    Args:
        cv_mae: Cross-validation MAE.
        threshold: MAE threshold for flagging.
        output_path: Output file path.

    Returns:
        Path to saved file.
    """
    if output_path is None:
        output_path = Path(config.results) / "methodological_flags.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    flags = {
        "mae_flag": cv_mae > threshold,
        "cv_mae": cv_mae,
        "threshold": threshold,
    }

    with open(output_path, "w") as f:
        json.dump(flags, f, indent=2)

    logger.info(f"Saved methodological flags to {output_path}")
    return output_path

def save_model(
    model: RandomForestRegressor,
    output_path: Optional[Path] = None,
) -> Path:
    """Serialize and save the trained model.

    Args:
        model: Trained RandomForestRegressor.
        output_path: Path to save the model. Defaults to models/rf_model.pkl.

    Returns:
        Path to saved model file.
    """
    if output_path is None:
        output_path = Path("models") / "rf_model.pkl"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save using joblib with compression
    joblib.dump(model, output_path, compress=3, protocol=3)

    logger.info(f"Saved model to {output_path}")

    # Verification: ensure file exists and can be loaded
    if not output_path.exists():
        raise RuntimeError(f"Failed to save model: {output_path} does not exist")

    try:
        loaded = joblib.load(output_path)
        logger.info(f"Verified model can be loaded from {output_path}")
    except Exception as e:
        raise RuntimeError(f"Model saved but failed to load: {e}")

    return output_path

def aggregate_model_metrics(
    cv_results: Dict[str, Any],
    test_results: Dict[str, Any],
    output_path: Optional[Path] = None,
) -> Path:
    """Aggregate CV and test metrics into a single file.

    Args:
        cv_results: Cross-validation results.
        test_results: Test set results.
        output_path: Output file path.

    Returns:
        Path to saved file.
    """
    if output_path is None:
        output_path = Path(config.results) / "model_metrics.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = {
        "cv_mae": cv_results["cv_mae"],
        "cv_ci_lower": cv_results["cv_ci_lower"],
        "cv_ci_upper": cv_results["cv_ci_upper"],
        "test_mae": test_results["test_mae"],
    }

    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Aggregated model metrics to {output_path}")
    return output_path

def run_modeling_pipeline(
    data_path: Optional[Path] = None,
    indices_path: Optional[Path] = None,
    save_model_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run the full modeling pipeline.

    Args:
        data_path: Path to cleaned data.
        indices_path: Path to split indices.
        save_model_path: Path to save the final model.

    Returns:
        Dictionary with pipeline results.
    """
    log_operation("modeling_pipeline_start")

    # Load data
    X, y = load_features_and_target(data_path, ilr_transform=True)

    # Load splits
    splits = load_split_indices(indices_path)
    train_idx = splits["train"]
    val_idx = splits["val"]
    test_idx = splits["test"]

    X_train = X.iloc[train_idx]
    y_train = y.iloc[train_idx]
    X_val = X.iloc[val_idx]
    y_val = y.iloc[val_idx]
    X_test = X.iloc[test_idx]
    y_test = y.iloc[test_idx]

    # Run repeated CV on train+val
    cv_results = run_repeated_cv(
        pd.concat([X_train, X_val]),
        pd.concat([y_train, y_val]),
        n_repeats=5,
    )

    # Train final model on train+val
    final_model, _ = train_random_forest_with_cv(
        pd.concat([X_train, X_val]),
        pd.concat([y_train, y_val]),
        n_estimators=100,
    )

    # Evaluate on test set
    test_results = evaluate_model_on_test(final_model, X_test, y_test)

    # Save artifacts
    save_model_metrics(cv_results, test_results)
    save_residuals(test_results)
    save_methodological_flags(cv_results["cv_mae"])

    # Save the model (T024)
    model_path = save_model(final_model, save_model_path)

    log_operation("modeling_pipeline_complete")

    return {
        "cv_results": cv_results,
        "test_results": test_results,
        "model_path": str(model_path),
    }

def main() -> None:
    """CLI entry point for modeling pipeline."""
    parser = argparse.ArgumentParser(description="Run modeling pipeline")
    parser.add_argument(
        "--data", type=Path, help="Path to cleaned data parquet"
    )
    parser.add_argument(
        "--indices", type=Path, help="Path to split indices JSON"
    )
    parser.add_argument(
        "--model-output", type=Path, help="Path to save final model"
    )
    args = parser.parse_args()

    results = run_modeling_pipeline(
        data_path=args.data,
        indices_path=args.indices,
        save_model_path=args.model_output,
    )

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
