"""
src/models/train.py
-------------------

Implements baseline model training with 5‑fold GroupKFold cross‑validation.
Produces per‑model mean ± std metrics, writes them to ``cv_metrics.json``,
computes a SHA‑256 checksum for the JSON, and serialises the fitted
RandomForest and GradientBoosting models to ``models/rf_cv.pkl`` and
``models/gb_cv.pkl`` respectively.

Execution
----------
``python -m src.models.train <train.csv> <cv_metrics.json>``
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import write_checksum

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _compute_fold_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute RMSE, MAE and R² for a single fold."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return {"rmse": rmse, "mae": mae, "r2": r2}

def _aggregate_metrics(per_fold: list) -> dict:
    """
    Convert a list of per‑fold metric dicts into mean ± std dict.
    Returns a dict with keys ``rmse_mean``, ``rmse_std``, etc.
    """
    rmses = np.array([m["rmse"] for m in per_fold])
    maes = np.array([m["mae"] for m in per_fold])
    r2s = np.array([m["r2"] for m in per_fold])

    return {
        "rmse_mean": float(rmses.mean()),
        "rmse_std": float(rmses.std(ddof=1)),
        "mae_mean": float(maes.mean()),
        "mae_std": float(maes.std(ddof=1)),
        "r2_mean": float(r2s.mean()),
        "r2_std": float(r2s.std(ddof=1)),
    }

def _train_and_evaluate(features_path: Path, output_path: Path) -> dict:
    """
    Perform 5‑fold GroupKFold CV on the training set.

    Parameters
    ----------
    features_path : Path
        CSV containing the training features (must include ``composition``
        column for grouping and ``formation_energy`` target).
    output_path : Path
        Destination for the aggregated CV metrics JSON.

    Returns
    -------
    dict
        Full metrics dictionary (including per‑fold results) – useful for
        downstream callers but not required for the JSON artefact.
    """
    # Load data
    df = pd.read_csv(features_path)
    if "formation_energy" not in df.columns:
        raise ValueError("Target column 'formation_energy' not found in training data.")
    if "composition" not in df.columns:
        raise ValueError("Column 'composition' required for GroupKFold grouping not found.")

    X = df.drop(columns=["formation_energy", "composition"])
    y = df["formation_energy"].values
    groups = df["composition"].values

    gkf = GroupKFold(n_splits=5)
    # Containers for per‑fold metrics
    rf_fold_metrics = []
    gb_fold_metrics = []

    # Iterate over folds
    for fold_idx, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups), start=1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # Random Forest
        rf = RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            n_jobs=1,
        )
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_val)
        rf_fold_metrics.append(_compute_fold_metrics(y_val, rf_pred))

        # Gradient Boosting
        gb = GradientBoostingRegressor(
            n_estimators=200,
            random_state=42,
        )
        gb.fit(X_train, y_train)
        gb_pred = gb.predict(X_val)
        gb_fold_metrics.append(_compute_fold_metrics(y_val, gb_pred))

        log.info(
            f"Fold {fold_idx}: RF RMSE={rf_fold_metrics[-1]['rmse']:.4f}, "
            f"GB RMSE={gb_fold_metrics[-1]['rmse']:.4f}"
        )

    # Aggregate metrics
    aggregated = {
        "RandomForest": _aggregate_metrics(rf_fold_metrics),
        "GradientBoosting": _aggregate_metrics(gb_fold_metrics),
    }

    # Write JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump({"cv_metrics": aggregated}, f, indent=2)

    log.info(f"Cross‑validation metrics written to {output_path}")

    # ------------------------------------------------------------------
    # Fit final models on the entire training set and serialise them.
    # ------------------------------------------------------------------
    final_rf = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=1,
    )
    final_rf.fit(X, y)
    rf_path = Path("models/rf_cv.pkl")
    rf_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_rf, rf_path)
    log.info(f"Random Forest model saved to {rf_path}")

    final_gb = GradientBoostingRegressor(
        n_estimators=200,
        random_state=42,
    )
    final_gb.fit(X, y)
    gb_path = Path("models/gb_cv.pkl")
    gb_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_gb, gb_path)
    log.info(f"Gradient Boosting model saved to {gb_path}")

    # ------------------------------------------------------------------
    # Compute checksum for the JSON metrics file.
    # ------------------------------------------------------------------
    checksum_dir = paths.data("checksums")
    checksum_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists.
    write_checksum(output_path, checksum_dir)

    return {"cv_metrics": aggregated, "rf_path": rf_path, "gb_path": gb_path}

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI wrapper used by ``python -m src.models.train``.

    Expected positional arguments:
    1. Path to the training CSV (produced by ``src.models.split``).
    2. Path where the CV metrics JSON should be written.
    """
    if len(sys.argv) != 3:
        log.error("Exactly two arguments required: <train.csv> <cv_metrics.json>")
        sys.exit(1)

    train_csv = Path(sys.argv[1])
    metrics_json = Path(sys.argv[2])

    if not train_csv.is_file():
        log.error(f"Training file not found: {train_csv}")
        sys.exit(1)

    _train_and_evaluate(train_csv, metrics_json)
    log.info("Training completed successfully.")

if __name__ == "__main__":
    main()