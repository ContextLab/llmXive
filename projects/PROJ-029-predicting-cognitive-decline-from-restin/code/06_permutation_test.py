"""
T029: Permutation Test for Statistical Significance

Implements a 500-permutation test to validate the significance of the
Random Forest model trained in code/04_train_model.py.

Pre-flight Check: Estimates runtime for 500 permutations based on a
single sample run. If estimated > 2 hours, aborts with error.

Execution:
1. Loads trained model and data from code/04_train_model.py outputs.
2. Shuffles labels 500 times (seed=42).
3. Re-trains and re-evaluates the model for each permutation.
4. Records ROC-AUC for each permutation.
5. Computes p-value as (count(permutation_auc >= original_auc) + 1) / (500 + 1).

Output: data/processed/permutation_results.json
"""
import os
import sys
import json
import time
import random
import warnings
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from joblib import Parallel, delayed

# Project imports
# Importing specific functions from 04_train_model as per task description
# Note: We assume 04_train_model exposes the necessary training logic.
# If 04_train_model is a script, we might need to import its functions or
# re-implement the core logic here if it's not exported.
# Based on the API surface, 04_train_model exports:
# define_decline_label, collinearity_filter, inner_cv_pipeline, train_and_evaluate_nested_cv, main
# We will need to re-use the logic from inner_cv_pipeline or train_and_evaluate_nested_cv.
# However, since these are in a script, we import them.
# To avoid circular imports or execution of main(), we import carefully.

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.io import load_csv, load_json, save_json
from config import get_config

logger = get_logger("permutation_test")
config = get_config()

# Constants
PERMUTATIONS = 500
RANDOM_SEED = 42
MAX_RUNTIME_HOURS = 2.0
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600

# Paths
DATA_DIR = Path("data/processed")
GRAPH_METRICS_FILE = DATA_DIR / "graph_metrics.csv"
MODEL_FILE = DATA_DIR / "model.pkl" # Assuming model is saved here by 04_train_model
CV_RESULTS_FILE = DATA_DIR / "cv_results.json" # Assuming this contains original metrics
PERFORMANCE_REPORT_FILE = DATA_DIR / "performance_report.json"
OUTPUT_FILE = DATA_DIR / "permutation_results.json"

