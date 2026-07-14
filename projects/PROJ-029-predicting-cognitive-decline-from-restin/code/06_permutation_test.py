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
def load_features_and_labels() -> tuple[List[List[float]], List[int]]:
    """
    Load graph‑metric features and binary decline labels.

    Returns:
        X: List of feature vectors (list of floats)
        y: List of binary labels (0 = stable, 1 = decline)
    """
    # Load CSV files using the project's I/O utilities.
    from utils.io import load_csv

    # Resolve processed data directory (fallback to default)
    data_dir = Path("data/processed")

    # Expected input files
    features_path = data_dir / "graph_metrics.csv"
    labels_path = data_dir / "eligible_subjects.csv"

    if not features_path.is_file():
        raise FileNotFoundError(f"Features file not found: {features_path}")
    if not labels_path.is_file():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")

    # Load CSVs with pandas for robustness
    df_features = pd.read_csv(features_path)
    df_labels = pd.read_csv(labels_path)

    # Verify required columns exist
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

    # Merge on subject_id to align rows
    merged = pd.merge(
        df_features,
        df_labels[["subject_id", "decline"]],
        on="subject_id",
        how="inner",
    )

    # Feature columns are everything except subject_id and decline
    feature_cols = [
        col for col in merged.columns if col not in ("subject_id", "decline")
    ]
    X = merged[feature_cols].values.tolist()
    y = merged["decline"].astype(int).tolist()

    return X, y


@log_operation
def estimate_runtime(num_permutations: int = 500) -> float:
    """
    Rough estimate of runtime in seconds.
    Assumes ~0.5 s per permutation (empirically observed on modest hardware).
    """
    return num_permutations * 0.5


@log_operation
def run_permutation_once(X: List[List[float]], y: List[int], seed: int) -> float:
    """
    Train a RandomForest on shuffled labels and return ROC‑AUC.

    Args:
        X: Feature matrix.
        y: Original labels.
        seed: Random seed for reproducibility.

    Returns:
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


@log_operation
def run_permutation_test(num_permutations: int = 500, seed: int = 42) -> dict:
    """
    Execute the full permutation test, storing ROC‑AUC for each run.

    Raises:
        RuntimeError: If the estimated runtime exceeds the 2‑hour limit.
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

    # Write results to the declared location
    output_path = Path("data/processed/permutation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(results, f, indent=2)

    logger = get_logger()
    logger.info(
        f"Permutation test completed in {elapsed:.2f}s; results saved to {output_path}"
    )
    return results


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------

@log_operation
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