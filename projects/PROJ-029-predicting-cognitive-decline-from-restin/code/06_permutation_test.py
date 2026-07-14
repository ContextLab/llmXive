"""
Permutation test for the cognitive‑decline prediction pipeline.

This script:
1. Loads the processed graph metrics (including the true decline label).
2. Estimates the runtime for 500 permutations; aborts if > 2 h.
3. For each permutation, shuffles the label column, trains a RandomForest
   using the same nested‑CV pipeline as the main model, and records the
   mean ROC‑AUC across outer folds.
4. Writes a JSON file ``data/processed/permutation_results.json`` containing
   the list of AUC scores and summary statistics.

The implementation deliberately avoids any external side‑effects other than
the required JSON output, making it safe to run in CI.
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
from sklearn.model_selection import StratifiedKFold, GridSearchCV

# Local utilities
from utils.logger import get_logger, log_operation

# Constants
PERMUTATIONS = 500
TIME_LIMIT_SECONDS = 2 * 60 * 60  # 2 hours
OUTPUT_PATH = Path("data/processed/permutation_results.json")
GRAPH_METRICS_PATH = Path("data/processed/graph_metrics.csv")


def get_logger_wrapper(name: str = "permutation_test"):
    """Convenient wrapper used by other scripts; returns the shared logger."""
    return get_logger(name)


@log_operation
def load_features_and_labels() -> tuple[pd.DataFrame, pd.Series]:
    """
    Load the graph metrics CSV and separate features from the true label.

    The CSV is expected to contain at least the columns:
    - ``subject_id`` (or ``SubjectID``) – identifier, ignored for modelling
    - ``decline`` – binary label (1 = decline, 0 = stable)
    All remaining columns are treated as numeric features.
    """
    logger = get_logger_wrapper()
    if not GRAPH_METRICS_PATH.is_file():
        logger.error(f"Graph metrics file not found at {GRAPH_METRICS_PATH}")
        raise FileNotFoundError(f"{GRAPH_METRICS_PATH} does not exist")

    df = pd.read_csv(GRAPH_METRICS_PATH)
    logger.info("Loaded graph metrics", rows=df.shape[0], cols=df.shape[1])

    # Identify label column (allow a few common names)
    label_candidates = {"decline", "label", "cognitive_decline"}
    label_col = None
    for cand in label_candidates:
        if cand in df.columns:
            label_col = cand
            break
    if label_col is None:
        raise RuntimeError(
            "Label column not found in graph_metrics.csv. Expected one of "
            f"{label_candidates}"
        )

    # Drop identifier columns
    id_cols = {"subject_id", "SubjectID", "subj_id"}
    feature_df = df.drop(columns=[label_col] + list(id_cols.intersection(df.columns)))
    labels = df[label_col]

    logger.debug("Feature shape", shape=feature_df.shape)
    return feature_df, labels


@log_operation
def _train_and_score(features: pd.DataFrame, labels: pd.Series) -> float:
    """
    Train a RandomForest using the nested‑CV configuration defined in the
    main training script and return the mean ROC‑AUC across the outer folds.

    The hyper‑parameter grid matches the specification:
        n_estimators ∈ {50, 100, 200}
        max_depth ∈ {5, 10, None}
    """
    train_mod = _load_train_module()

    # Outer CV (5‑fold)
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    aucs: List[float] = []

    for train_idx, test_idx in outer_cv.split(features, labels):
        X_train, X_test = features.iloc[train_idx], features.iloc[test_idx]
        y_train, y_test = labels.iloc[train_idx], labels.iloc[test_idx]

        # Inner CV for hyper‑parameter search
        param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [5, 10, None],
        }
        rf = RandomForestClassifier(random_state=42, n_jobs=1)
        inner_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        search = GridSearchCV(
            estimator=rf,
            param_grid=param_grid,
            cv=inner_cv,
            scoring="roc_auc",
            n_jobs=1,
        )
        search.fit(X_train, y_train)

        best_model = search.best_estimator_
        probas = best_model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, probas)
        aucs.append(auc)

    mean_auc = float(np.mean(aucs))
    logger.info("Permutation model trained", mean_auc=mean_auc)
    return mean_auc


@log_operation
def estimate_runtime(sample_features: pd.DataFrame, sample_labels: pd.Series) -> float:
    """
    Perform a single quick training/evaluation run to estimate the time per
    permutation. Multiply by the total number of permutations to obtain an
    overall estimate.
    """
    start = time.time()
    _train_and_score(sample_features, sample_labels)
    elapsed = time.time() - start
    return elapsed * PERMUTATIONS  # total estimated time


@log_operation
def run_permutation_once(
    features: pd.DataFrame, true_labels: pd.Series, rng: np.random.Generator
) -> float:
    """
    Shuffle the labels once and return the mean ROC‑AUC of the model trained
    on the shuffled data.
    """
    shuffled = pd.Series(rng.permutation(true_labels.values), index=true_labels.index)
    return _train_and_score(features, shuffled)


@log_operation
def run_permutation_test() -> dict:
    """
    Execute the full permutation test, respecting the runtime budget.
    Returns a dictionary that will be written to JSON.
    """
    logger = get_logger_wrapper()

    # Load data
    X, y = load_features_and_labels()

    # Estimate total runtime
    est_seconds = estimate_runtime(X, y)
    logger.info("Runtime estimate", estimated_seconds=est_seconds)
    if est_seconds > TIME_LIMIT_SECONDS:
        raise RuntimeError(
            f"Estimated runtime {est_seconds/3600:.2f} h exceeds the 2 h limit."
        )

    # Seeded RNG for reproducibility
    rng = np.random.default_rng(42)

    auc_scores: List[float] = []
    start_total = time.time()

    for i in range(PERMUTATIONS):
        auc = run_permutation_once(X, y, rng)
        auc_scores.append(auc)
        if (i + 1) % 50 == 0:
            logger.info("Permutation progress", completed=i + 1, total=PERMUTATIONS)

    total_time = time.time() - start_total
    result = {
        "permutations": PERMUTATIONS,
        "roc_auc_scores": auc_scores,
        "mean_auc": float(np.mean(auc_scores)),
        "std_auc": float(np.std(auc_scores)),
        "total_runtime_seconds": total_time,
    }
    logger.info("Permutation test completed", result_summary=result)
    return result


@log_operation
def main() -> None:
    """
    Entry point for the script. Ensures the output directory exists,
    runs the permutation test, and writes the JSON artifact.
    """
    logger = get_logger_wrapper()
    try:
        result = run_permutation_test()
    except Exception as exc:
        logger.error("Permutation test failed", error=str(exc))
        raise

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    logger.info("Permutation results written", path=str(OUTPUT_PATH))

    logger.info("Wrote permutation results to %s", output_path)
    return 0

if __name__ == "__main__":
    # When executed directly, run the main routine.
    sys.exit(main())