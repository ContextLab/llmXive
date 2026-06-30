"""
code/07_sensitivity_analysis.py

Implements sensitivity analysis for cognitive decline prediction.

Part 1 (T030a): Decision threshold sweep (already implemented).
Part 2 (T030b): Label definition robustness check by re-training models
with varied decline thresholds (±1 point on MMSE/MOCA).
"""
import os
import sys
import json
import time
import argparse
import warnings
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix
import joblib

# Local imports matching API surface
from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from utils.stats import check_collinearity, filter_low_variance_features

# Import training logic from 04_train_model
# We need to replicate the inner CV pipeline logic to allow re-training
# with different labels.

# Constants
RANDOM_SEED = 42
DECLINE_THRESHOLDS = [-2, -3, -4]  # Original is -3, check ±1 point
THRESHOLD_LABELS = {
    -2: "decline_threshold_minus_1",
    -3: "decline_threshold_base",
    -4: "decline_threshold_plus_1"
}
OUTPUT_PATH = Path("data/processed/sensitivity_report.json")
MODEL_PATH = Path("data/processed/model.pkl")
DATA_PATH = Path("data/processed/graph_metrics.csv")
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")

def get_logger_wrapper():
    return get_logger(__name__)

def calculate_fpr_fnr(conf_matrix):
    """
    Calculate False Positive Rate and False Negative Rate from confusion matrix.
    Confusion matrix format: [[TN, FP], [FN, TP]]
    """
    tn, fp, fn, tp = conf_matrix.flatten()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return fpr, fnr

def load_model_and_data():
    """Load the trained model and necessary data."""
    logger = get_logger_wrapper()
    
    if not MODEL_PATH.exists():
        logger.error(f"Model file not found: {MODEL_PATH}. Please run 04_train_model.py first.")
        sys.exit(1)
    
    if not DATA_PATH.exists():
        logger.error(f"Data file not found: {DATA_PATH}. Please run 03_compute_graph_metrics.py first.")
        sys.exit(1)
        
    if not ELIGIBLE_SUBJECTS_PATH.exists():
        logger.error(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}. Please run 01_download_and_filter.py first.")
        sys.exit(1)

    model = joblib.load(MODEL_PATH)
    metrics_df = load_csv(DATA_PATH)
    eligible_df = load_csv(ELIGIBLE_SUBJECTS_PATH)
    
    # Merge to get MMSE/MOCA scores for label calculation
    # Assuming eligible_df has subject_id, mmse_t1, mmse_t2, moca_t1, moca_t2
    # and metrics_df has subject_id and graph features
    merged = pd.merge(metrics_df, eligible_df, on="subject_id", how="inner")
    
    logger.info(f"Loaded model and {len(merged)} subjects for sensitivity analysis.")
    return model, merged

def define_decline_label(df: pd.DataFrame, threshold: int) -> pd.Series:
    """
    Define cognitive decline label based on MMSE/MOCA score drop.
    
    Args:
        df: DataFrame with score columns.
        threshold: Minimum drop required to be considered decline (negative value).
        
    Returns:
        Series of 0/1 labels.
    """
    # Determine which score to use (MMSE preferred, fallback to MOCA)
    if "mmse_t1" in df.columns and "mmse_t2" in df.columns:
        score_diff = df["mmse_t2"] - df["mmse_t1"]
    elif "moca_t1" in df.columns and "moca_t2" in df.columns:
        score_diff = df["moca_t2"] - df["moca_t1"]
    else:
        raise ValueError("No MMSE or MOCA timepoint columns found to calculate decline.")
    
    # Label 1 if drop >= abs(threshold) (e.g., threshold=-3 means drop >= 3)
    # Since threshold is negative (e.g. -3), we check if diff <= threshold
    labels = (score_diff <= threshold).astype(int)
    return labels

