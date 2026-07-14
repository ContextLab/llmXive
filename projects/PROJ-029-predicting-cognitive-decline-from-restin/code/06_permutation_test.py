"""Permutation test for cognitive‑decline prediction model.

This script:
1. Loads the processed graph‑metric features and the binary decline label.
2. Estimates the total runtime for 500 label‑shuffles; aborts if > 2 h.
3. Performs 500 permutations:
   - Shuffles the label vector (seed = 42 + perm_index).
   - Trains / evaluates a nested‑CV RandomForest model on the shuffled data.
   - Records the mean ROC‑AUC across outer folds.
4. Writes a JSON file ``data/processed/permutation_results.json`` containing
   the list of AUC scores (one per permutation) and summary statistics.

The implementation is deliberately lightweight yet fully functional on the
real dataset.  It re‑uses the same modelling pipeline as the main training
script (code/04_train_model.py) to ensure comparable hyper‑parameter
selection.
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

# Local utilities
from utils.logger import get_logger, log_operation

# --------------------------------------------------------------------------- #
# Helper / logger wrappers
# --------------------------------------------------------------------------- #

def get_logger_wrapper(name: str = "permutation_test"):
    """Return the shared reproducibility logger."""
    return get_logger(name)


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #

def load_features_and_labels() -> tuple[pd.DataFrame, np.ndarray]:
    """
    Load feature matrix and binary decline label.

    Expected files:
        data/processed/graph_metrics.csv        – contains ``subject_id`` + feature cols
        data/processed/eligible_subjects.csv   – contains ``subject_id`` and ``decline_label``

    Returns
    -------
    X : pd.DataFrame
        Feature matrix (subjects × features) indexed by ``subject_id``.
    y : np.ndarray
        Binary label array (0 = stable, 1 = decline) aligned with ``X``.
    """
    logger = get_logger_wrapper()

    graph_path = Path("data/processed/graph_metrics.csv")
    subjects_path = Path("data/processed/eligible_subjects.csv")

    if not graph_path.is_file():
        logger.error("Missing graph metrics file", path=str(graph_path))
        raise FileNotFoundError(f"Graph metrics not found: {graph_path}")
    if not subjects_path.is_file():
        logger.error("Missing eligible subjects file", path=str(subjects_path))
        raise FileNotFoundError(f"Eligible subjects not found: {subjects_path}")

    graph_df = pd.read_csv(graph_path)
    subjects_df = pd.read_csv(subjects_path)

    # Expect a ``subject_id`` column in both files
    if "subject_id" not in graph_df.columns or "subject_id" not in subjects_df.columns:
        logger.error("subject_id column missing in one of the input files")
        raise KeyError("subject_id column required in both graph_metrics and eligible_subjects")

    merged = pd.merge(graph_df, subjects_df, on="subject_id", how="inner")
    if merged.empty:
        logger.error("No overlapping subject IDs between features and labels")
        raise ValueError("Empty merged dataset after joining features and labels")

    # Assume the decline label column is named ``decline_label``; if not present,
    # fall back to ``label``.
    label_col = "decline_label" if "decline_label" in merged.columns else "label"
    y = merged[label_col].values
    X = merged.drop(columns=["subject_id", label_col])

    logger.info("Loaded features and labels", n_subjects=X.shape[0], n_features=X.shape[1])
    return X, y


# --------------------------------------------------------------------------- #
# Runtime estimation
# --------------------------------------------------------------------------- #

def _single_permutation_runtime(X: pd.DataFrame, y: np.ndarray) -> float:
    """
    Run a **single** permutation (shuffle + nested CV) and return the elapsed
    seconds.  This lightweight benchmark is used by ``estimate_runtime``.
    """
    start = time.time()
    _ = run_permutation_once(X, y, perm_index=0, seed_base=42)
    return time.time() - start


def estimate_runtime(X: pd.DataFrame, y: np.ndarray, n_permutations: int = 500) -> float:
    """
    Estimate total runtime (seconds) for ``n_permutations`` permutations.

    The function measures the time for a single permutation and scales it.
    If the projected runtime exceeds the 2‑hour limit (7200 s), the caller
    should abort.
    """
    logger = get_logger_wrapper()
    logger.info("Estimating runtime for permutation test")
    single_sec = _single_permutation_runtime(X, y)
    total = single_sec * n_permutations
    logger.info(
        "Runtime estimate",
        single_permutation_sec=single_sec,
        n_permutations=n_permutations,
        total_estimated_sec=total,
    )
    return total


# --------------------------------------------------------------------------- #
# Permutation core
# --------------------------------------------------------------------------- #

def run_permutation_once(
    X: pd.DataFrame,
    y: np.ndarray,
    perm_index: int,
    seed_base: int = 42,
) -> float:
    """
    Perform a single permutation:
    * Shuffle ``y`` with a deterministic seed.
    * Execute the same nested‑CV pipeline used for the real model.
    * Return the mean ROC‑AUC across outer folds.
    """
    # Deterministic shuffling for reproducibility
    rng = np.random.RandomState(seed_base + perm_index)
    y_permuted = rng.permutation(y)

    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed_base)
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed_base)

    param_grid = {
        "n_estimators": [50, 100, 200],
        "max_depth": [5, 10, None],
    }

    aucs: List[float] = []
    for train_idx, test_idx in outer_cv.split(X, y_permuted):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y_permuted[train_idx], y_permuted[test_idx]

        rf = RandomForestClassifier(random_state=seed_base, n_jobs=1)
        grid = GridSearchCV(
            estimator=rf,
            param_grid=param_grid,
            cv=inner_cv,
            scoring="roc_auc",
            n_jobs=1,
        )
        grid.fit(X_train, y_train)
        best = grid.best_estimator_

        # Predict probabilities for the positive class
        probas = best.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, probas)
        aucs.append(auc)

    mean_auc = float(np.mean(aucs))
    return mean_auc


def run_permutation_test(
    X: pd.DataFrame,
    y: np.ndarray,
    n_permutations: int = 500,
    seed_base: int = 42,
) -> List[float]:
    """
    Execute the full permutation test and return a list of mean AUCs.
    """
    logger = get_logger_wrapper()
    logger.info("Starting permutation test", n_permutations=n_permutations)

    results: List[float] = []
    for i in range(n_permutations):
        auc = run_permutation_once(X, y, perm_index=i, seed_base=seed_base)
        results.append(auc)
        if (i + 1) % 50 == 0:
            logger.info("Completed permutations", completed=i + 1)
    return results


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main(argv: List[str] | None = None) -> int:
    """
    CLI entry point used by the quick‑start run‑book.

    Returns an exit code (0 = success, non‑zero = error) so that the
    orchestrating script can detect failures.
    """
    logger = get_logger_wrapper()
    try:
        X, y = load_features_and_labels()

        # ------------------------------------------------------------------- #
        # Runtime pre‑flight check
        # ------------------------------------------------------------------- #
        total_estimated = estimate_runtime(X, y, n_permutations=500)
        MAX_SECONDS = 2 * 60 * 60  # 2 hours
        if total_estimated > MAX_SECONDS:
            logger.error(
                "Estimated runtime exceeds limit",
                estimated_sec=total_estimated,
                limit_sec=MAX_SECONDS,
            )
            raise RuntimeError(
                f"Permutation test estimated runtime {total_estimated/3600:.2f} h exceeds the 2 h limit."
            )

        # ------------------------------------------------------------------- #
        # Execute permutations
        # ------------------------------------------------------------------- #
        aucs = run_permutation_test(X, y, n_permutations=500, seed_base=42)

        # ------------------------------------------------------------------- #
        # Write results
        # ------------------------------------------------------------------- #
        output_path = Path("data/processed/permutation_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result_dict = {
            "permutation_aucs": aucs,
            "summary": {
                "mean_auc": float(np.mean(aucs)),
                "std_auc": float(np.std(aucs, ddof=1)),
                "n_permutations": len(aucs),
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2)

        logger.info("Permutation test completed", output=str(output_path))
        return 0
    except Exception as e:
        logger.exception("Permutation test failed", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())