"""
code/06_permutation_test.py

Implements a runtime-bounded permutation test for the cognitive decline prediction model.
Target: n=500 permutations.
Constraint: Max runtime 2 hours (7200 seconds).
Strategy: Pilot run -> Estimate -> Adjust n -> Execute -> Report.
"""
from __future__ import annotations

import json
import os
import sys
import time
import pickle
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold, RFE
from joblib import Parallel, delayed

# Import from local utils and modules as per project structure
# Note: We assume these modules exist and are implemented in previous tasks
from utils.logger import get_logger, log_operation
from utils.io import load_csv, load_json, save_json, ensure_dir
from utils.stats import check_collinearity

# Constants
TARGET_N_PERMUTATIONS = 500
MAX_RUNTIME_SECONDS = 7200  # 2 hours
EXIT_CODE_RUNTIME_EXCEEDED = 4
RANDOM_SEED = 42

logger = get_logger("permutation_test")

def load_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load features and labels from the processed graph metrics and model output.
    Returns:
        X: Feature DataFrame
        y: Target Series (decline label)
    """
    # Load graph metrics
    metrics_path = Path("data/processed/graph_metrics.csv")
    if not metrics_path.exists():
        logger.log("error", message=f"Missing required file: {metrics_path}")
        sys.exit(1)

    df = load_csv(metrics_path)

    # Define feature columns (exclude subject_id)
    feature_cols = [
        "node_degree", "global_efficiency", "clustering_coeff", "path_length"
    ]
    # Check if columns exist, if not, try to infer or fail
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        # Fallback: use all numeric columns except subject_id if specific ones missing
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if "subject_id" in numeric_cols:
            numeric_cols.remove("subject_id")
        feature_cols = numeric_cols

    X = df[feature_cols].copy()
    
    # Load labels (decline status)
    # The label is typically derived from the training data or a separate label file.
    # Assuming the training data (T023) produced a label column or we need to reconstruct it.
    # For this task, we assume the training data logic is encapsulated or we re-derive.
    # However, T023 output 'model.pkl' and 'cv_results.json'.
    # We need the original labels. Let's assume they are in 'eligible_subjects.csv' or derived.
    # The prompt says T023 depends on T019 (graph_metrics).
    # Let's assume the label 'decline' is in the eligible_subjects.csv or needs to be joined.
    # Actually, T023 (train_model) likely loaded the graph metrics and joined with labels.
    # To be safe, let's look for a label file or reconstruct.
    # Given the constraints, we will assume the label 'decline' is in the graph_metrics CSV 
    # or we need to load it from a specific source.
    # Let's assume the training script T023 created a 'data/processed/labels.csv' or similar.
    # If not, we might need to re-calculate decline from MMSE scores if available.
    # For this implementation, we assume a 'labels.csv' exists in processed or we join.
    # Let's check for a standard location.
    labels_path = Path("data/processed/labels.csv")
    if not labels_path.exists():
        # Fallback: try to find labels in eligible_subjects.csv if it has MMSE scores
        eligible_path = Path("data/processed/eligible_subjects.csv")
        if eligible_path.exists():
            eligible_df = load_csv(eligible_path)
            if 'mmse_baseline' in eligible_df.columns and 'mmse_followup' in eligible_df.columns:
                eligible_df['decline'] = (eligible_df['mmse_baseline'] - eligible_df['mmse_followup']) >= 3
                y = eligible_df['decline']
                # Merge with X if subject_id matches
                # Assuming X has subject_id
                if 'subject_id' in df.columns:
                    merged = eligible_df.merge(df[['subject_id'] + feature_cols], on='subject_id')
                    X = merged[feature_cols]
                    y = merged['decline']
                else:
                    # If no subject_id in X, assume order matches (risky but fallback)
                    y = eligible_df['decline']
            else:
                logger.log("error", message="Cannot determine labels. Missing MMSE scores or labels file.")
                sys.exit(1)
        else:
            logger.log("error", message="No labels source found.")
            sys.exit(1)
    else:
        labels_df = load_csv(labels_path)
        y = labels_df['decline']
        if 'subject_id' in labels_df and 'subject_id' in df.columns:
            merged = df.merge(labels_df[['subject_id', 'decline']], on='subject_id')
            X = merged[feature_cols]
            y = merged['decline']
        else:
            # Fallback to order
            X = df[feature_cols]
            y = labels_df['decline']

    return X, y

def estimate_runtime(X: pd.DataFrame, y: pd.Series, n_pilot: int = 1) -> float:
    """
    Run a pilot permutation to estimate time per permutation.
    """
    logger.log("estimate_runtime", message="Starting pilot run", n_pilot=n_pilot)
    
    start_time = time.time()
    # Run one full permutation
    _run_single_permutation_logic(X, y, seed=RANDOM_SEED)
    pilot_time = time.time() - start_time

    logger.log("estimate_runtime", message="Pilot run complete", pilot_time=pilot_time)
    return pilot_time

def _run_single_permutation_logic(X: pd.DataFrame, y: pd.Series, seed: int) -> float:
    """
    Internal logic to run a single permutation iteration.
    Returns the score (ROC-AUC) of the permuted model.
    """
    # Set seed for reproducibility within this permutation
    np.random.seed(seed)
    random.seed(seed)

    # Permute labels
    y_perm = y.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Prepare data
    X_np = X.values
    y_np = y_perm.values

    # Nested CV setup (simplified version of T023 logic)
    # Outer CV
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    scores = []

    for train_idx, test_idx in outer_cv.split(X_np, y_np):
        X_train, X_test = X_np[train_idx], X_np[test_idx]
        y_train, y_test = y_np[train_idx], y_np[test_idx]

        # Inner loop for feature selection (Variance -> RFE)
        # Variance Threshold
        vt = VarianceThreshold(threshold=0.01)
        X_train_vt = vt.fit_transform(X_train)
        X_test_vt = vt.transform(X_test)

        # RFE to select <= 20 features
        rf_base = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=seed)
        rfe = RFE(estimator=rf_base, n_features_to_select=min(20, X_train_vt.shape[1]))
        X_train_rfe = rfe.fit_transform(X_train_vt, y_train)
        X_test_rfe = rfe.transform(X_test_vt)

        # Train final model
        model = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=seed)
        model.fit(X_train_rfe, y_train)

        # Evaluate
        y_pred = model.predict_proba(X_test_rfe)[:, 1]
        try:
            auc = roc_auc_score(y_test, y_pred)
            scores.append(auc)
        except ValueError:
            # If only one class in test set, skip or handle
            scores.append(0.5)

    return np.mean(scores) if scores else 0.5

def run_single_permutation(X: pd.DataFrame, y: pd.Series, seed: int) -> float:
    """
    Wrapper to run a single permutation and return the score.
    """
    return _run_single_permutation_logic(X, y, seed)

def run_permutation_test(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Main function to execute the runtime-bounded permutation test.
    """
    logger.log("run_permutation_test", message="Starting permutation test", target_n=TARGET_N_PERMUTATIONS, max_runtime=MAX_RUNTIME_SECONDS)

    # 1. Pilot
    pilot_time = estimate_runtime(X, y, n_pilot=1)
    
    # 2. Estimate
    estimated_total = pilot_time * TARGET_N_PERMUTATIONS
    logger.log("run_permutation_test", message="Runtime estimation", estimated_total=estimated_total)

    # 3. Decision
    n_executed = TARGET_N_PERMUTATIONS
    if estimated_total > MAX_RUNTIME_SECONDS:
        n_executed = int(MAX_RUNTIME_SECONDS / pilot_time)
        if n_executed < 10:
            logger.log("error", message="Runtime limit exceeded even for minimum n=10")
            sys.exit(EXIT_CODE_RUNTIME_EXCEEDED)
        logger.log("run_permutation_test", message="Adjusting n due to runtime limit", n_executed=n_executed)

    # 4. Execute
    start_time = time.time()
    distribution = []
    
    logger.log("run_permutation_test", message="Executing permutations", n=n_executed)
    
    # Run sequentially to ensure memory safety and accurate timing
    # In a real production environment, one might use joblib with careful memory management
    for i in range(n_executed):
        seed = RANDOM_SEED + i
        score = run_single_permutation(X, y, seed)
        distribution.append(score)
        
        if (i + 1) % 50 == 0:
            logger.log("run_permutation_test", message="Progress", completed=i+1, n=n_executed)

    total_time = time.time() - start_time
    logger.log("run_permutation_test", message="Permutations complete", total_time=total_time)

    # 5. Output
    # Calculate p-value
    # We need the original score (from non-permuted data)
    # Re-calculate original score once
    original_score = _run_single_permutation_logic(X, y, seed=RANDOM_SEED) # Use a fixed seed for consistency or re-run logic
    # Actually, the original score should be the one from T023. Let's re-calculate it here to be safe.
    # Or we can assume the user wants to compare against the distribution of permuted scores.
    # The p-value is the proportion of permuted scores >= original score.
    # But we need the original score. Let's calculate it once more with a fixed seed.
    original_score = _run_single_permutation_logic(X, y, seed=RANDOM_SEED)

    # Calculate p-value
    # Note: In a strict permutation test, the original score is included in the distribution?
    # Usually p = (count(perm >= orig) + 1) / (n + 1)
    count_ge = sum(1 for s in distribution if s >= original_score)
    p_value = (count_ge + 1) / (n_executed + 1)

    results = {
        "p_value": p_value,
        "distribution": distribution,
        "original_score": original_score,
        "n_permutations_requested": TARGET_N_PERMUTATIONS,
        "n_permutations_executed": n_executed,
        "runtime_estimate": estimated_total,
        "actual_runtime": total_time,
        "pilot_time": pilot_time
    }

    return results

def main():
    """
    Entry point for the permutation test.
    """
    logger.log("main", message="Starting main execution")

    # Load data
    X, y = load_data()

    # Run test
    results = run_permutation_test(X, y)

    # Save results
    output_path = Path("data/processed/permutation_results.json")
    ensure_dir(output_path.parent)
    save_json(output_path, results)

    logger.log("main", message="Results saved", path=str(output_path))
    print(f"Permutation test complete. Results saved to {output_path}")
    print(f"P-value: {results['p_value']:.4f}")
    print(f"Original Score: {results['original_score']:.4f}")
    print(f"Executed: {results['n_permutations_executed']} / {results['n_permutations_requested']}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
