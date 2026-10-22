"""
src/models/train.py
-------------------

Trains Random Forest and Gradient Boosting regressors on the feature
matrix using 5‑fold GroupKFold cross‑validation.  The implementation
follows the specification for T007.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import compute_checksum

log = get_logger(__name__)

TARGET_COL = "formation_energy"
GROUP_COL = "composition"


def _compute_fold_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return {"rmse": rmse, "mae": mae, "r2": r2}


def _aggregate_metrics(per_fold: list) -> dict:
    """
    Aggregate per‑fold metrics into mean ± std dictionaries.
    """
    agg = {}
    for metric in ["rmse", "mae", "r2"]:
        values = [fold[metric] for fold in per_fold]
        agg[metric] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values, ddof=1)),
        }
    return agg


def _train_and_evaluate(features_path: Path, output_path: Path) -> dict:
    """
    Perform 5‑fold GroupKFold CV on ``features_path`` and write the
    aggregated metrics to ``output_path``.  Returns the full metrics
    dictionary (including per‑fold results) for downstream use.
    """
    df = pd.read_csv(features_path)

    if TARGET_COL not in df.columns or GROUP_COL not in df.columns:
        raise ValueError(f"Feature CSV must contain '{TARGET_COL}' and '{GROUP_COL}' columns.")

    X = df.drop(columns=[TARGET_COL, GROUP_COL])
    y = df[TARGET_COL].values
    groups = df[GROUP_COL].values

    gkf = GroupKFold(n_splits=5)
    per_fold_metrics = []

    # Prepare models.
    models = {
        "RandomForest": RandomForestRegressor(
            n_estimators=200, random_state=42, n_jobs=1
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=200, random_state=42
        ),
    }

    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        for name, model in models.items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics = _compute_fold_metrics(y_test, preds)
            # Record metrics with model identifier.
            per_fold_metrics.append(
                {
                    "model": name,
                    "fold": fold_idx,
                    "rmse": metrics["rmse"],
                    "mae": metrics["mae"],
                    "r2": metrics["r2"],
                }
            )
            log.debug(f"{name} fold {fold_idx}: {metrics}")

    # Aggregate metrics per model.
    aggregated = {}
    for name in models.keys():
        model_folds = [m for m in per_fold_metrics if m["model"] == name]
        aggregated[name] = _aggregate_metrics(model_folds)

    # Write JSON.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=2)

    # Compute checksum for the JSON file.
    checksum_path = paths.data("checksums", "cv_metrics.sha256")
    compute_checksum(output_path, checksum_path)

    return aggregated


def main() -> None:
    """
    CLI entry point: ``python -m src.models.train <features.csv> <out.json>``
    """
    if len(sys.argv) != 3:
        raise RuntimeError("Usage: python -m src.models.train <features.csv> <out.json>")
    features_csv = Path(sys.argv[1])
    out_json = Path(sys.argv[2])
    _train_and_evaluate(features_csv, out_json)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)
