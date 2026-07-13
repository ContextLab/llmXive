"""
Sensitivity Analysis Script (T030a & T030b).

Implements:
- Part 1 (T030a): Decision threshold sweep (0.45, 0.50, 0.55).
- Part 2 (T030b): Label definition sensitivity (vary decline threshold by ±1 point).
  For T030b, this script MUST re-train the model for each variation.
"""

import os
import sys
import json
import time
import argparse
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score, fpr_score, confusion_matrix

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from config import get_config

# Configure logging
logger = get_logger("sensitivity_analysis")

# Constants
CONFIG = get_config()
DATA_DIR = Path(CONFIG["data_dir"])
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
MODEL_PATH = PROCESSED_DIR / "model.pkl"
GRAPH_METRICS_PATH = PROCESSED_DIR / "graph_metrics.csv"
ELIGIBLE_SUBJECTS_PATH = PROCESSED_DIR / "eligible_subjects.csv"
SENSITIVITY_REPORT_PATH = PROCESSED_DIR / "sensitivity_report.json"

# Random seed
RANDOM_SEED = CONFIG.get("random_seed", 42)
np.random.seed(RANDOM_SEED)

def get_logger_wrapper(name):
    """Helper to get a logger with a specific name."""
    return get_logger(name)

def calculate_fpr_fnr(y_true, y_pred):
    """
    Calculate False Positive Rate and False Negative Rate.
    FPR = FP / (FP + TN)
    FNR = FN / (FN + TP)
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return fpr, fnr

def load_model_and_data():
    """
    Load the pre-trained model and the necessary data for sensitivity analysis.
    Returns:
        model: The trained RandomForest model.
        X: Feature matrix (graph metrics).
        y: Original labels (decline status).
        metadata: DataFrame with raw scores (MMSE/MOCA) for label re-definition.
    """
    if not MODEL_PATH.exists():
        logger.error(f"Model file not found: {MODEL_PATH}")
        logger.error("Please run code/04_train_model.py and code/05_evaluate_model.py first.")
        sys.exit(1)

    if not GRAPH_METRICS_PATH.exists():
        logger.error(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
        logger.error("Please run code/03_compute_graph_metrics.py first.")
        sys.exit(1)

    if not ELIGIBLE_SUBJECTS_PATH.exists():
        logger.error(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
        logger.error("Please run code/01_download_and_filter.py first.")
        sys.exit(1)

    logger.info(f"Loading model from {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)

    logger.info(f"Loading graph metrics from {GRAPH_METRICS_PATH}")
    df_metrics = load_csv(GRAPH_METRICS_PATH)

    logger.info(f"Loading eligible subjects from {ELIGIBLE_SUBJECTS_PATH}")
    df_eligible = load_csv(ELIGIBLE_SUBJECTS_PATH)

    # Merge to get raw scores for label re-definition
    # Assuming df_eligible has columns: subject_id, mmse_t1, mmse_t2, moca_t1, moca_t2 (or similar)
    # and df_metrics has subject_id and graph metrics.
    df = pd.merge(df_metrics, df_eligible, on="subject_id", how="inner")

    if df.empty:
        logger.error("No overlapping subjects found between metrics and eligible subjects.")
        sys.exit(1)

    # Drop rows with NaN in critical columns
    # Note: Fixed the missing parentheses in the original code
    df = df.dropna(subset=["subject_id"])

    # Identify feature columns (exclude subject_id and raw score columns)
    # Assuming raw score columns are named like 'mmse_t1', 'mmse_t2', 'moca_t1', 'moca_t2'
    raw_cols = [c for c in df.columns if c.startswith(('mmse_', 'moca_')) or c in ['subject_id']]
    feature_cols = [c for c in df.columns if c not in raw_cols and c != 'subject_id']

    if not feature_cols:
        logger.error("No feature columns found in graph metrics.")
        sys.exit(1)

    X = df[feature_cols].values
    # We need the original labels to compare, but for T030b we will re-define them
    # So we return the raw data needed to re-define labels
    metadata = df[["subject_id"] + raw_cols]

    logger.info(f"Loaded {len(X)} subjects with {len(feature_cols)} features.")
    return model, X, metadata, feature_cols

def define_decline_label(metadata, threshold_points):
    """
    Define decline labels based on raw scores.
    Decline is defined as a drop of >= threshold_points in MMSE or MOCA.
    Args:
        metadata: DataFrame with subject_id and raw scores (mmse_t1, mmse_t2, etc.)
        threshold_points: Integer threshold for decline (e.g., 3, 2, 4).
    Returns:
        y: Array of binary labels (1 = decline, 0 = no decline).
    """
    # Check which score columns exist
    mmse_cols = [c for c in metadata.columns if 'mmse' in c.lower()]
    moca_cols = [c for c in metadata.columns if 'moca' in c.lower()]

    if not mmse_cols and not moca_cols:
        logger.error("No MMSE or MOCA score columns found in metadata.")
        sys.exit(1)

    y = np.zeros(len(metadata), dtype=int)

    # Logic: Decline if drop >= threshold in EITHER MMSE or MOCA
    # We assume t1 and t2 are available. If only one is available, we skip that modality.
    for idx, row in metadata.iterrows():
        decline = False
        # Check MMSE
        if len(mmse_cols) >= 2:
            # Assume sorted: t1, t2. If not, we need to identify them properly.
            # For simplicity, assume the first two found are t1, t2 or we look for suffixes.
            # Let's try to find 't1' and 't2' explicitly or just sort by name if ambiguous.
            # A robust way: find columns ending in _t1 and _t2
            mmse_t1_cols = [c for c in mmse_cols if 't1' in c.lower()]
            mmse_t2_cols = [c for c in mmse_cols if 't2' in c.lower()]

            if mmse_t1_cols and mmse_t2_cols:
                # Take the first match for each
                t1_val = row[mmse_t1_cols[0]]
                t2_val = row[mmse_t2_cols[0]]
                if pd.notna(t1_val) and pd.notna(t2_val):
                    if (t1_val - t2_val) >= threshold_points:
                        decline = True

        # Check MOCA if not already declined
        if not decline and len(moca_cols) >= 2:
            moca_t1_cols = [c for c in moca_cols if 't1' in c.lower()]
            moca_t2_cols = [c for c in moca_cols if 't2' in c.lower()]

            if moca_t1_cols and moca_t2_cols:
                t1_val = row[moca_t1_cols[0]]
                t2_val = row[moca_t2_cols[0]]
                if pd.notna(t1_val) and pd.notna(t2_val):
                    if (t1_val - t2_val) >= threshold_points:
                        decline = True

        y[idx] = 1 if decline else 0

    return y

def run_threshold_sweep(model, X, metadata, feature_cols):
    """
    Part 1 (T030a): Run decision threshold sweep over {0.45, 0.50, 0.55}.
    Uses the pre-trained model and original labels.
    """
    logger.info("Starting Decision Threshold Sweep (T030a)...")

    # Re-load original labels (threshold=3)
    y_orig = define_decline_label(metadata, threshold_points=3)

    # Get probabilities from the model
    y_prob = model.predict_proba(X)[:, 1]

    thresholds = [0.45, 0.50, 0.55]
    results = []

    for thresh in thresholds:
        y_pred = (y_prob >= thresh).astype(int)
        fpr, fnr = calculate_fpr_fnr(y_orig, y_pred)
        results.append({
            "type": "decision_threshold",
            "threshold": thresh,
            "fpr": float(fpr),
            "fnr": float(fnr)
        })
        logger.info(f"  Threshold {thresh}: FPR={fpr:.4f}, FNR={fnr:.4f}")

    return results

def run_label_definition_sensitivity(X, metadata, feature_cols):
    """
    Part 2 (T030b): Vary the decline-definition threshold by ±1 point.
    MUST re-train the model for each variation.
    Thresholds: 2, 3, 4 (Original is 3).
    """
    logger.info("Starting Label Definition Sensitivity Analysis (T030b)...")
    logger.info("This step re-trains the model for each threshold variation.")

    thresholds = [2, 3, 4] # ±1 from original 3
    results = []

    # We need a simple training pipeline to re-train.
    # Since we don't have the exact hyperparameters from the original training
    # (unless we load them from a config or the model object), we will use
    # a standard Random Forest with default-ish parameters or try to infer from the loaded model.
    # However, to be robust, we will use a standard RF configuration similar to T023.
    # T023 used n_estimators=100, max_depth=None (or grid search).
    # We will use a fixed seed and standard parameters for consistency in this sensitivity check.

    base_params = {
        'n_estimators': 100,
        'max_depth': None,
        'random_state': RANDOM_SEED,
        'n_jobs': -1
    }

    # Use CV to evaluate performance for each new label set
    # We use a simple 5-fold CV to get an estimate of performance (ROC-AUC)
    # and then calculate FPR/FNR on the full dataset using the CV predictions?
    # Or re-train on full data and report FPR/FNR?
    # The task asks for "Report false-positive/false-negative rates".
    # Usually, FPR/FNR are calculated on a held-out set.
    # Since we are re-training, we will do a simple train/test split or CV.
    # To match the "re-train" requirement, we will train on the full data for each threshold
    # and then calculate FPR/FNR on the full data (which is optimistic but consistent with the prompt's
    # "re-train... to assess robustness" instruction).
    # Alternatively, we can do a simple split. Let's do a simple 80/20 split to get realistic FPR/FNR.

    from sklearn.model_selection import train_test_split

    for thresh in thresholds:
        logger.info(f"  Training model with decline threshold = {thresh}...")

        # Re-define labels
        y_new = define_decline_label(metadata, threshold_points=thresh)

        # Check class balance
        if np.sum(y_new) == 0 or np.sum(y_new) == len(y_new):
            logger.warning(f"  Threshold {thresh} results in no positive or no negative samples. Skipping.")
            results.append({
                "type": "label_definition",
                "threshold": thresh,
                "status": "skipped",
                "reason": "Class imbalance (all 0 or all 1)"
            })
            continue

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_new, test_size=0.2, random_state=RANDOM_SEED, stratify=y_new
        )

        # Train model
        model_temp = RandomForestClassifier(**base_params)
        model_temp.fit(X_train, y_train)

        # Predict on test set
        y_pred = model_temp.predict(X_test)

        # Calculate FPR/FNR
        fpr, fnr = calculate_fpr_fnr(y_test, y_pred)

        results.append({
            "type": "label_definition",
            "threshold": thresh,
            "fpr": float(fpr),
            "fnr": float(fnr),
            "n_positives": int(np.sum(y_test)),
            "n_negatives": int(len(y_test) - np.sum(y_test))
        })

        logger.info(f"    Threshold {thresh}: FPR={fpr:.4f}, FNR={fnr:.4f} (on test set)")

    return results

def main():
    """Main entry point for sensitivity analysis."""
    logger.info("Starting Sensitivity Analysis Script.")

    # Load data and model
    model, X, metadata, feature_cols = load_model_and_data()

    all_results = {
        "decision_threshold_sweep": [],
        "label_definition_sensitivity": []
    }

    # Part 1: Decision Threshold Sweep (T030a)
    try:
        all_results["decision_threshold_sweep"] = run_threshold_sweep(model, X, metadata, feature_cols)
    except Exception as e:
        logger.error(f"Error in decision threshold sweep: {e}")
        import traceback
        traceback.print_exc()

    # Part 2: Label Definition Sensitivity (T030b)
    try:
        all_results["label_definition_sensitivity"] = run_label_definition_sensitivity(X, metadata, feature_cols)
    except Exception as e:
        logger.error(f"Error in label definition sensitivity: {e}")
        import traceback
        traceback.print_exc()

    # Save results
    ensure_dir(SENSITIVITY_REPORT_PATH.parent)
    with open(SENSITIVITY_REPORT_PATH, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Sensitivity analysis complete. Results saved to {SENSITIVITY_REPORT_PATH}")

    # Return success
    return 0

if __name__ == "__main__":
    sys.exit(main())