def inner_cv_pipeline(X: np.ndarray, y: np.ndarray, param_grid: Dict, n_jobs: int = 2) -> Tuple[Any, Dict]:
    """
    Perform inner CV pipeline with collinearity filter and Random Forest.
    Replicates logic from 04_train_model.py to ensure consistency.
    """
    logger = get_logger_wrapper()
    
    # 1. Collinearity Filter
    # Check correlations and drop one of pair if > 0.95
    if X.shape[1] > 1:
        corr_matrix = np.corrcoef(X, rowvar=False)
        to_drop = set()
        for i in range(corr_matrix.shape[0]):
            for j in range(i + 1, corr_matrix.shape[0]):
                if i not in to_drop and j not in to_drop:
                    if abs(corr_matrix[i, j]) > 0.95:
                        # Drop the one with lower variance
                        var_i = np.var(X[:, i])
                        var_j = np.var(X[:, j])
                        if var_i < var_j:
                            to_drop.add(i)
                        else:
                            to_drop.add(j)
        
        if to_drop:
            logger.info(f"Dropping {len(to_drop)} collinear features.")
            keep_indices = [i for i in range(X.shape[1]) if i not in to_drop]
            X = X[:, keep_indices]
    
    # 2. Variance Thresholding
    # Filter features with variance < 0.01
    variances = np.var(X, axis=0)
    var_keep = variances > 0.01
    if not np.all(var_keep):
        logger.info(f"Dropping {np.sum(~var_keep)} low-variance features.")
        X = X[:, var_keep]
    
    if X.shape[1] == 0:
        raise ValueError("All features were filtered out by collinearity or variance threshold.")

    # 3. RFE to select <= 20 features
    # We'll use a simple RF estimator for RFE
    rf_base = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, max_depth=None)
    from sklearn.feature_selection import RFE
    n_features_to_select = min(20, X.shape[1])
    rfe = RFE(estimator=rf_base, n_features_to_select=n_features_to_select)
    
    # 4. Grid Search with Nested CV structure (Inner loop)
    # Since we are inside the inner loop of the original design, we just do GridSearchCV here
    # The outer loop is handled by the caller (run_sensitivity_analysis)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    grid = GridSearchCV(
        estimator=rfe, # Pipeline: RFE + RF
        param_grid=param_grid,
        cv=skf,
        scoring='roc_auc',
        n_jobs=n_jobs,
        refit=True
    )
    
    # Note: The RFE needs to be part of a pipeline to work with GridSearchCV properly
    # But here we are just fitting the GridSearch on the filtered X
    # To be strictly correct with the original design (T023), the RFE should be inside the CV loop
    # However, for this sensitivity analysis re-training, we approximate the pipeline.
    # A more robust way is to wrap RFE and RF in a Pipeline.
    from sklearn.pipeline import Pipeline
    pipe = Pipeline([
        ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, max_depth=None), n_features_to_select=n_features_to_select)),
        ('clf', RandomForestClassifier(random_state=RANDOM_SEED))
    ])
    
    # Re-do grid search with pipeline
    grid = GridSearchCV(
        estimator=pipe,
        param_grid=param_grid,
        cv=skf,
        scoring='roc_auc',
        n_jobs=n_jobs,
        refit=True
    )
    
    grid.fit(X, y)
    
    return grid.best_estimator_, grid.best_params_

