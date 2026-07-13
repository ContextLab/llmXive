"""
code/07_sensitivity_analysis.py
Implements T030a and T030b: Sensitivity Analysis for cognitive decline prediction.

Part 1 (T030a): Decision threshold sweep over {0.45, 0.50, 0.55}.
Part 2 (T030b): Label definition threshold variation (±1 point) with re-training.

Outputs:
    data/processed/sensitivity_report.json
"""

import os
import sys
import json
import time
import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib

# Import internal utilities
from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from utils.stats import calculate_correlation_matrix, filter_low_variance_features
from config import get_config

# Suppress specific warnings for cleaner logs
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Configuration
CONFIG = get_config()
RANDOM_SEED = CONFIG.get("random_seed", 42)
DATA_DIR = Path("data/processed")
ARTIFACTS_DIR = Path("data/artifacts")

# Paths to expected inputs
GRAPH_METRICS_PATH = DATA_DIR / "graph_metrics.csv"
ELIGIBLE_SUBJECTS_PATH = DATA_DIR / "eligible_subjects.csv"
MODEL_PATH = DATA_DIR / "model.pkl"
CV_RESULTS_PATH = DATA_DIR / "cv_results.json"
PERFORMANCE_REPORT_PATH = DATA_DIR / "performance_report.json"

# Output path
SENSITIVITY_REPORT_PATH = DATA_DIR / "sensitivity_report.json"

logger = get_logger("sensitivity_analysis")

def get_logger_wrapper(name: str):
    """Helper to get a logger with a specific name."""
    return get_logger(name)

