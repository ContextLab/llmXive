"""
code/07_sensitivity_analysis.py
Implements T030a: Decision threshold sweep on the trained model.
Implements T030b: Label definition threshold sensitivity (re-training).

This script loads the trained Random Forest model and the processed data,
then performs two analyses:
1. Decision Threshold Sweep: Varies the probability threshold (0.45, 0.50, 0.55)
   to report False Positive and False Negative rates.
2. Label Definition Sensitivity: Varies the MMSE/MOCA decline threshold (±1 point),
   re-trains the model for each variation, and reports performance.
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, roc_auc_score, f1_score, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from config import get_config

# Suppress specific warnings for cleaner logs during analysis
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

logger = get_logger(__name__)

# --- Part 1: Decision Threshold Sweep (T030a) ---

def load_model_and_data():
    """
    Loads the trained model, features (X), and labels (y) from disk.
    Handles the specific KeyError 'data_processed_dir' by deriving paths from config.
    """
    config = get_config()
    data_dir = Path(config.get('data_processed_dir', 'data/processed'))
    model_path = data_dir / 'model.pkl'
    metrics_path = data_dir / 'graph_metrics.csv'
    subjects_path = data_dir / 'eligible_subjects.csv'

    logger.info(f"Loading model from {model_path}")
    logger.info(f"Loading metrics from {metrics_path}")
    logger.info(f"Loading subjects from {subjects_path}")

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}. Run code/04_train_model.py first.")
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}. Run code/03_compute_graph_metrics.py first.")
    if not subjects_path.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {subjects_path}. Run code/01_download_and_filter.py first.")

    # Load model
    import joblib
    model = joblib.load(model_path)

    # Load data
    df_metrics = load_csv(str(metrics_path))
    df_subjects = load_csv(str(subjects_path))

    # Merge to get labels
    # Assuming df_subjects has 'subject_id' and 'decline_label' (or similar)
    # df_metrics has 'subject_id' and graph features.
    # We need to align them.
    if 'subject_id' not in df_subjects.columns:
        # Fallback: assume index or first column is ID
        df_subjects['subject_id'] = df_subjects.index if 'subject_id' not in df_subjects.columns else df_subjects.iloc[:, 0]

    # Merge on subject_id
    if 'subject_id' in df_metrics.columns and 'subject_id' in df_subjects.columns:
        df_merged = pd.merge(df_metrics, df_subjects[['subject_id', 'decline_label']], on='subject_id', how='inner')
    else:
        # Fallback if column names differ (common in pipeline drift)
        # Try to find a common column
        common_cols = list(set(df_metrics.columns) & set(df_subjects.columns))
        if common_cols:
            df_merged = pd.merge(df_metrics, df_subjects, on=common_cols[0], how='inner')
            df_merged = df_merged.rename(columns={common_cols[0]: 'subject_id'})
        else:
            raise ValueError("No common column found to merge metrics and subject labels.")

    if 'decline_label' not in df_merged.columns:
        raise ValueError("Column 'decline_label' not found in merged data.")

    # Separate features and target
    # Assume all columns except subject_id and decline_label are features
    feature_cols = [c for c in df_merged.columns if c not in ['subject_id', 'decline_label']]
    X = df_merged[feature_cols].values
    y = df_merged['decline_label'].values

    logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features.")
    return model, X, y, df_merged['subject_id'].values

def define_decline_label(df, mmse_col='MMSE', moca_col='MOCA', threshold=3):
    """
    Helper to re-calculate decline labels based on a specific threshold.
    """
    # Logic: decline = (baseline - followup) >= threshold
    # We need to handle cases where data might be wide (two columns) or long.
    # Assuming standard wide format from previous steps: 'baseline_score', 'followup_score' or similar.
    # If the original data has 'MMSE' as a single column, we assume the pipeline already calculated the label.
    # For T030b, we need to re-calculate based on raw scores if available.
    # If raw scores are not available in the CSV, we cannot re-calculate.
    # We will assume the CSV has 'baseline_score' and 'followup_score' or similar derived columns.
    # If not, we skip re-calculation and warn.

    if 'baseline_score' in df.columns and 'followup_score' in df.columns:
        diff = df['baseline_score'] - df['followup_score']
        return (diff >= threshold).astype(int).values
    elif 'MMSE_baseline' in df.columns and 'MMSE_followup' in df.columns:
        diff = df['MMSE_baseline'] - df['MMSE_followup']
        return (diff >= threshold).astype(int).values
    else:
        logger.warning("Raw baseline/followup scores not found. Cannot re-calculate labels for T030b.")
        return None

def run_threshold_sweep(model, X, y):
    """
    Performs the decision threshold sweep over {0.45, 0.50, 0.55}.
    Returns a dict of results.
    """
    thresholds = [0.45, 0.50, 0.55]
    results = {}

    logger.info("Starting Decision Threshold Sweep (T030a)...")

    # Get probabilities
    if hasattr(model, 'predict_proba'):
        probs = model.predict_proba(X)[:, 1]
    else:
        logger.error("Model does not support predict_proba. Cannot perform threshold sweep.")
        return {}

    for thresh in thresholds:
        logger.info(f"  Evaluating threshold: {thresh}")
        preds = (probs >= thresh).astype(int)

        tn, fp, fn, tp = confusion_matrix(y, preds).ravel()
        # Avoid division by zero
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        results[str(thresh)] = {
            "threshold": float(thresh),
            "false_positive_rate": float(fpr),
            "false_negative_rate": float(fnr),
            "true_positives": int(tp),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn)
        }

    logger.info("Threshold sweep completed.")
    return results

# --- Part 2: Label Definition Sensitivity (T030b) ---

def retrain_model_for_threshold(X, y, decline_threshold, config):
    """
    Retrains the model with a specific decline threshold definition.
    This is a simplified re-training to avoid full nested CV overhead for sensitivity analysis,
    but follows the same preprocessing and model architecture.
    """
    logger.info(f"Retraining model with decline threshold: {decline_threshold}")

    # Re-calculate labels if possible
    # Note: We need the original dataframe to re-calculate labels.
    # Since we only have X and y here, we assume the caller passes the full dataframe
    # or we have access to the raw scores.
    # For this implementation, we assume the caller handles label re-calculation
    # and passes the new y.
    # However, the task says "MUST re-train the model".
    # We will simulate the re-training process using the same pipeline logic.
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train RF (using default params from T023: n_estimators=100, max_depth=None)
    model = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=42, n_jobs=-1)
    model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    auc = roc_auc_score(y_test, y_proba)
    f1 = f1_score(y_test, y_pred)
    acc = accuracy_score(y_test, y_pred)

    return {
        "decline_threshold": decline_threshold,
        "roc_auc": float(auc),
        "f1_score": float(f1),
        "accuracy": float(acc),
        "model_params": {"n_estimators": 100, "max_depth": None}
    }

def run_label_definition_sensitivity(df_merged, feature_cols, decline_thresholds):
    """
    Varies the decline definition threshold and re-trains the model.
    """
    logger.info("Starting Label Definition Sensitivity Analysis (T030b)...")
    results = {}

    # We need the raw scores to re-calculate labels.
    # If not present, we skip.
    if 'baseline_score' not in df_merged.columns or 'followup_score' not in df_merged.columns:
        logger.warning("Raw scores not available. Skipping label definition sensitivity (T030b).")
        return {}

    X = df_merged[feature_cols].values
    
    for thresh in decline_thresholds:
        y_new = define_decline_label(df_merged, threshold=thresh)
        if y_new is None:
            continue
        
        # Check class balance
        if len(np.unique(y_new)) < 2:
            logger.warning(f"Threshold {thresh} results in single class. Skipping.")
            continue

        res = retrain_model_for_threshold(X, y_new, thresh, None)
        results[str(thresh)] = res

    logger.info("Label definition sensitivity completed.")
    return results

def main():
    logger.info("Starting Sensitivity Analysis Script (T030a & T030b).")
    start_time = time.time()

    try:
        # Load data
        model, X, y, subject_ids = load_model_and_data()
        
        # Get feature columns from the dataframe used to create X
        # We need to reload the dataframe to get column names if we want to re-calculate labels
        config = get_config()
        data_dir = Path(config.get('data_processed_dir', 'data/processed'))
        metrics_path = data_dir / 'graph_metrics.csv'
        df_merged = load_csv(str(metrics_path))
        # Re-merge to get labels and raw scores if available
        subjects_path = data_dir / 'eligible_subjects.csv'
        df_subjects = load_csv(str(subjects_path))
        common_cols = list(set(df_merged.columns) & set(df_subjects.columns))
        if common_cols:
            df_full = pd.merge(df_merged, df_subjects, on=common_cols[0], how='inner')
        else:
            df_full = df_merged # Fallback

        feature_cols = [c for c in df_full.columns if c not in ['subject_id', 'decline_label']]
        X = df_full[feature_cols].values
        y = df_full['decline_label'].values

        # --- T030a: Threshold Sweep ---
        threshold_results = run_threshold_sweep(model, X, y)

        # --- T030b: Label Definition Sensitivity ---
        # Thresholds: 3 (default), 2, 4 (±1 point)
        label_results = run_label_definition_sensitivity(df_full, feature_cols, [2, 3, 4])

        # Compile final report
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "analysis_type": "sensitivity_analysis",
            "threshold_sweep": threshold_results,
            "label_definition_sensitivity": label_results,
            "runtime_seconds": time.time() - start_time
        }

        # Save output
        output_path = data_dir / 'sensitivity_report.json'
        ensure_dir(output_path)
        save_json(report, str(output_path))
        logger.info(f"Sensitivity report saved to {output_path}")

        print(json.dumps(report, indent=2))

    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()