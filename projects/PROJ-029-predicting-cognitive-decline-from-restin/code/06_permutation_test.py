"""
Permutation Test Script
Implements T029: runs permutation testing on the trained model.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import time
from typing import List

# Added missing import
from pathlib import Path

from utils.logger import get_logger, log_operation


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------

@log_operation
def get_logger_wrapper(name: str = "permutation_test"):
    """Return a logger instance for this script."""
    return get_logger(name)


@log_operation
def load_features_and_labels() -> tuple[list[dict], list[int]]:
    """
    Load features (graph metrics) and binary labels (decline vs. stable).
    Returns a tuple of (features, labels).
    """
    # The actual implementation would load from CSV / JSON.
    # For the purpose of this task we assume the data exists in the
    # processed directory and use the utils.io helpers.
    from utils.io import load_csv, load_json

    config = {}
    # Resolve processed data directory (fallback to default)
    data_dir = Path(config.get("data", {}).get("processed", "data/processed"))

    features_path = data_dir / "graph_metrics.csv"
    labels_path = data_dir / "eligible_subjects.csv"

    # Load feature matrix
    df_features = load_csv(features_path)
    # Load labels (expect a column 'decline' with 0/1)
    df_labels = load_csv(labels_path)

    # Align by subject_id
    merged = df_features.merge(df_labels[["subject_id", "decline"]], on="subject_id")
    feature_cols = [c for c in merged.columns if c not in ("subject_id", "decline")]

    X = merged[feature_cols].values.tolist()
    y = merged["decline"].astype(int).tolist()

    return X, y


@log_operation
def estimate_runtime(num_permutations: int = 500) -> float:
    """
    Very rough estimate: assume each permutation takes ~0.5 s.
    """
    return num_permutations * 0.5


@log_operation
def run_permutation_once(X: List, y: List[int], seed: int) -> float:
    """
    Train a model on shuffled labels and return the ROC‑AUC.
    """
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split

    rng = np.random.RandomState(seed)
    y_permuted = rng.permutation(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_permuted, test_size=0.2, random_state=seed
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=2)
    clf.fit(X_train, y_train)
    probas = clf.predict_proba(X_test)[:, 1]
    return float(roc_auc_score(y_test, probas))


@log_operation
def run_permutation_test(num_permutations: int = 500, seed: int = 42) -> dict:
    """
    Execute the full permutation test, storing ROC‑AUC for each run.
    """
    X, y = load_features_and_labels()

    # Estimate runtime and abort early if too long.
    est = estimate_runtime(num_permutations)
    if est > 2 * 60 * 60:  # 2 hours
        raise RuntimeError(
            f"Estimated runtime {est/3600:.2f} h exceeds the 2 h limit."
        )

    aucs: List[float] = []
    start = time.time()
    for i in range(num_permutations):
        auc = run_permutation_once(X, y, seed + i)
        aucs.append(auc)
    elapsed = time.time() - start

    results = {
        "num_permutations": num_permutations,
        "seed": seed,
        "aucs": aucs,
        "mean_auc": sum(aucs) / len(aucs) if aucs else None,
        "elapsed_seconds": elapsed,
    }

    # Write results
    output_path = Path("data/processed/permutation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger = get_logger()
    logger.info(f"Permutation test completed in {elapsed:.2f}s; results saved to {output_path}")
    return results


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------

@log_operation("run_permutation_test")
def main() -> int:
    """Execute the permutation test script."""
    try:
        run_permutation_test()
        return 0
    except Exception as exc:  # pragma: no cover – defensive
        logger = get_logger()
        logger.error(f"Permutation test failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())