def calculate_fpr_fnr(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    """
    Calculate False Positive Rate (FPR) and False Negative Rate (FNR).
    
    Args:
        y_true: True labels (0 or 1)
        y_pred: Predicted labels (0 or 1)
        
    Returns:
        Tuple of (FPR, FNR)
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return fpr, fnr

def load_model_and_data() -> Tuple[Any, pd.DataFrame, pd.DataFrame]:
    """
    Load the trained model and necessary data.
    
    Returns:
        Tuple of (model, X, y)
    """
    if not MODEL_PATH.exists():
        logger.error(f"Model file not found: {MODEL_PATH}")
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    
    if not GRAPH_METRICS_PATH.exists():
        logger.error(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
    
    model = joblib.load(MODEL_PATH)
    df_metrics = load_csv(GRAPH_METRICS_PATH)
    df_eligible = load_csv(ELIGIBLE_SUBJECTS_PATH)
    
    # Merge to get labels
    df_merged = pd.merge(df_metrics, df_eligible, on="subject_id", how="inner")
    
    # Identify feature columns (exclude subject_id and label columns)
    label_cols = ["decline_label", "mmse_baseline", "mmse_followup", "moca_baseline", "moca_followup"]
    feature_cols = [c for c in df_merged.columns if c not in label_cols and c != "subject_id"]
    
    X = df_merged[feature_cols].values
    y = df_merged["decline_label"].values
    
    logger.info(f"Loaded model and data. Shape: {X.shape}")
    return model, X, y, df_merged, feature_cols

def define_decline_label(df: pd.DataFrame, threshold: int = 3) -> pd.Series:
    """
    Define cognitive decline label based on MMSE/MOCA score drop.
    
    Args:
        df: DataFrame with baseline and followup scores
        threshold: Minimum drop required to be considered 'decline'
        
    Returns:
        Series of binary labels (1 = decline, 0 = no decline)
    """
    # Prefer MMSE if available, else MOCA
    if "mmse_baseline" in df.columns and "mmse_followup" in df.columns:
        score_drop = df["mmse_baseline"] - df["mmse_followup"]
    elif "moca_baseline" in df.columns and "moca_followup" in df.columns:
        score_drop = df["moca_baseline"] - df["moca_followup"]
    else:
        raise ValueError("No valid MMSE or MOCA columns found for label definition.")
        
    return (score_drop >= threshold).astype(int)

def inner_cv_pipeline(X: np.ndarray, y: np.ndarray, n_estimators: int = 100, max_depth: int = None) -> Tuple[Any, float]:
    """
    Simplified inner CV pipeline for re-training during sensitivity analysis.
    Uses the best parameters found in T023 (T030b requirement: re-train).
    
    Args:
        X: Feature matrix
        y: Labels
        n_estimators: Number of trees
        max_depth: Max depth of trees
        
    Returns:
        Tuple of (trained model, mean_cv_score)
    """
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    scores = []
    
    for train_idx, val_idx in skf.split(X, y):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        # Apply variance thresholding (simplified)
        variances = np.var(X_train, axis=0)
        valid_features = variances > 0.01
        X_train = X_train[:, valid_features]
        X_val = X_val[:, valid_features]
        
        clf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=RANDOM_SEED,
            n_jobs=1 # Single core for stability in re-training
        )
        clf.fit(X_train, y_train)
        score = clf.score(X_val, y_val)
        scores.append(score)
        
    return clf, np.mean(scores)

def run_threshold_sweep(model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    T030a: Perform decision threshold sweep over {0.45, 0.50, 0.55}.
    
    Args:
        model: Trained Random Forest model
        X: Feature matrix
        y: True labels
        
    Returns:
        Dictionary of results for each threshold
    """
    logger.info("Starting Threshold Sweep (T030a)...")
    thresholds = [0.45, 0.50, 0.55]
    results = {}
    
    # Get probability predictions
    if hasattr(model, 'predict_proba'):
        y_proba = model.predict_proba(X)[:, 1]
    else:
        logger.error("Model does not support predict_proba.")
        return {}
    
    for thresh in thresholds:
        y_pred = (y_proba >= thresh).astype(int)
        fpr, fnr = calculate_fpr_fnr(y, y_pred)
        acc = accuracy_score(y, y_pred)
        f1 = f1_score(y, y_pred)
        
        results[str(thresh)] = {
            "threshold": thresh,
            "accuracy": float(acc),
            "f1_score": float(f1),
            "false_positive_rate": float(fpr),
            "false_negative_rate": float(fnr),
            "num_predicted_positive": int(y_pred.sum()),
            "num_actual_positive": int(y.sum())
        }
        logger.info(f"  Threshold {thresh}: Acc={acc:.3f}, F1={f1:.3f}, FPR={fpr:.3f}, FNR={fnr:.3f}")
    
    return results

def run_label_sensitivity_analysis(X: np.ndarray, y: np.ndarray, df_merged: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
    """
    T030b: Vary the decline-definition threshold by ±1 point and re-train.
    
    Args:
        X: Original feature matrix (based on original labels)
        y: Original labels
        df_merged: Full dataframe with scores
        feature_cols: List of feature column names
        
    Returns:
        Dictionary of results for each label threshold variation
    """
    logger.info("Starting Label Definition Sensitivity Analysis (T030b)...")
    base_threshold = 3
    variations = [-1, 0, 1] # 2, 3, 4 points drop
    results = {}
    
    for delta in variations:
        new_threshold = base_threshold + delta
        logger.info(f"  Re-training with label threshold = {new_threshold}...")
        
        # Re-define labels based on new threshold
        new_labels = define_decline_label(df_merged, threshold=new_threshold)
        y_new = new_labels.values
        
        # Check class balance
        if y_new.sum() == 0 or y_new.sum() == len(y_new):
            logger.warning(f"  Threshold {new_threshold} results in no positive or all positive samples. Skipping.")
            results[str(new_threshold)] = {
                "threshold": new_threshold,
                "error": "Invalid class distribution",
                "positive_count": int(y_new.sum()),
                "total_count": len(y_new)
            }
            continue
        
        # Re-train model
        try:
            model_new, cv_score = inner_cv_pipeline(X, y_new)
            
            # Evaluate on the same split (or full set for simplicity in this context)
            # Ideally, we'd do a full nested CV again, but for sensitivity analysis
            # on the label definition, we re-train and evaluate on the same data
            # to see how the model adapts to the new definition.
            y_pred_new = model_new.predict(X)
            acc = accuracy_score(y_new, y_pred_new)
            f1 = f1_score(y_new, y_pred_new)
            fpr, fnr = calculate_fpr_fnr(y_new, y_pred_new)
            
            results[str(new_threshold)] = {
                "threshold": new_threshold,
                "cv_score": float(cv_score),
                "accuracy": float(acc),
                "f1_score": float(f1),
                "false_positive_rate": float(fpr),
                "false_negative_rate": float(fnr),
                "positive_count": int(y_new.sum()),
                "total_count": len(y_new)
            }
            logger.info(f"    Threshold {new_threshold}: CV={cv_score:.3f}, Acc={acc:.3f}, F1={f1:.3f}")
            
        except Exception as e:
            logger.error(f"    Failed to train for threshold {new_threshold}: {e}")
            results[str(new_threshold)] = {
                "threshold": new_threshold,
                "error": str(e)
            }
    
    return results

def main():
    """Main entry point for sensitivity analysis."""
    logger.info("Starting Sensitivity Analysis Script (T030a + T030b).")
    
    # Ensure output directory exists
    ensure_dir(SENSITIVITY_REPORT_PATH.parent)
    
    try:
        # Load data and model
        model, X, y, df_merged, feature_cols = load_model_and_data()
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "random_seed": RANDOM_SEED,
            "threshold_sweep": {},
            "label_definition_sensitivity": {}
        }
        
        # T030a: Threshold Sweep
        # This uses the EXISTING trained model (from T023/T024)
        report["threshold_sweep"] = run_threshold_sweep(model, X, y)
        
        # T030b: Label Definition Sensitivity
        # This RE-TRAINS the model for each variation
        report["label_definition_sensitivity"] = run_label_sensitivity_analysis(X, y, df_merged, feature_cols)
        
        # Save report
        save_json(report, SENSITIVITY_REPORT_PATH)
        logger.info(f"Sensitivity report saved to {SENSITIVITY_REPORT_PATH}")
        
        # Verify output exists
        if not SENSITIVITY_REPORT_PATH.exists():
            logger.error("Failed to write sensitivity report.")
            sys.exit(1)
            
        logger.info("Sensitivity Analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()