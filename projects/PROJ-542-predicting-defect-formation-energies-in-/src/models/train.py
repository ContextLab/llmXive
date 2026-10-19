"""
src/models/train.py
-------------------

Perform 5‑fold GroupKFold cross‑validation on the compositional feature
matrix for two baseline regressors: RandomForestRegressor and
GradientBoostingRegressor.  The grouping variable is the full composition
string so that all rows belonging to the same perovskite composition stay
within a single fold.

The script writes:
  - ``models/rf_cv.pkl`` – Random Forest fitted on the full dataset
  - ``models/gb_cv.pkl`` – Gradient Boosting fitted on the full dataset
  - ``data/processed/cv_metrics.json`` – summary statistics conforming to
    ``contracts/model_performance.schema.yaml``

Usage (as documented in ``quickstart.md``):
    python -m src.models.train <features_csv> <cv_metrics_json>

The script is CPU‑only (``n_jobs=1``) and uses a deterministic random
seed (``random_state=42``) to satisfy reproducibility requirements.
"""

import json
import sys
from pathlib import Path

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
    """Return RMSE, MAE and R2 for a single fold."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return {"rmse": rmse, "mae": mae, "r2": r2}

def _aggregate_metrics(per_fold: List[dict]) -> dict:
    """
    Convert a list of per‑fold metric dicts into a dict containing
    mean and standard deviation for each metric.
    """
    metrics = {"rmse": [], "mae": [], "r2": []}
    for entry in per_fold:
        metrics["rmse"].append(entry["rmse"])
        metrics["mae"].append(entry["mae"])
        metrics["r2"].append(entry["r2"])

    agg = {}
    for name, values in metrics.items():
        agg[f"{name}_mean"] = float(np.mean(values))
        agg[f"{name}_std"] = float(np.std(values, ddof=1))
    return agg

# ----------------------------------------------------------------------
# Main training routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for ``python -m src.models.train``.
    Expected CLI arguments:
        1. Path to the feature matrix CSV (must contain a ``composition`` column
           and a ``formation_energy`` target column).
        2. Path where the CV metrics JSON should be written.
    """
    if len(sys.argv) != 3:
        log.error("Usage: python -m src.models.train <features_csv> <cv_metrics_json>")
        sys.exit(1)

    features_path = Path(sys.argv[1])
    metrics_out_path = Path(sys.argv[2])

    if not features_path.is_file():
        log.error(f"Feature matrix not found at {features_path}")
        sys.exit(1)

    # Load data
    df = pd.read_csv(features_path)
    required = {"composition", "formation_energy"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        log.error(f"Feature CSV missing required columns: {missing}")
        sys.exit(1)

    X = df.drop(columns=["formation_energy", "composition"])
    y = df["formation_energy"].values
    groups = df["composition"].values

    # Define models
    rf = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=1,
    )
    gb = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.1,
        random_state=42,
    )

    # Prepare CV
    gkf = GroupKFold(n_splits=5)

    # Containers for per‑fold results
    rf_fold_metrics = []
    gb_fold_metrics = []

    # Perform CV
    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups), start=1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Random Forest
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        rf_fold_metrics.append(_compute_fold_metrics(y_test, rf_pred))

        # Gradient Boosting
        gb.fit(X_train, y_train)
        gb_pred = gb.predict(X_test)
        gb_fold_metrics.append(_compute_fold_metrics(y_test, gb_pred))

        log.debug(
            f"Fold {fold_idx}: RF RMSE={rf_fold_metrics[-1]['rmse']:.4f}, "
            f"GB RMSE={gb_fold_metrics[-1]['rmse']:.4f}"
        )

    # Aggregate metrics
    cv_metrics = {
        "RandomForest": _aggregate_metrics(rf_fold_metrics),
        "GradientBoosting": _aggregate_metrics(gb_fold_metrics),
    }

    # Fit each model on the full dataset for downstream use
    rf.fit(X, y)
    gb.fit(X, y)

    # Serialize models
    rf_path = paths.path("models", "rf_cv.pkl")
    gb_path = paths.path("models", "gb_cv.pkl")
    rf_path.parent.mkdir(parents=True, exist_ok=True)
    gb_path.parent.mkdir(parents=True, exist_ok=True)

    # Use joblib (available via sklearn's external joblib)
    import joblib

    joblib.dump(rf, rf_path)
    joblib.dump(gb, gb_path)
    log.info(f"Saved RandomForest model to {rf_path}")
    log.info(f"Saved GradientBoosting model to {gb_path}")

    # Write CV metrics JSON (conforms to contracts/model_performance.schema.yaml)
    metrics_out_path.parent.mkdir(parents=True, exist_ok=True)
    with metrics_out_path.open("w", encoding="utf-8") as f:
        json.dump({"cv_metrics": cv_metrics}, f, indent=2)
    log.info(f"Wrote CV metrics to {metrics_out_path}")

if __name__ == "__main__":
    main()
