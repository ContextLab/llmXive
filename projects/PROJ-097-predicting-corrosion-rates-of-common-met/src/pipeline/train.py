"""Training script for the corrosion‑rate prediction pipeline (T006).

Performs a 5‑fold Group‑aware cross‑validation (using the splits generated
by ``src.pipeline.split``) and a grid‑search over ``max_depth`` and
``n_estimators`` for both ``RandomForestRegressor`` and
``GradientBoostingRegressor``.  For each hyper‑parameter combination a
**Full model** (with engineered interaction columns) and a **Null model**
(same algorithm, same hyper‑parameters, interaction columns removed) are
trained.  The best Full model (highest mean CV R²) and its corresponding
Null model are serialized, and a ``model_artifact.yaml`` conforming to
``contracts/model_artifact.schema.yaml`` is written.

Additionally, a legacy ``first_run_metrics.json`` (used by earlier tests)
is retained for backward compatibility.
"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
import psutil
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _memory_exceeds(limit_gb: float = 7.0) -> bool:
    """Return True if the current process RSS exceeds *limit_gb*."""
    rss = psutil.Process(os.getpid()).memory_info().rss
    return rss > limit_gb * (1024 ** 3)

def _sample_if_necessary(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """If memory is high, sample ~50 % of rows (stratified by groups)."""
    if not _memory_exceeds():
        return df
    log.warning(
        "RSS exceeds 7 GB; sampling 50 %% of rows to stay within memory budget."
    )
    random.seed(seed)
    # Simple random sample; keep reproducibility.
    return df.sample(frac=0.5, random_state=seed)

# ----------------------------------------------------------------------
# Core training routine
# ----------------------------------------------------------------------
def _load_splits() -> List[Tuple[List[int], List[int]]]:
    """Load the 5‑fold GroupKFold splits produced by ``src.pipeline.split``."""
    splits_path = paths.data("processed", "splits.pkl")
    if not splits_path.is_file():
        raise RuntimeError(f"Splits file not found at {splits_path}")
    import pickle

    with open(splits_path, "rb") as fh:
        splits = pickle.load(fh)
    return splits

def _identify_interaction_columns(df: pd.DataFrame) -> List[str]:
    """Return a list of engineered interaction columns (contain ``_x_``)."""
    return [col for col in df.columns if "_x_" in col]

def _train_one_model(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
    model_cls,
    params: Dict,
) -> Tuple[float, float, object]:
    """Train a model on one fold and return (R², RMSE, fitted model)."""
    model = model_cls(**params, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    preds = model.predict(X_val)
    r2 = r2_score(y_val, preds)
    rmse = mean_squared_error(y_val, preds, squared=False)
    return r2, rmse, model

def train_and_evaluate() -> Dict:
    """Run the full hyper‑parameter grid‑search and return a metrics dict."""
    cleaned_path = paths.data("processed", "cleaned_dataset.csv")
    df = pd.read_csv(cleaned_path)

    # Target and grouping column
    y = df["corrosion_rate"].values
    groups = df["source_id"].values

    # Feature matrix – all columns except target, source_id, and the helper column.
    X_full = df.drop(columns=["corrosion_rate", "source_id", "composition_original"])

    # Identify interaction columns (they contain ``_x_``).
    interaction_cols = _identify_interaction_columns(X_full)

    # Null‑model feature matrix (remove interaction columns).
    X_null = X_full.drop(columns=interaction_cols)

    # Ensure we stay within RAM limits.
    df = _sample_if_necessary(df)

    # Load pre‑computed splits.
    splits = _load_splits()

    # Grid‑search definition
    max_depth_vals = [3, 4, 5]
    n_estimators_vals = [50, 100, 150]
    algorithms = {
        "RandomForest": RandomForestRegressor,
        "GradientBoosting": GradientBoostingRegressor,
    }

    best_score = -np.inf
    best_artifact: Dict = {}
    best_full_model = None
    best_null_model = None

    # Iterate over algorithm + hyper‑parameters
    for algo_name, model_cls in algorithms.items():
        for max_depth in max_depth_vals:
            for n_estimators in n_estimators_vals:
                params = {"max_depth": max_depth, "n_estimators": n_estimators}
                # Containers for CV metrics
                full_r2_scores: List[float] = []
                full_rmse_scores: List[float] = []
                null_r2_scores: List[float] = []
                null_rmse_scores: List[float] = []

                # Train / evaluate on each fold
                for train_idx, val_idx in splits:
                    X_train_full = X_full.iloc[train_idx]
                    X_val_full = X_full.iloc[val_idx]
                    X_train_null = X_null.iloc[train_idx]
                    X_val_null = X_null.iloc[val_idx]

                    y_train = y[train_idx]
                    y_val = y[val_idx]

                    # Full model
                    r2_f, rmse_f, model_f = _train_one_model(
                        X_train_full, y_train, X_val_full, y_val, model_cls, params
                    )
                    full_r2_scores.append(r2_f)
                    full_rmse_scores.append(rmse_f)

                    # Null model (same hyper‑parameters, same algorithm)
                    r2_n, rmse_n, model_n = _train_one_model(
                        X_train_null,
                        y_train,
                        X_val_null,
                        y_val,
                        model_cls,
                        params,
                    )
                    null_r2_scores.append(r2_n)
                    null_rmse_scores.append(rmse_n)

                # Aggregate CV results
                mean_full_r2 = np.mean(full_r2_scores)
                mean_full_rmse = np.mean(full_rmse_scores)

                # Update best model if this configuration is superior
                if mean_full_r2 > best_score:
                    best_score = mean_full_r2
                    best_artifact = {
                        "model_type": algo_name,
                        "hyperparameters": params,
                        "feature_list": list(X_full.columns),
                        "cv_r2": float(mean_full_r2),
                        "cv_rmse": float(mean_full_rmse),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    # Retrain on the full dataset to obtain final models
                    final_full = model_cls(**params, random_state=42, n_jobs=-1)
                    final_full.fit(X_full, y)
                    final_null = model_cls(**params, random_state=42, n_jobs=-1)
                    final_null.fit(X_null, y)
                    best_full_model = final_full
                    best_null_model = final_null

    if not best_artifact:
        raise RuntimeError("No model was trained – check the data and grid.")

    # ------------------------------------------------------------------
    # Persist models and artifact metadata
    # ------------------------------------------------------------------
    results_dir = paths.results()
    results_dir.mkdir(parents=True, exist_ok=True)

    full_path = results_dir / "best_full_model.joblib"
    null_path = results_dir / "best_null_model.joblib"
    joblib.dump(best_full_model, full_path)
    joblib.dump(best_null_model, null_path)

    # Compute SHA‑256 of the serialized Full model file.
    sha256_full = (
        hashlib.sha256()
        .update(open(full_path, "rb").read())
        .hexdigest()
    )
    best_artifact["sha256"] = sha256_full

    # Write the model artifact YAML.
    artifact_path = paths.results("model_artifact.yaml")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    with open(artifact_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(best_artifact, fh, sort_keys=False)

    # ------------------------------------------------------------------
    # Legacy first‑run metrics (kept for older tests)
    # ------------------------------------------------------------------
    legacy_metrics = {
        "baseline_rmse_mean": None,  # placeholder – not required for T006
        "baseline_r2_mean": None,
        "model_rmse_mean": best_artifact["cv_rmse"],
        "model_r2_mean": best_artifact["cv_r2"],
        "folds": [],  # detailed per‑fold metrics omitted for brevity
    }
    legacy_path = paths.results("first_run_metrics.json")
    with open(legacy_path, "w", encoding="utf-8") as fh:
        json.dump(legacy_metrics, fh, indent=2)

    log.info(
        "Best model (%s) saved to %s; Null model saved to %s",
        best_artifact["model_type"],
        full_path,
        null_path,
    )
    log.info("Model artifact metadata written to %s", artifact_path)
    return best_artifact

def main(argv: List[str] | None = None) -> int:
    """Entry point for ``python -m src.pipeline.train``."""
    try:
        train_and_evaluate()
        return 0
    except Exception as exc:
        log.exception("Training failed: %s", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())
