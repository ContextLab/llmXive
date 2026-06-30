"""
T026: Verify runtime for nested-CV training.

Ensures that the nested cross-validation training process completes
within 30 minutes on a CPU-only runner.

Uses joblib for parallelization (n_jobs=2) and monitors elapsed time.
Aborts if the limit is exceeded.
"""
import os
import sys
import time
import json
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import RFE
from sklearn.metrics import roc_auc_score
import joblib
from joblib import Parallel, delayed

# Add project root to path if running as script
if 'code' not in sys.path:
    code_dir = Path(__file__).parent
    if code_dir.name == 'code':
        sys.path.insert(0, str(code_dir))
    else:
        sys.path.insert(0, str(code_dir.parent / 'code'))

from utils.logger import get_logger
from utils.io import ensure_dir, save_json
from utils.stats import check_collinearity, filter_low_variance_features
from config import get_config

# Constants
MAX_RUNTIME_SECONDS = 30 * 60  # 30 minutes
RANDOM_SEED = 42
N_JOBS = 2
N_OUTER_FOLDS = 5
N_INNER_FOLDS = 3
N_PERMUTATIONS_ESTIMATE = 10  # Small sample for estimation

logger = get_logger("runtime_verifier")


def estimate_inner_cv_runtime(
    X: np.ndarray,
    y: np.ndarray,
    param_grid: Dict[str, list],
    n_inner_folds: int = 3,
    n_jobs: int = 2
) -> float:
    """
    Estimate runtime for a single inner CV fold on a small subset.
    Used to project total runtime.
    """
    # Use a small subset for estimation if dataset is large
    if X.shape[0] > 50:
        subset_indices = np.random.RandomState(RANDOM_SEED).choice(
            X.shape[0], 50, replace=False
        )
        X_sub = X[subset_indices]
        y_sub = y[subset_indices]
    else:
        X_sub, y_sub = X, y

    start_time = time.time()

    inner_cv = StratifiedKFold(n_splits=n_inner_folds, shuffle=True, random_state=RANDOM_SEED)
    
    # Run one fold manually to estimate
    fold_start = time.time()
    for train_idx, val_idx in list(inner_cv.split(X_sub, y_sub))[:1]:
        X_train, X_val = X_sub[train_idx], X_sub[val_idx]
        y_train, y_val = y_sub[train_idx], y_sub[val_idx]

        # Apply collinearity filter
        if X_train.shape[1] > 1:
            mask = check_collinearity(X_train, threshold=0.95)
            X_train = X_train[:, mask]
            X_val = X_val[:, mask]

        # Variance threshold
        mask_var = filter_low_variance_features(X_train, threshold=0.01)
        X_train = X_train[:, mask_var]
        X_val = X_val[:, mask_var]

        if X_train.shape[1] == 0:
            continue

        # RFE to select <= 20 features
        rf_base = RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED, n_jobs=1)
        rfe = RFE(estimator=rf_base, n_features_to_select=min(20, X_train.shape[1]))
        
        pipe = Pipeline([
            ('scaler', StandardScaler()),
            ('rfe', rfe),
            ('rf', RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1))
        ])

        # Grid search on one fold
        grid = GridSearchCV(
            pipe, param_grid, cv=2, n_jobs=1, scoring='roc_auc'
        )
        grid.fit(X_train, y_train)

    fold_time = time.time() - fold_start
    
    # Extrapolate: total folds * inner folds * outer folds
    # But we only ran 1 inner fold. Total = (num_outer_folds * num_inner_folds)
    # However, we need to account for the fact that we ran a subset.
    # Let's just return the time for one inner fold and let the caller extrapolate.
    return fold_time


def train_nested_cv_with_timing(
    X: np.ndarray,
    y: np.ndarray,
    param_grid: Dict[str, list],
    n_jobs: int = N_JOBS
) -> tuple:
    """
    Train the model using nested CV and return the trained model,
    outer fold scores, and total elapsed time.
    """
    outer_cv = StratifiedKFold(
        n_splits=N_OUTER_FOLDS, shuffle=True, random_state=RANDOM_SEED
    )
    
    start_time = time.time()
    outer_scores = []
    best_models = []
    best_params_list = []

    # We run the outer loop sequentially, but inner loops in parallel
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        logger.info(f"Processing outer fold {fold_idx + 1}/{N_OUTER_FOLDS}")
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Collinearity filter
        if X_train.shape[1] > 1:
            collinearity_mask = check_collinearity(X_train, threshold=0.95)
            X_train = X_train[:, collinearity_mask]
            X_test = X_test[:, collinearity_mask]

        # Variance threshold
        variance_mask = filter_low_variance_features(X_train, threshold=0.01)
        X_train = X_train[:, variance_mask]
        X_test = X_test[:, variance_mask]

        if X_train.shape[1] == 0:
            logger.warning("No features remaining after filtering in fold %d", fold_idx)
            continue

        # Inner CV with GridSearch
        inner_cv = StratifiedKFold(
            n_splits=N_INNER_FOLDS, shuffle=True, random_state=RANDOM_SEED
        )
        
        pipe = Pipeline([
            ('scaler', StandardScaler()),
            ('rfe', RFE(
                estimator=RandomForestClassifier(
                    n_estimators=10, random_state=RANDOM_SEED, n_jobs=1
                ),
                n_features_to_select=min(20, X_train.shape[1])
            )),
            ('rf', RandomForestClassifier(random_state=RANDOM_SEED))
        ])

        grid_search = GridSearchCV(
            pipe,
            param_grid,
            cv=inner_cv,
            n_jobs=n_jobs,  # Parallelize inner CV
            scoring='roc_auc',
            refit=True
        )

        grid_search.fit(X_train, y_train)
        
        # Evaluate on test set
        y_pred_proba = grid_search.predict_proba(X_test)[:, 1]
        try:
            score = roc_auc_score(y_test, y_pred_proba)
            outer_scores.append(score)
        except ValueError:
            logger.warning("Could not compute AUC for fold %d", fold_idx)
            continue

        best_models.append(grid_search.best_estimator_)
        best_params_list.append(grid_search.best_params_)

        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS:
            logger.error("Runtime limit exceeded at fold %d", fold_idx)
            break

    total_time = time.time() - start_time
    return best_models, outer_scores, best_params_list, total_time


