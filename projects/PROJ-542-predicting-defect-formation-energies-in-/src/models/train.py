"""
src/models/train.py
-------------------

This module provides the training routine for the defect formation energy
prediction pipeline. It performs 5‑fold GroupKFold cross‑validation on the
supplied training feature matrix and writes the aggregated metrics to a
JSON file.

The original implementation expected command‑line arguments via ``sys.argv``,
which broke programmatic calls from ``src.pipeline.run``.  The module now
exposes a flexible ``main`` function that can be called either with
positional arguments (as a CLI) **or** directly with ``features_path`` and
``output_path`` keyword arguments.  This makes the pipeline entry point
importable and runnable without raising ``TypeError``.
"""

import json
import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.model_selection import GroupKFold

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _compute_fold_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Return RMSE, MAE and R² for a single fold."""
    rmse = mean_squared_error(y_true, y_pred, squared=False)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return {"rmse": rmse, "mae": mae, "r2": r2}


def _aggregate_metrics(per_fold: List[dict]) -> dict:
    """Aggregate per‑fold metrics into mean ± std dictionaries."""
    agg = {}
    for metric in ["rmse", "mae", "r2"]:
        values = [fold[metric] for fold in per_fold]
        agg[f"mean_{metric}"] = float(np.mean(values))
        agg[f"std_{metric}"] = float(np.std(values, ddof=1))
    return agg


# ----------------------------------------------------------------------
# Core training routine
# ----------------------------------------------------------------------
def _train_and_evaluate(
    features_path: Path, output_path: Path
) -> dict:
    """
    Perform 5‑fold GroupKFold CV on ``features_path`` and write the
    aggregated metrics to ``output_path``.  Returns the full metrics
    dictionary (including per‑fold results) for possible downstream use.
    """
    df = pd.read_csv(features_path)

    # Required columns
    if "composition" not in df.columns:
        raise ValueError("Feature matrix must contain a 'composition' column.")
    if "formation_energy" not in df.columns:
        raise ValueError("Feature matrix must contain a 'formation_energy' target column.")

    X = df.drop(columns=["composition", "formation_energy"])
    y = df["formation_energy"].values
    groups = df["composition"].values  # ensure compositions stay together

    gkf = GroupKFold(n_splits=5)
    rf = RandomForestRegressor(
        n_estimators=200, random_state=42, n_jobs=1
    )
    gb = GradientBoostingRegressor(
        n_estimators=200, random_state=42
    )

    results = {}

    for name, model in [("RandomForest", rf), ("GradientBoosting", gb)]:
        per_fold = []
        for train_idx, val_idx in gkf.split(X, y, groups):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            model.fit(X_train, y_train)
            preds = model.predict(X_val)
            per_fold.append(_compute_fold_metrics(y_val, preds))

        results[name] = {
            "per_fold": per_fold,
            "aggregate": _aggregate_metrics(per_fold),
        }

    # Write JSON output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    log.info(f"Cross‑validation metrics written to {output_path}")
    return results


# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------
def main(*args, **kwargs) -> None:
    """
    Entry point used by the pipeline and by the CLI.

    It can be called in two ways:

    1. **CLI style** – ``python -m src.models.train <features.csv> <out.json>``
       In this mode ``args`` will contain the positional arguments from
       ``sys.argv`` (excluding the script name).  ``kwargs`` must be empty.

    2. **Programmatic style** – ``main(features_path=Path(...),
       output_path=Path(...))``.  ``args`` must be empty.

    Any mismatch raises a clear ``RuntimeError`` with usage information.
    """
    if args and kwargs:
        raise RuntimeError(
            "Provide either positional arguments *or* keyword arguments, not both."
        )

    # CLI style
    if args:
        if len(args) != 2:
            raise RuntimeError(
                "Usage: python -m src.models.train <features.csv> <cv_metrics.json>"
            )
        features_path = Path(args[0])
        output_path = Path(args[1])
    else:
        # Programmatic style
        try:
            features_path = kwargs["features_path"]
            output_path = kwargs["output_path"]
        except KeyError as exc:
            raise RuntimeError(
                "Programmatic call requires 'features_path' and 'output_path' keyword arguments."
            ) from exc

    _train_and_evaluate(features_path, output_path)


if __name__ == "__main__":
    # When executed as a script, forward sys.argv[1:] to ``main``.
    main(*sys.argv[1:])
