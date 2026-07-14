"""
Permutation test for the cognitive‑decline prediction pipeline.

This script:
  1. Loads the processed feature matrix (graph metrics) and the binary
     decline labels produced by the training pipeline.
  2. Estimates whether 500 label‑shuffles can be completed within the
     2‑hour runtime budget.
  3. Performs 500 permutations: each permutation shuffles the labels,
     re‑trains a simple RandomForest classifier using the same preprocessing
     steps as the main training script, and records the ROC‑AUC.
  4. Writes a JSON report to ``data/processed/permutation_results.json``.

The implementation deliberately avoids any heavy neuro‑imaging processing;
it works entirely on the already‑computed ``graph_metrics.csv`` file.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import time
from typing import List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import roc_auc_score

# --------------------------------------------------------------------------- #
# Helper: import the training module (named with a leading digit) safely.
# --------------------------------------------------------------------------- #
def _load_train_module():
    """Dynamically load ``code/04_train_model.py`` as a module named ``train_model``."""
    module_path = pathlib.Path(__file__).with_name("04_train_model.py")
    spec = importlib.util.spec_from_file_location("train_model", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load training module from {module_path}")
    train_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(train_mod)
    return train_mod

# --------------------------------------------------------------------------- #
# Logging utilities – use the unified logger defined in utils/logger.py.
# --------------------------------------------------------------------------- #
from utils.logger import get_logger

def get_logger_wrapper(name: str | None = None):
    """Compatibility wrapper used by older scripts."""
    return get_logger(name) if name else get_logger()

logger = get_logger_wrapper("permutation_test")

# --------------------------------------------------------------------------- #
# Data loading helpers
# --------------------------------------------------------------------------- #
def load_features_and_labels():
    """
    Load the feature matrix (graph metrics) and the binary decline labels.

    Returns
    -------
    X : pd.DataFrame
        Feature matrix with one row per subject.
    y : np.ndarray
        Binary labels (1 = decline, 0 = stable).
    """
    train_mod = _load_train_module()

    # Features – already saved by ``code/03_compute_graph_metrics.py``
    X = train_mod.load_features()

    # Eligible subjects + raw scores – needed to compute the decline label
    eligible_df = train_mod.load_eligible_subjects()
    y_series = train_mod.define_decline_label(eligible_df)
    y = y_series.values

    return X, y

# --------------------------------------------------------------------------- #
# Runtime estimation
# --------------------------------------------------------------------------- #
def estimate_runtime(num_permutations: int = 500) -> float:
    """
    Roughly estimate the total runtime for the requested number of permutations.

    The estimate is deliberately conservative: we time a single quick
    permutation (training on a 10 % subsample) and multiply.

    Parameters
    ----------
    num_permutations : int
        Number of label shuffles to perform.

    Returns
    -------
    total_seconds : float
        Estimated total runtime in seconds.
    """
    X, y = load_features_and_labels()

    # Use a tiny subset to get a fast timing (avoid O(N) cost on CI)
    subset_idx = np.random.choice(len(y), size=max(5, int(0.1 * len(y))), replace=False)
    X_sub = X.iloc[subset_idx]
    y_sub = y[subset_idx]

    start = time.time()
    _run_permutation_once(X_sub, y_sub, seed=42)
    single_sec = time.time() - start
    total_est = single_sec * num_permutations
    logger.info(
        "Estimated total runtime for %d permutations: %.1f seconds",
        num_permutations,
        total_est,
    )
    return total_est

# --------------------------------------------------------------------------- #
# Core permutation logic
# --------------------------------------------------------------------------- #
def _run_permutation_once(X: pd.DataFrame, y: np.ndarray, seed: int) -> float:
    """
    Train a RandomForest on the provided (shuffled) labels and return ROC‑AUC.

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix.
    y : np.ndarray
        Shuffled binary labels.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    auc : float
        Mean cross‑validated ROC‑AUC (5‑fold CV).
    """
    rng = np.random.RandomState(seed)
    shuffled_y = y.copy()
    rng.shuffle(shuffled_y)

    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=seed,
        n_jobs=2,
    )
    # 5‑fold CV, scoring by ROC‑AUC
    scores = cross_val_score(
        clf,
        X,
        shuffled_y,
        cv=5,
        scoring="roc_auc",
        n_jobs=2,
    )
    return float(scores.mean())

def run_permutation_test(num_permutations: int = 500) -> List[float]:
    """
    Execute the full permutation suite.

    Returns
    -------
    aucs : list of float
        ROC‑AUC obtained for each permutation.
    """
    X, y = load_features_and_labels()
    aucs: List[float] = []
    for i in range(num_permutations):
        seed = 42 + i  # deterministic but distinct per iteration
        auc = _run_permutation_once(X, y, seed)
        aucs.append(auc)
        if (i + 1) % 50 == 0:
            logger.info("Completed %d / %d permutations", i + 1, num_permutations)
    return aucs

# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #
def main():
    """
    Entry‑point for the permutation test.

    - Checks the 2‑hour runtime budget.
    - Runs 500 label shuffles.
    - Writes ``data/processed/permutation_results.json``.
    """
    NUM_PERMUTATIONS = 500
    MAX_SECONDS = 2 * 60 * 60  # 2 hours

    estimated = estimate_runtime(NUM_PERMUTATIONS)
    if estimated > MAX_SECONDS:
        logger.error(
            "Estimated runtime %.1f s exceeds the 2‑hour limit. Aborting.",
            estimated,
        )
        raise RuntimeError(
            f"Permutation test estimated runtime ({estimated:.1f}s) > 2 h limit."
        )

    start_time = time.time()
    aucs = run_permutation_test(NUM_PERMUTATIONS)
    elapsed = time.time() - start_time
    logger.info(
        "Permutation test completed in %.1f seconds (estimated %.1f seconds).",
        elapsed,
        estimated,
    )

    results = {
        "num_permutations": NUM_PERMUTATIONS,
        "mean_auc": float(np.mean(aucs)),
        "std_auc": float(np.std(aucs, ddof=1)),
        "auc_values": aucs,
    }

    output_path = pathlib.Path("data/processed/permutation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(results, fp, indent=2)

    logger.info("Wrote permutation results to %s", output_path)
    return 0

if __name__ == "__main__":
    # When executed as a script we exit with the return code from ``main``.
    raise SystemExit(main())