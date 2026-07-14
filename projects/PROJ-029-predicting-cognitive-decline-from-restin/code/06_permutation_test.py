"""
Permutation test script for predicting cognitive decline.

This script:
  1. Loads the pre‑computed graph metrics and the eligible subject list.
  2. Defines the decline label (≥ 3 point drop on MMSE/MOCA).
  3. Estimates whether the full 500‑permutation run can finish within the
     2‑hour wall‑clock limit.  If not, it aborts with a clear error.
  4. Performs 500 permutations of the label vector, retrains a simple
     RandomForest classifier for each permutation using a 5‑fold outer
     cross‑validation, and records the ROC‑AUC for every run.
  5. Writes a JSON file ``data/processed/permutation_results.json`` with
     the collected AUC scores.

The implementation deliberately avoids heavy dependencies (e.g. the full
nested‑CV pipeline from ``04_train_model.py``) to keep the runtime within
the allowed budget while still providing a fully reproducible
permutation test.
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score

# ----------------------------------------------------------------------
# Utility logger – a thin wrapper around the project‑wide reproducibility
# logger.  All callers expect a function called ``get_logger_wrapper`` that
# returns an object with ``info``/``debug``/``warning`` methods (no‑op is
# acceptable if the underlying logger does not support them).
# ----------------------------------------------------------------------
from utils.logger import get_logger

def get_logger_wrapper(name: str = "permutation_test") -> object:
    """Return a tolerant logger instance.

    The project logger is deliberately permissive; we simply forward the
    request to ``utils.logger.get_logger`` and return the resulting object.
    """
    return get_logger(name)

# ----------------------------------------------------------------------
# Data loading helpers
# ----------------------------------------------------------------------
from utils.io import ensure_dir, load_csv, save_json

DATA_DIR = Path("data/processed")
GRAPH_METRICS_PATH = DATA_DIR / "graph_metrics.csv"
ELIGIBLE_SUBJECTS_PATH = DATA_DIR / "eligible_subjects.csv"
PERMUTATION_RESULTS_PATH = DATA_DIR / "permutation_results.json"

def load_features_and_labels() -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Load the feature matrix (graph metrics) and the binary decline label.

    Returns
    -------
    X : pd.DataFrame
        Feature matrix where rows correspond to subjects.
    y : np.ndarray
        Binary label array (1 = decline, 0 = stable).
    """
    logger = get_logger_wrapper()
    logger.info("Loading graph metrics from %s", GRAPH_METRICS_PATH)

    if not GRAPH_METRICS_PATH.is_file():
        raise FileNotFoundError(f"Graph metrics file missing: {GRAPH_METRICS_PATH}")

    metrics_df = load_csv(GRAPH_METRICS_PATH)

    logger.info("Loading eligible subjects from %s", ELIGIBLE_SUBJECTS_PATH)
    if not ELIGIBLE_SUBJECTS_PATH.is_file():
        raise FileNotFoundError(f"Eligible subjects file missing: {ELIGIBLE_SUBJECTS_PATH}")

    subjects_df = load_csv(ELIGIBLE_SUBJECTS_PATH)

    # Merge on a common identifier – assume column ``subject_id`` exists in both.
    if "subject_id" not in metrics_df.columns or "subject_id" not in subjects_df.columns:
        raise KeyError("Both CSV files must contain a 'subject_id' column.")

    merged = pd.merge(metrics_df, subjects_df, on="subject_id", how="inner")
    if merged.empty:
        raise ValueError("Merged dataset is empty – check subject IDs.")

    # Define decline label: drop ≥ 3 points between baseline and follow‑up.
    # The eligible_subjects.csv is expected to contain ``mmse_baseline`` and
    # ``mmse_followup`` (or the MOCA equivalents).  We use MMSE if present,
    # otherwise MOCA.
    if {"mmse_baseline", "mmse_followup"}.issubset(merged.columns):
        score_diff = merged["mmse_baseline"] - merged["mmse_followup"]
    elif {"moca_baseline", "moca_followup"}.issubset(merged.columns):
        score_diff = merged["moca_baseline"] - merged["moca_followup"]
    else:
        raise KeyError("Missing MMSE/MOCA columns required to define decline label.")

    y = (score_diff >= 3).astype(int).values
    X = merged.drop(
        columns=[
            "subject_id",
            "mmse_baseline",
            "mmse_followup",
            "moca_baseline",
            "moca_followup",
        ],
        errors="ignore",
    )
    logger.info("Loaded %d subjects with %d features", X.shape[0], X.shape[1])
    return X, y

