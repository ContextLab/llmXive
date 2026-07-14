"""Permutation test for the cognitive‑decline prediction pipeline.

This script:
  1. Loads the pre‑computed graph‑metric features and the binary decline label.
  2. Estimates the total runtime for 500 permutations; aborts if > 2 h.
  3. Performs 500 label‑shuffling permutations, each time training a
     nested‑cross‑validated Random Forest and recording the ROC‑AUC.
  4. Writes the results to ``data/processed/permutation_results.json``.

The implementation purposefully avoids any “partial p‑value” calculation –
it simply records the distribution of ROC‑AUC scores.
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold

# --------------------------------------------------------------------------- #
# Helper / logger utilities
# --------------------------------------------------------------------------- #
from utils.logger import get_logger


def get_logger_wrapper(name: str = "permutation_test") -> get_logger:
    """Return a tolerant logger instance for this script."""
    return get_logger(name)


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
from utils.io import load_csv, save_json, ensure_dir


def load_features_and_labels() -> tuple[np.ndarray, np.ndarray]:
    """
    Load feature matrix ``X`` and binary label vector ``y``.

    Expected input file: ``data/processed/graph_metrics.csv``.
    The CSV must contain a column named ``decline`` (binary 0/1) and an
    identifier column (e.g., ``subject_id``). All other columns are treated
    as numeric features.
    """
    metrics_path = Path("data/processed/graph_metrics.csv")
    if not metrics_path.is_file():
        raise FileNotFoundError(f"Required file not found: {metrics_path}")

    df = load_csv(metrics_path)
    required_label = "decline"
    if required_label not in df.columns:
        raise RuntimeError(
            f"Column '{required_label}' not found in {metrics_path}. "
            "The column must contain the binary decline label."
        )

    # Drop non‑feature identifier columns if present
    feature_df = df.drop(columns=[col for col in ["subject_id", required_label] if col in df.columns])
    X = feature_df.to_numpy(dtype=float)
    y = df[required_label].to_numpy(dtype=int)
    return X, y


# --------------------------------------------------------------------------- #
# Runtime estimation
# --------------------------------------------------------------------------- #
def _train_one_permutation(X: np.ndarray, y: np.ndarray, rng: np.random.Generator) -> float:
    """
    Train a nested‑CV Random Forest on a single shuffled label set and
    return the mean ROC‑AUC across outer folds.
    """
    # Shuffle labels
    y_shuffled = rng.permutation(y)

    # Nested CV configuration (mirrors the main training script)
    param_grid = {
        "n_estimators": [50, 100, 200],
        "max_depth": [5, 10, None],
    }
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=rng.integers(0, 2**31 - 1))
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=rng.integers(0, 2**31 - 1))

    aucs: List[float] = []
    for train_idx, test_idx in outer_cv.split(X, y_shuffled):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y_shuffled[train_idx], y_shuffled[test_idx]

        clf = GridSearchCV(
            estimator=RandomForestClassifier(random_state=rng.integers(0, 2**31 - 1)),
            param_grid=param_grid,
            cv=inner_cv,
            scoring="roc_auc",
            n_jobs=2,
        )
        clf.fit(X_train, y_train)

        probas = clf.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, probas)
        aucs.append(auc)

    return float(np.mean(aucs))


def estimate_runtime(X: np.ndarray, y: np.ndarray, n_samples: int = 5) -> float:
    """
    Perform ``n_samples`` quick permutations, time them, and extrapolate the
    total runtime for 500 permutations. Returns the estimated total seconds.
    """
    rng = np.random.default_rng(42)
    timings = []
    for _ in range(n_samples):
        start = time.time()
        _train_one_permutation(X, y, rng)
        timings.append(time.time() - start)
    avg_one = sum(timings) / n_samples
    estimated_total = avg_one * 500
    return estimated_total


# --------------------------------------------------------------------------- #
# Main permutation loop
# --------------------------------------------------------------------------- #
def run_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 500,
    seed: int = 42,
) -> dict:
    """
    Execute the full permutation test.

    Returns a dictionary containing:
        - ``permutations``: number of permutations performed
        - ``auc_scores``: list of ROC‑AUC scores (float)
        - ``mean_auc``: average ROC‑AUC over all permutations
    """
    logger = get_logger_wrapper()
    logger.info("Starting permutation test", permutations=n_permutations)

    rng = np.random.default_rng(seed)
    auc_scores: List[float] = []

    for i in range(1, n_permutations + 1):
        auc = _train_one_permutation(X, y, rng)
        auc_scores.append(auc)
        if i % 50 == 0 or i == n_permutations:
            logger.info("Completed permutation", iteration=i, auc=auc)

    result = {
        "permutations": n_permutations,
        "auc_scores": auc_scores,
        "mean_auc": float(np.mean(auc_scores)),
    }
    logger.info("Permutation test completed", mean_auc=result["mean_auc"])
    return result


# --------------------------------------------------------------------------- #
# Script entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    logger = get_logger_wrapper()
    logger.info("Permutation test script started")

    try:
        X, y = load_features_and_labels()
    except Exception as exc:
        logger.error("Failed to load features/labels", error=str(exc))
        sys.exit(1)

    # ------------------------------------------------------------------- #
    # Pre‑flight runtime check
    # ------------------------------------------------------------------- #
    estimated_seconds = estimate_runtime(X, y)
    max_allowed = 2 * 60 * 60  # 2 hours
    logger.info(
        "Runtime estimation",
        estimated_seconds=estimated_seconds,
        max_allowed_seconds=max_allowed,
    )
    if estimated_seconds > max_allowed:
        logger.error(
            "Estimated runtime exceeds the 2‑hour limit; aborting permutation test."
        )
        sys.exit(2)

    # ------------------------------------------------------------------- #
    # Run permutations
    # ------------------------------------------------------------------- #
    results = run_permutation_test(X, y, n_permutations=500, seed=42)

    # ------------------------------------------------------------------- #
    # Write output
    # ------------------------------------------------------------------- #
    out_path = Path("data/processed/permutation_results.json")
    ensure_dir(out_path)
    save_json(results, out_path, indent=2)
    logger.info("Permutation results written", path=str(out_path))

    logger.info("Permutation test script finished")


if __name__ == "__main__":
    main()