def run_label_sensitivity_analysis():
    """
    T030b Implementation: Vary the decline-definition threshold by ±1 point.
    MUST re-train the model for each variation.
    """
    logger = get_logger_wrapper()
    logger.info("Starting Label Definition Sensitivity Analysis (T030b)...")
    
    # Load base data (features and scores)
    # We need the raw features and the score columns to recalculate labels
    if not DATA_PATH.exists():
        logger.error(f"Graph metrics file not found: {DATA_PATH}")
        sys.exit(1)
    if not ELIGIBLE_SUBJECTS_PATH.exists():
        logger.error(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
        sys.exit(1)
        
    metrics_df = load_csv(DATA_PATH)
    eligible_df = load_csv(ELIGIBLE_SUBJECTS_PATH)
    merged = pd.merge(metrics_df, eligible_df, on="subject_id", how="inner")
    
    # Identify feature columns (exclude metadata columns)
    exclude_cols = ['subject_id', 'mmse_t1', 'mmse_t2', 'moca_t1', 'moca_t2', 'decline_label']
    feature_cols = [c for c in merged.columns if c not in exclude_cols]
    
    X = merged[feature_cols].values
    logger.info(f"Using {len(feature_cols)} features for re-training.")
    
    results = []
    
    # Grid parameters (matching T023)
    param_grid = {
        'clf__n_estimators': [50, 100, 200],
        'clf__max_depth': [5, 10, None]
    }
    
    start_time = time.time()
    
    for thresh in DECLINE_THRESHOLDS:
        logger.info(f"Processing threshold: {thresh} (Drop >= {abs(thresh)})")
        
        # 1. Re-calculate labels
        y = define_decline_label(merged, thresh)
        
        # Check class balance
        class_counts = np.bincount(y)
        if len(class_counts) < 2 or class_counts[1] == 0:
            logger.warning(f"No positive samples for threshold {thresh}. Skipping.")
            results.append({
                "threshold": thresh,
                "label": THRESHOLD_LABELS.get(thresh, f"thresh_{thresh}"),
                "status": "skipped",
                "reason": "No positive samples",
                "auc": None,
                "f1": None,
                "fpr": None,
                "fnr": None
            })
            continue
        
        # 2. Re-train model (Nested CV simulation)
        # Since we are doing sensitivity on the label, we run the full training pipeline
        # We use a single train/test split for speed in this specific task, 
        # or a simplified CV if full nested is too heavy.
        # However, T030b says "MUST re-train". To be faithful to T023 logic:
        # We will run a simplified 5-fold CV to get the metric, as full nested CV 3 times 
        # might be heavy. But the prompt says "re-train the model", implying the full process.
        # Let's do a 5-fold CV to estimate performance for this threshold.
        
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
        aucs = []
        f1s = []
        
        # We also need to store predictions for the best threshold to calculate FPR/FNR
        # For the base threshold, we might want to compare, but here we just report per threshold.
        # Let's collect all predictions for the current threshold to compute confusion matrix.
        all_true = []
        all_pred = []
        
        for train_idx, test_idx in skf.split(X, y):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            try:
                model, best_params = inner_cv_pipeline(X_train, y_train, param_grid, n_jobs=2)
                
                # Evaluate on test set
                y_pred_proba = model.predict_proba(X_test)[:, 1]
                y_pred = (y_pred_proba >= 0.5).astype(int)
                
                auc = roc_auc_score(y_test, y_pred_proba)
                f1 = f1_score(y_test, y_pred)
                
                aucs.append(auc)
                f1s.append(f1)
                
                all_true.extend(y_test)
                all_pred.extend(y_pred)
                
            except Exception as e:
                logger.error(f"Error in CV fold for threshold {thresh}: {e}")
                continue
        
        if not aucs:
            results.append({
                "threshold": thresh,
                "label": THRESHOLD_LABELS.get(thresh, f"thresh_{thresh}"),
                "status": "failed",
                "reason": "Training failed in all folds",
                "auc": None,
                "f1": None,
                "fpr": None,
                "fnr": None
            })
            continue
        
        mean_auc = np.mean(aucs)
        mean_f1 = np.mean(f1s)
        
        # Calculate FPR/FNR from aggregated predictions
        cm = confusion_matrix(all_true, all_pred)
        fpr, fnr = calculate_fpr_fnr(cm)
        
        logger.info(f"Threshold {thresh}: AUC={mean_auc:.3f}, F1={mean_f1:.3f}, FPR={fpr:.3f}, FNR={fnr:.3f}")
        
        results.append({
            "threshold": thresh,
            "label": THRESHOLD_LABELS.get(thresh, f"thresh_{thresh}"),
            "status": "success",
            "auc_mean": float(mean_auc),
            "f1_mean": float(mean_f1),
            "fpr": float(fpr),
            "fnr": float(fnr),
            "n_samples": int(len(y)),
            "n_positive": int(np.sum(y))
        })
    
    elapsed = time.time() - start_time
    logger.info(f"Sensitivity analysis completed in {elapsed:.2f} seconds.")
    
    report = {
        "task_id": "T030b",
        "description": "Label definition sensitivity analysis (re-training with varied thresholds)",
        "thresholds_tested": DECLINE_THRESHOLDS,
        "results": results,
        "total_runtime_seconds": elapsed
    }
    
    # Save report
    ensure_dir(OUTPUT_PATH.parent)
    save_json(report, OUTPUT_PATH)
    logger.info(f"Sensitivity report saved to {OUTPUT_PATH}")
    
    return report

def run_threshold_sweep():
    """
    T030a Implementation (Part 1): Decision threshold sweep.
    Kept here for completeness, though T030b is the focus of this task.
    """
    logger = get_logger_wrapper()
    logger.info("Running Decision Threshold Sweep (T030a)...")
    
    if not MODEL_PATH.exists():
        logger.warning(f"Model not found at {MODEL_PATH}. Skipping threshold sweep.")
        return None

    model, data_df = load_model_and_data()
    exclude_cols = ['subject_id', 'mmse_t1', 'mmse_t2', 'moca_t1', 'moca_t2', 'decline_label']
    feature_cols = [c for c in data_df.columns if c not in exclude_cols]
    X = data_df[feature_cols].values
    y = data_df['decline_label'].values

    thresholds = [0.45, 0.50, 0.55]
    sweep_results = []
    
    for thresh in thresholds:
        y_pred_proba = model.predict_proba(X)[:, 1]
        y_pred = (y_pred_proba >= thresh).astype(int)
        
        cm = confusion_matrix(y, y_pred)
        fpr, fnr = calculate_fpr_fnr(cm)
        
        sweep_results.append({
            "threshold": thresh,
            "fpr": float(fpr),
            "fnr": float(fnr),
            "n_positive": int(np.sum(y_pred)),
            "n_negative": int(len(y_pred) - np.sum(y_pred))
        })
        
    return sweep_results

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(description="Sensitivity Analysis for Cognitive Decline Prediction")
    parser.add_argument("--mode", choices=["label", "threshold", "both"], default="label",
                        help="Mode: 'label' for T030b, 'threshold' for T030a, 'both' for both.")
    args = parser.parse_args()
    
    logger = get_logger_wrapper()
    logger.info("Starting Sensitivity Analysis Script.")
    
    results = {}
    
    if args.mode in ["label", "both"]:
        results["label_sensitivity"] = run_label_sensitivity_analysis()
    
    if args.mode in ["threshold", "both"]:
        results["threshold_sweep"] = run_threshold_sweep()
    
    # If we ran both, we might want to combine or just save separately.
    # The task T030b specifically asks for the label variation report.
    # We ensure the main output file (sensitivity_report.json) contains the T030b results.
    
    logger.info("Sensitivity Analysis complete.")

if __name__ == "__main__":
    main()