def main():
    logger.info("Starting runtime verification for nested-CV training (T026)")
    logger.info(f"Max allowed runtime: {MAX_RUNTIME_SECONDS} seconds ({MAX_RUNTIME_SECONDS//60} minutes)")
    logger.info(f"Parallelization: n_jobs={N_JOBS}")

    # Load data
    data_dir = Path("data/processed")
    if not data_dir.exists():
        logger.error("Data directory not found. Run preprocessing tasks first.")
        sys.exit(1)

    metrics_path = data_dir / "graph_metrics.csv"
    labels_path = data_dir / "eligible_subjects.csv"

    if not metrics_path.exists() or not labels_path.exists():
        logger.error("Required data files not found. Run T019 and T017 first.")
        sys.exit(1)

    import pandas as pd
    metrics_df = pd.read_csv(metrics_path)
    labels_df = pd.read_csv(labels_path)

    # Merge to get features and labels
    # Assuming labels_df has 'subject_id' and 'decline_label'
    # And metrics_df has 'subject_id' and graph metrics
    merged = metrics_df.merge(labels_df[['subject_id', 'decline_label']], on='subject_id', how='inner')
    
    if merged.empty:
        logger.error("No overlapping subjects found between metrics and labels.")
        sys.exit(1)

    # Prepare features (exclude subject_id and labels)
    feature_cols = [c for c in merged.columns if c not in ['subject_id', 'decline_label']]
    X = merged[feature_cols].values
    y = merged['decline_label'].values

    logger.info(f"Dataset shape: {X.shape}, Label distribution: {np.bincount(y.astype(int))}")

    # Define parameter grid
    param_grid = {
        'rf__n_estimators': [50, 100, 200],
        'rf__max_depth': [5, 10, None]
    }

    # Estimate runtime
    logger.info("Estimating runtime with a small sample...")
    try:
        est_time = estimate_inner_cv_runtime(X, y, param_grid, n_inner_folds=N_INNER_FOLDS, n_jobs=N_JOBS)
        # Total folds = outer * inner
        estimated_total = est_time * N_OUTER_FOLDS * N_INNER_FOLDS
        logger.info(f"Estimated single fold time: {est_time:.2f}s")
        logger.info(f"Projected total runtime: {estimated_total:.2f}s ({estimated_total/60:.2f} min)")
        
        if estimated_total > MAX_RUNTIME_SECONDS * 1.5:
            logger.warning("Projected runtime exceeds 150% of limit. Proceeding with caution.")
    except Exception as e:
        logger.warning(f"Runtime estimation failed: {e}. Proceeding with actual run.")

    # Run full nested CV
    logger.info("Starting full nested CV training...")
    try:
        models, scores, params, total_time = train_nested_cv_with_timing(
            X, y, param_grid, n_jobs=N_JOBS
        )
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

    logger.info(f"Training completed in {total_time:.2f} seconds ({total_time/60:.2f} minutes)")

    # Check result
    status = "PASS" if total_time <= MAX_RUNTIME_SECONDS else "FAIL"
    logger.info(f"Runtime Verification: {status}")

    # Save report
    report = {
        "task_id": "T026",
        "status": status,
        "max_runtime_seconds": MAX_RUNTIME_SECONDS,
        "actual_runtime_seconds": total_time,
        "n_jobs": N_JOBS,
        "n_outer_folds": N_OUTER_FOLDS,
        "n_inner_folds": N_INNER_FOLDS,
        "final_params": params[0] if params else None,
        "mean_auc": float(np.mean(scores)) if scores else None,
        "timestamp": datetime.now().isoformat()
    }

    artifacts_dir = Path("data/artifacts")
    ensure_dir(artifacts_dir)
    report_path = artifacts_dir / "runtime_verification.json"
    save_json(report, report_path)
    logger.info(f"Report saved to {report_path}")

    if status == "FAIL":
        logger.error("Runtime limit exceeded. The pipeline is too slow for the 30-minute constraint.")
        sys.exit(1)
    else:
        logger.info("Success: Nested-CV training completed within the 30-minute limit.")
        sys.exit(0)


if __name__ == "__main__":
    main()