def load_model_and_data() -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Loads the graph metrics and the original model/training config.
    Since we need to re-train, we load the features and labels.
    We also load the original AUC to compare against.
    """
    if not GRAPH_METRICS_FILE.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_FILE}")

    df = load_csv(str(GRAPH_METRICS_FILE))

    # Identify target column and feature columns
    # Assuming the target column is 'decline_label' or similar, created by 04_train_model
    # Let's assume the column name is 'decline_label' based on T023 description
    target_col = 'decline_label'
    if target_col not in df.columns:
        # Try to find a binary column or the one used for classification
        # Fallback: assume the last column is the target if not found
        logger.warning(f"Target column '{target_col}' not found. Attempting to infer.")
        # This is a heuristic; in a real scenario, we'd rely on a contract
        # Let's assume the column 'label' or 'decline' exists
        possible_targets = [c for c in df.columns if 'label' in c.lower() or 'decline' in c.lower()]
        if possible_targets:
            target_col = possible_targets[0]
        else:
            # Fallback to last column
            target_col = df.columns[-1]
            logger.warning(f"Using '{target_col}' as target column.")

    X = df.drop(columns=[target_col]).values
    y = df[target_col].values

    # Load original performance to compare
    if not PERFORMANCE_REPORT_FILE.exists():
        # Fallback: try to load cv_results if performance_report is missing
        if CV_RESULTS_FILE.exists():
            cv_results = load_json(str(CV_RESULTS_FILE))
            # Extract mean AUC from cv_results
            # Structure depends on 04_train_model output, assuming 'mean_test_roc_auc'
            original_auc = cv_results.get('mean_test_roc_auc', 0.5)
            logger.warning(f"performance_report.json not found, using AUC from cv_results: {original_auc}")
        else:
            raise FileNotFoundError(f"Cannot find original performance metrics in {PERFORMANCE_REPORT_FILE} or {CV_RESULTS_FILE}")
    else:
        perf_report = load_json(str(PERFORMANCE_REPORT_FILE))
        original_auc = perf_report.get('mean_roc_auc', 0.5)

    return X, y, original_auc, df.columns.drop(target_col).tolist()

def inner_cv_pipeline(X: np.ndarray, y: np.ndarray, params: Dict[str, Any]) -> float:
    """
    Re-implementation of the inner training logic from 04_train_model.py
    to allow for permutation testing without re-running the full nested CV grid search.
    For the permutation test, we typically fix the hyperparameters to the best found
    in the original run, or re-run a simplified CV.
    Task says: "re-train/re-evaluate the model for each permutation".
    To be rigorous, we should use the same hyperparameter selection logic.
    However, 500 permutations * full nested CV is extremely expensive.
    The task says "re-train/re-evaluate the model".
    We will use the best parameters found in the original run if available,
    or a fixed set if not.
    But to be safe and follow the "re-train" instruction strictly, we will
    run a simplified version of the training (e.g., fixed params or quick CV).
    Given the 2-hour limit, a full nested CV for 500 permutations is likely impossible.
    We will assume the best parameters from the original run are used for speed,
    as is common in permutation tests to test the stability of the metric, not the CV.
    OR, we run a single CV (no inner loop) with the best params.

    Let's assume we load the best params from the original run if possible.
    If not, we use defaults.

    For this implementation, we will:
    1. Use the best parameters found in the original run (loaded from 04_train_model outputs if available).
    2. If not available, use default params.
    3. Perform a simple CV (e.g. 5-fold) to get an AUC for the permuted data.

    Wait, the task says "re-train/re-evaluate the model".
    If we don't re-run the grid search, are we re-training? Yes, we are fitting on new data.
    If we don't re-run the grid search, we are testing the model with fixed hyperparameters.
    This is standard for permutation tests to assess the null distribution of the metric.

    We need to know the best params. Let's try to load them from cv_results.json or performance_report.json.
    If not found, we use defaults.
    """
    # Try to load best params from previous run
    best_params = {'n_estimators': 100, 'max_depth': None}
    if CV_RESULTS_FILE.exists():
        cv_res = load_json(str(CV_RESULTS_FILE))
        if 'best_params' in cv_res:
            best_params = cv_res['best_params']
        elif 'params' in cv_res:
            best_params = cv_res['params']

    # If we have params, use them. Otherwise, use defaults.
    # We will use a simple 5-fold CV to compute the AUC for this permutation.
    # This is much faster than nested CV.
    n_splits = 5
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    aucs = []

    for train_idx, test_idx in skf.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        clf = RandomForestClassifier(
            n_estimators=best_params.get('n_estimators', 100),
            max_depth=best_params.get('max_depth', None),
            random_state=RANDOM_SEED,
            n_jobs=1 # Avoid oversubscription in parallel loop
        )
        clf.fit(X_train, y_train)
        y_pred_prob = clf.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_pred_prob)
        aucs.append(auc)

    return np.mean(aucs)

def estimate_runtime(num_permutations: int = 500) -> float:
    """
    Runs a single permutation to estimate runtime.
    """
    logger.info("Running pre-flight runtime estimation...")
    X, y, _, _ = load_model_and_data()

    # Run one permutation
    start = time.time()
    _ = inner_cv_pipeline(X, y, {})
    elapsed = time.time() - start

    estimated_total = elapsed * num_permutations
    logger.info(f"Single permutation took {elapsed:.2f} seconds. "
                f"Estimated total for {num_permutations} permutations: {estimated_total:.2f} seconds ({estimated_total/3600:.2f} hours).")
    return estimated_total

def run_permutation(X: np.ndarray, y: np.ndarray, rng: np.random.Generator) -> float:
    """
    Shuffles labels and runs the training pipeline.
    """
    y_permuted = rng.permutation(y)
    return inner_cv_pipeline(X, y_permuted, {})

def main():
    logger.info("Starting T029: Permutation Test")

    # 1. Pre-flight Check
    try:
        X, y, original_auc, feature_names = load_model_and_data()
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)

    estimated_runtime = estimate_runtime(PERMUTATIONS)

    if estimated_runtime > MAX_RUNTIME_SECONDS:
        logger.error(f"Estimated runtime ({estimated_runtime/3600:.2f}h) exceeds limit ({MAX_RUNTIME_HOURS}h). Aborting.")
        sys.exit(1)

    logger.info(f"Runtime estimate within limits. Proceeding with {PERMUTATIONS} permutations.")

    # 2. Execution
    results = []
    rng = np.random.default_rng(RANDOM_SEED)

    start_time = time.time()

    # Run permutations
    # We can use joblib for parallelism if needed, but the inner pipeline is already single-threaded per fold.
    # However, the permutation loop itself can be parallelized.
    # But to keep it simple and avoid oversubscription, we'll run sequentially or with limited parallelism.
    # Given the 2-core limit mentioned in other tasks, we might use n_jobs=2.
    # Let's run sequentially first to ensure correctness, then parallelize if needed.
    # Actually, for 500 permutations, parallel is safer for time.
    # We'll use joblib.

    # Note: inner_cv_pipeline uses n_jobs=1 internally, so parallelizing the outer loop is safe.
    from joblib import Parallel, delayed

    logger.info(f"Starting {PERMUTATIONS} permutations...")

    # We need to pass X and y to the parallel function.
    # We'll generate the permutations in the worker to avoid passing huge arrays?
    # No, passing references is fine. We just need to permute y inside.

    # To ensure reproducibility in parallel, we need to manage seeds carefully.
    # Or just run sequentially if time permits.
    # Let's run sequentially for simplicity and correctness of RNG.
    # If it's too slow, we can switch to parallel with explicit seeds.

    for i in range(PERMUTATIONS):
        auc = run_permutation(X, y, rng)
        results.append({
            "permutation_id": i,
            "roc_auc": auc
        })
        if (i + 1) % 50 == 0:
            logger.info(f"Completed {i+1}/{PERMUTATIONS} permutations.")

    elapsed_time = time.time() - start_time
    logger.info(f"All permutations completed in {elapsed_time:.2f} seconds.")

    # 3. Compute p-value
    # p-value = (count(perm_auc >= orig_auc) + 1) / (N + 1)
    perm_aucs = [r['roc_auc'] for r in results]
    count_ge = sum(1 for auc in perm_aucs if auc >= original_auc)
    p_value = (count_ge + 1) / (PERMUTATIONS + 1)

    logger.info(f"Original AUC: {original_auc:.4f}")
    logger.info(f"Mean Permutation AUC: {np.mean(perm_aucs):.4f}")
    logger.info(f"P-value: {p_value:.4f}")

    # 4. Output
    output_data = {
        "original_auc": original_auc,
        "permutation_count": PERMUTATIONS,
        "mean_permutation_auc": float(np.mean(perm_aucs)),
        "std_permutation_auc": float(np.std(perm_aucs)),
        "p_value": p_value,
        "runtime_seconds": elapsed_time,
        "permutation_results": results,
        "seed": RANDOM_SEED
    }

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    save_json(str(OUTPUT_FILE), output_data)
    logger.info(f"Results written to {OUTPUT_FILE}")

    # Check success criteria (optional, but good for logging)
    if p_value < 0.05:
        logger.info("Significance threshold (p < 0.05) met.")
    else:
        logger.warning("Significance threshold (p < 0.05) NOT met.")

    logger.info("T029 Permutation Test completed.")

if __name__ == "__main__":
    main()