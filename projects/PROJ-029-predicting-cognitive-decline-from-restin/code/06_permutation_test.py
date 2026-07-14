"""
Permutation Test Script (T029)
Runs a permutation test on the trained model, shuffling labels 500 times,
and records ROC‑AUC for each permutation.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from utils.logger import get_logger

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------

DEFAULT_NUM_PERMUTATIONS = 500
RUNTIME_ESTIMATE_PERMUTATION_SEC = 0.5  # empirical estimate per permutation
RUNTIME_LIMIT_SEC = 2 * 60 * 60  # 2 hours

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _get_logger(name: str = "permutation_test"):
    """Return a logger instance for this script."""
    return get_logger(name)


def load_features_and_labels() -> tuple[List[List[float]], List[int]]:
    """
    Load graph‑metric features and binary decline labels.

    Returns
    -------
    X : list of list of float
        Feature matrix.
    y : list of int
        Binary labels (0 = stable, 1 = decline).
    """
    from utils.io import load_csv

    data_dir = Path("data/processed")

    features_path = data_dir / "graph_metrics.csv"
    labels_path = data_dir / "eligible_subjects.csv"

    if not features_path.is_file():
        raise FileNotFoundError(f"Features file not found: {features_path}")
    if not labels_path.is_file():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")

    df_features = pd.read_csv(features_path)
    df_labels = pd.read_csv(labels_path)

    # Basic validation of required columns
    required_feat_cols = {"subject_id"}
    if not required_feat_cols.issubset(df_features.columns):
        raise ValueError(
            f"Features CSV must contain columns: {required_feat_cols}"
        )
    required_label_cols = {"subject_id", "decline"}
    if not required_label_cols.issubset(df_labels.columns):
        raise ValueError(
            f"Labels CSV must contain columns: {required_label_cols}"
        )

    # Merge on subject_id to align features with labels
    merged = pd.merge(
        df_features,
        df_labels[["subject_id", "decline"]],
        on="subject_id",
        how="inner",
    )

    feature_cols = [
        col for col in merged.columns if col not in ("subject_id", "decline")
    ]
    X = merged[feature_cols].values.tolist()
    y = merged["decline"].astype(int).tolist()

    return X, y


def estimate_runtime(num_permutations: int = DEFAULT_NUM_PERMUTATIONS) -> float:
    """
    Rough estimate of total runtime in seconds.

    Parameters
    ----------
    num_permutations : int
        Number of label shuffles to perform.

    Returns
    -------
    float
        Estimated runtime in seconds.
    """
    return num_permutations * RUNTIME_ESTIMATE_PERMUTATION_SEC


def run_permutation_once(
    X: List[List[float]], y: List[int], seed: int
) -> float:
    """
    Train a RandomForest on a single permutation of the labels and return ROC‑AUC.

    Parameters
    ----------
    X : list of list of float
        Feature matrix.
    y : list of int
        Original labels.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    float
        ROC‑AUC score for this permutation.
    """
    rng = np.random.RandomState(seed)
    y_permuted = rng.permutation(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_permuted, test_size=0.2, random_state=seed
    )

    clf = RandomForestClassifier(
        n_estimators=100, random_state=seed, n_jobs=2
    )
    clf.fit(X_train, y_train)
    probas = clf.predict_proba(X_test)[:, 1]
    return float(roc_auc_score(y_test, probas))


def run_permutation_test(
    num_permutations: int = DEFAULT_NUM_PERMUTATIONS, seed: int = 42
) -> dict:
    """
    Execute the full permutation test, storing ROC‑AUC for each run.

    Parameters
    ----------
    num_permutations : int
        Number of permutations to perform (default 500).
    seed : int
        Base random seed (default 42).

    Returns
    -------
    dict
        Summary dictionary containing the permutation results.

    Raises
    ------
    RuntimeError
        If the estimated runtime exceeds the 2‑hour limit.
    """
    logger = _get_logger()

    # Load data
    X, y = load_features_and_labels()

    # Estimate runtime and enforce limit
    est_seconds = estimate_runtime(num_permutations)
    logger.info(
        f"Estimated runtime for {num_permutations} permutations: {est_seconds:.1f}s"
    )
    if est_seconds > RUNTIME_LIMIT_SEC:
        raise RuntimeError(
            f"Estimated runtime {est_seconds/3600:.2f} h exceeds the 2 h limit."
        )

    aucs: List[float] = []
    start_time = time.time()

    for i in range(num_permutations):
        perm_seed = seed + i
        auc = run_permutation_once(X, y, perm_seed)
        aucs.append(auc)
        logger.info(f"Permutation {i+1}/{num_permutations}: ROC‑AUC = {auc:.4f}")

    elapsed = time.time() - start_time
    results = {
        "num_permutations": num_permutations,
        "seed": seed,
        "aucs": aucs,
        "mean_auc": sum(aucs) / len(aucs) if aucs else None,
        "elapsed_seconds": elapsed,
    }

    output_path = Path("data/processed/permutation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(results, f, indent=2)

    logger.info(
        f"Permutation test completed in {elapsed:.2f}s; results saved to {output_path}"
    )
    return results


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> int:
    """Execute the permutation‑test script."""
    logger = _get_logger()
    try:
        run_permutation_test()
        return 0
    except Exception as exc:  # pragma: no cover – defensive
        logger.error(f"Permutation test failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())