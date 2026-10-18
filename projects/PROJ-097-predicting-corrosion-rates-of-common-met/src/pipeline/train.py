"""Training script for the corrosion‑rate prediction pipeline (T004).

Performs a 5‑fold StratifiedGroupKFold split on ``source_id`` while
stratifying on the original composition category, trains a RandomForest
model (max_depth=5, n_estimators=200, random_state=42) on the full
feature set, and a mean‑only baseline.  Results (per‑fold and mean R²
and RMSE) are written to ``data/results/first_run_metrics.json``.
"""

from __future__ import annotations

import json
import logging
import os
import random
from pathlib import Path

import numpy as np
import psutil
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import StratifiedGroupKFold

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
def train_and_evaluate() -> dict:
    """Run CV, train Full model and baseline, return metrics dict."""
    cleaned_path = paths.data("processed", "cleaned_dataset.csv")
    df = pd.read_csv(cleaned_path)

    # Target and groups
    y = df["corrosion_rate"].values
    groups = df["source_id"].values

    # Stratification label – original composition before one‑hot encoding.
    if "composition_original" not in df.columns:
        raise RuntimeError(
            "Column 'composition_original' missing; required for stratified split."
        )
    stratify = df["composition_original"].values

    # Features: all columns except target, source_id, and the helper column.
    X = df.drop(columns=["corrosion_rate", "source_id", "composition_original"])

    # Ensure we stay within RAM limits.
    df = _sample_if_necessary(df)

    # 5‑fold StratifiedGroupKFold
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)

    fold_metrics = []
    for fold_idx, (train_idx, test_idx) in enumerate(
        cv.split(X, y, groups=groups)
    ):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # ------------------------------
        # Baseline: predict training mean
        # ------------------------------
        mean_pred = np.full_like(y_test, fill_value=y_train.mean())
        baseline_rmse = mean_squared_error(y_test, mean_pred, squared=False)
        baseline_r2 = r2_score(y_test, mean_pred)

        # ------------------------------
        # Full RandomForest model
        # ------------------------------
        rf = RandomForestRegressor(
            max_depth=5,
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
        )
        rf.fit(X_train, y_train)
        preds = rf.predict(X_test)

        model_rmse = mean_squared_error(y_test, preds, squared=False)
        model_r2 = r2_score(y_test, preds)

        fold_metrics.append(
            {
                "fold": fold_idx + 1,
                "baseline_rmse": baseline_rmse,
                "baseline_r2": baseline_r2,
                "model_rmse": model_rmse,
                "model_r2": model_r2,
            }
        )
        log.info(
            "Fold %d – Baseline R²=%.4f, RMSE=%.4f | Model R²=%.4f, RMSE=%.4f",
            fold_idx + 1,
            baseline_r2,
            baseline_rmse,
            model_r2,
            model_rmse,
        )

    # Aggregate means
    agg = {
        "baseline_rmse_mean": np.mean([m["baseline_rmse"] for m in fold_metrics]),
        "baseline_r2_mean": np.mean([m["baseline_r2"] for m in fold_metrics]),
        "model_rmse_mean": np.mean([m["model_rmse"] for m in fold_metrics]),
        "model_r2_mean": np.mean([m["model_r2"] for m in fold_metrics]),
        "folds": fold_metrics,
    }
    return agg

def main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m src.pipeline.train``."""
    metrics = train_and_evaluate()
    out_path = paths.results("first_run_metrics.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)
    log.info("First‑run metrics written to %s", out_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
