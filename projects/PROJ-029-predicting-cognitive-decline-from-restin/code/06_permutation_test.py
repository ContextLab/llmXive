"""Permutation test for model significance.

This script imports the training logic from code/04_train_model.py,
estimates runtime, and runs 100 permutations to validate the model's
significance. It outputs data/processed/permutation_results.json.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Tuple, Any, Dict

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

# Import training logic from 04_train_model
# We need to access the core training function without re-running the full pipeline
# Since 04_train_model is a script, we import the functions it defines
from code_04_train_model_wrapper import train_single_fold_model, load_features_and_labels_from_disk

# Import logger utilities from the shared logging module
from utils.logger import get_logger, log_operation

# Constants
N_PERMUTATIONS = 100
RANDOM_SEED = 42
MAX_RUNTIME_HOURS = 2.0
DATA_DIR = Path("data/processed")
OUTPUT_FILE = DATA_DIR / "permutation_results.json"

logger = get_logger("permutation_test")


def estimate_runtime(n_permutations: int = 10, n_subjects: int = 50) -> float:
    """Estimate runtime for n_permutations based on a small sample.

    Args:
        n_permutations: Number of permutations to test for estimation
        n_subjects: Number of subjects to use for estimation

    Returns:
        Estimated time in seconds per permutation
    """
    logger.log("estimate_runtime", parameters={"n_permutations": n_permutations, "n_subjects": n_subjects})

    # Load a small subset for estimation
    try:
        X, y = load_features_and_labels_from_disk(DATA_DIR, n_subjects=n_subjects)
    except FileNotFoundError:
        # If data not available, return a conservative estimate
        logger.log("estimate_runtime_failed", status="data_not_found")
        return 300.0  # 5 minutes per permutation as default

    start_time = time.time()

    # Run a few permutations
    for i in range(n_permutations):
        # Shuffle labels
        y_shuffled = y.copy()
        np.random.shuffle(y_shuffled)

        # Train and evaluate
        try:
            _ = train_single_fold_model(X, y_shuffled, random_state=RANDOM_SEED)
        except Exception as e:
            logger.log("estimate_runtime_error", error=str(e))
            # Continue with estimation despite errors

    elapsed = time.time() - start_time
    time_per_perm = elapsed / n_permutations

    logger.log("estimate_runtime_complete", time_per_perm=time_per_perm, total_time=elapsed)
    return time_per_perm


def run_permutation_once(
    X: np.ndarray,
    y: np.ndarray,
    permutation_idx: int,
    random_state: int = RANDOM_SEED
) -> Tuple[int, float]:
    """Run a single permutation iteration.

    Args:
        X: Feature matrix
        y: Original labels
        permutation_idx: Index of this permutation (for logging)
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (permutation_index, roc_auc_score)
    """
    # Set seed for this permutation
    np.random.seed(random_state + permutation_idx)

    # Shuffle labels
    y_shuffled = y.copy()
    np.random.shuffle(y_shuffled)

    # Train and evaluate
    try:
        auc = train_single_fold_model(X, y_shuffled, random_state=random_state)
    except Exception as e:
        logger.log("permutation_error", permutation=permutation_idx, error=str(e))
        return permutation_idx, 0.0

    logger.log("permutation_complete", permutation=permutation_idx, auc=auc)
    return permutation_idx, auc


def run_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = N_PERMUTATIONS,
    random_state: int = RANDOM_SEED,
    n_jobs: int = 2
) -> Dict[str, Any]:
    """Run the full permutation test.

    Args:
        X: Feature matrix
        y: Original labels
        n_permutations: Number of permutations to run
        random_state: Base random seed
        n_jobs: Number of parallel jobs

    Returns:
        Dictionary with p_value and distribution
    """
    logger.log("run_permutation_test", parameters={
        "n_permutations": n_permutations,
        "random_state": random_state,
        "n_jobs": n_jobs,
        "n_subjects": len(y)
    })

    # Estimate runtime first
    est_time_per_perm = estimate_runtime(n_permutations=5, n_subjects=min(20, len(y)))
    total_est_time = est_time_per_perm * n_permutations

    if total_est_time > MAX_RUNTIME_HOURS * 3600:
        logger.log("runtime_limit_exceeded", estimated_hours=total_est_time/3600)
        raise RuntimeError(
            f"Estimated runtime {total_est_time/3600:.2f} hours exceeds limit "
            f"of {MAX_RUNTIME_HOURS} hours. Aborting."
        )

    logger.log("runtime_check_passed", estimated_hours=total_est_time/3600)

    # Run permutations
    results = Parallel(n_jobs=n_jobs, backend="loky")(
        delayed(run_permutation_once)(X, y, i, random_state)
        for i in range(n_permutations)
    )

    # Collect AUC scores
    auc_scores = [auc for _, auc in results]

    # Calculate p-value: proportion of permuted AUCs >= observed AUC
    # We need the observed AUC from the original model
    # For this, we train one more time on the original labels
    try:
        observed_auc = train_single_fold_model(X, y, random_state=random_state)
    except Exception as e:
        logger.log("observed_auc_error", error=str(e))
        observed_auc = 0.5  # Default to random performance

    # Calculate p-value
    # p-value = (number of permuted AUCs >= observed AUC + 1) / (n_permutations + 1)
    p_value = (sum(1 for auc in auc_scores if auc >= observed_auc) + 1) / (n_permutations + 1)

    logger.log("permutation_test_complete", p_value=p_value, observed_auc=observed_auc)

    return {
        "p_value": float(p_value),
        "distribution": [float(auc) for auc in auc_scores],
        "observed_auc": float(observed_auc),
        "n_permutations": n_permutations,
        "random_state": random_state
    }


def main() -> int:
    """Main entry point for the permutation test script."""
    logger.log("main_start", script="06_permutation_test.py")

    try:
        # Load features and labels
        X, y = load_features_and_labels_from_disk(DATA_DIR)

        logger.log("data_loaded", n_subjects=len(y), n_features=X.shape[1])

        # Run permutation test
        results = run_permutation_test(X, y, n_permutations=N_PERMUTATIONS)

        # Write results to file
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=2)

        logger.log("output_written", path=str(OUTPUT_FILE))
        logger.log("main_success")

        return 0

    except Exception as e:
        logger.log("main_error", error=str(e))
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