# ----------------------------------------------------------------------
# Runtime estimation
# ----------------------------------------------------------------------
def estimate_runtime(num_subjects: int, num_permutations: int = 500) -> float:
    """
    Very rough runtime estimator.

    We assume a single permutation (shuffle + 5‑fold CV training of a
    modest RandomForest) takes roughly 0.01 seconds per subject.  This is a
    deliberately conservative estimate; if the projected total exceeds
    2 hours (7200 seconds) we abort early.

    Parameters
    ----------
    num_subjects : int
        Number of subjects in the dataset.
    num_permutations : int, default 500
        Number of label shuffles to perform.

    Returns
    -------
    float
        Estimated total runtime in seconds.
    """
    per_subject_estimate = 0.01  # seconds
    total_seconds = num_subjects * num_permutations * per_subject_estimate
    return total_seconds

# ----------------------------------------------------------------------
# Permutation test core
# ----------------------------------------------------------------------
def run_permutation_test(
    X: pd.DataFrame,
    y: np.ndarray,
    n_permutations: int = 500,
    random_state: int = 42,
) -> List[float]:
    """
    Perform the permutation test.

    For each permutation we randomly shuffle the label vector, train a
    RandomForest classifier using a 5‑fold stratified CV, and record the
    mean ROC‑AUC across folds.

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix.
    y : np.ndarray
        Original label vector.
    n_permutations : int
        Number of label shuffles (default 500).
    random_state : int
        Seed for reproducibility.

    Returns
    -------
    List[float]
        List of mean ROC‑AUC values, one per permutation.
    """
    logger = get_logger_wrapper()
    rng = np.random.RandomState(random_state)
    aucs: List[float] = []

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)

    for perm_idx in range(n_permutations):
        # Shuffle labels while keeping the feature matrix unchanged
        y_permuted = rng.permutation(y)

        # Simple RandomForest – hyper‑parameters are modest to keep runtime low
        clf = RandomForestClassifier(
            n_estimators=100,
            max_depth=None,
            random_state=random_state,
            n_jobs=1,
        )

        # Compute ROC‑AUC for each fold; ``cross_val_score`` returns an array
        # of scores (one per split).  Use ``scoring='roc_auc'``.
        try:
            fold_scores = cross_val_score(
                clf,
                X,
                y_permuted,
                cv=cv,
                scoring="roc_auc",
                n_jobs=1,
            )
            mean_auc = float(np.mean(fold_scores))
        except Exception as e:
            logger.warning(
                "Permutation %d failed during model training/evaluation: %s",
                perm_idx,
                e,
            )
            mean_auc = np.nan

        aucs.append(mean_auc)

        if (perm_idx + 1) % 50 == 0:
            logger.info("Completed %d / %d permutations", perm_idx + 1, n_permutations)

    return aucs

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the full permutation‑test pipeline.

    The function performs the following steps:
      1. Load data.
      2. Estimate runtime and abort if the projected duration exceeds 2 h.
      3. Run the permutation test.
      4. Write the results to ``data/processed/permutation_results.json``.
    """
    logger = get_logger_wrapper()
    start_time = time.time()

    try:
        X, y = load_features_and_labels()
    except Exception as exc:
        logger.error("Failed to load data: %s", exc)
        sys.exit(1)

    num_subjects = X.shape[0]
    est_seconds = estimate_runtime(num_subjects, n_permutations=500)

    logger.info(
        "Estimated total runtime for 500 permutations: %.1f seconds (%.2f hours)",
        est_seconds,
        est_seconds / 3600,
    )

    max_allowed = 2 * 60 * 60  # 2 hours in seconds
    if est_seconds > max_allowed:
        logger.error(
            "Projected runtime (%.2f h) exceeds the 2‑hour limit. Aborting.",
            est_seconds / 3600,
        )
        sys.exit(2)

    # Run the permutations
    aucs = run_permutation_test(X, y, n_permutations=500, random_state=42)

    # Prepare output structure
    results = {
        "num_permutations": 500,
        "estimated_runtime_seconds": est_seconds,
        "actual_runtime_seconds": time.time() - start_time,
        "permutation_aucs": aucs,
    }

    # Ensure the output directory exists
    ensure_dir(DATA_DIR)

    # Write JSON results
    try:
        save_json(PERMUTATION_RESULTS_PATH, results)
        logger.info(
            "Permutation test completed. Results written to %s",
            PERMUTATION_RESULTS_PATH,
        )
    except Exception as exc:
        logger.error("Failed to write permutation results: %s", exc)
        sys.exit(1)

if __name__ == "__main__":
    main()