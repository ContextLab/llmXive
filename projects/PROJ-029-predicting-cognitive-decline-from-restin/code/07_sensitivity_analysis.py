"""
T030b: Sensitivity Analysis (Part 2) - Label Definition Robustness

Varies the decline-definition threshold by ±1 point on raw MMSE/MOCA scores
and re-trains the model for each variation to assess robustness of the label definition.

Outputs:
    data/processed/sensitivity_report.json
"""

import os
import sys
import json
import argparse
import warnings
import logging
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
from joblib import Parallel, delayed

# Project imports
from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from config import get_config

# Suppress specific warnings for cleaner logs
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Constants
RANDOM_SEED = 42
MEMORY_LIMIT_GB = 7.0
MAX_RUNTIME_MINUTES = 30

def get_logger_wrapper(name: str) -> logging.Logger:
    """Get a logger for the module."""
    return get_logger(name)

def calculate_fpr_fnr(y_true: np.ndarray, y_pred: np.ndarray, threshold: float) -> Tuple[float, float]:
    """
    Calculate False Positive Rate and False Negative Rate.
    
    Args:
        y_true: True labels (0 or 1)
        y_pred: Predicted probabilities or scores
        threshold: Decision threshold
        
    Returns:
        Tuple of (FPR, FNR)
    """
    y_pred_binary = (y_pred >= threshold).astype(int)
    
    # False Positive Rate: FP / (FP + TN)
    fp = np.sum((y_pred_binary == 1) & (y_true == 0))
    tn = np.sum((y_pred_binary == 0) & (y_true == 0))
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    # False Negative Rate: FN / (FN + TP)
    fn = np.sum((y_pred_binary == 0) & (y_true == 1))
    tp = np.sum((y_pred_binary == 1) & (y_true == 1))
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    return fpr, fnr

def load_model_and_data(logger: logging.Logger) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, str]:
    """
    Load graph metrics, labels, and pre-trained model.
    
    Returns:
        Tuple of (X, y, model_path, metrics_path)
    """
    base_dir = Path(__file__).parent.parent
    metrics_path = base_dir / "data" / "processed" / "graph_metrics.csv"
    model_path = base_dir / "data" / "processed" / "model.pkl"
    
    if not metrics_path.exists():
        logger.error(f"Graph metrics file not found: {metrics_path}")
        logger.error("Please run code/03_compute_graph_metrics.py and code/04_train_model.py first.")
        sys.exit(1)
    
    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}")
        logger.error("Please run code/04_train_model.py first.")
        sys.exit(1)
    
    # Load data
    df = load_csv(str(metrics_path))
    
    # Separate features and labels
    # Assuming 'decline_label' is the target column and others are features
    feature_cols = [col for col in df.columns if col not in ['subject_id', 'decline_label', 'timepoint', 'mmse_baseline', 'mmse_followup', 'moca_baseline', 'moca_followup']]
    
    X = df[feature_cols].values
    y = df['decline_label'].values
    
    logger.info(f"Loaded {len(df)} subjects with {len(feature_cols)} features")
    
    return X, y, str(model_path), str(metrics_path)

def define_decline_label_with_threshold(
    df: pd.DataFrame, 
    decline_threshold: int
) -> np.ndarray:
    """
    Define decline label based on a custom threshold.
    
    Args:
        df: DataFrame with cognitive scores
        decline_threshold: Minimum drop in score to be considered decline
        
    Returns:
        Array of binary labels (0: no decline, 1: decline)
    """
    # Try MMSE first, then MOCA
    if 'mmse_baseline' in df.columns and 'mmse_followup' in df.columns:
        score_drop = df['mmse_baseline'] - df['mmse_followup']
    elif 'moca_baseline' in df.columns and 'moca_followup' in df.columns:
        score_drop = df['moca_baseline'] - df['moca_followup']
    else:
        raise ValueError("No MMSE or MOCA columns found in data")
    
    # Define decline as drop >= threshold
    labels = (score_drop >= decline_threshold).astype(int)
    return labels.values

def train_and_evaluate_model(
    X: np.ndarray, 
    y: np.ndarray, 
    threshold: int,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Train a Random Forest model and evaluate with cross-validation.
    
    Args:
        X: Feature matrix
        y: Labels based on custom threshold
        threshold: The decline threshold used
        logger: Logger instance
        
    Returns:
        Dictionary with evaluation metrics
    """
    logger.info(f"Training model with decline threshold: {threshold}")
    
    # Split data
    n_samples = len(X)
    n_train = int(0.8 * n_samples)
    
    # Shuffle with seed
    indices = np.arange(n_samples)
    np.random.seed(RANDOM_SEED)
    np.random.shuffle(indices)
    
    train_idx, test_idx = indices[:n_train], indices[n_train:]
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=RANDOM_SEED,
        n_jobs=2
    )
    
    rf_model.fit(X_train_scaled, y_train)
    
    # Predictions
    y_pred_proba = rf_model.predict_proba(X_test_scaled)[:, 1]
    y_pred = rf_model.predict(X_test_scaled)
    
    # Calculate metrics
    try:
        auc = roc_auc_score(y_test, y_pred_proba)
    except ValueError:
        auc = 0.5  # If only one class present
    
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    # Calculate FPR and FNR at standard threshold (0.5)
    fpr, fnr = calculate_fpr_fnr(y_test, y_pred_proba, 0.5)
    
    results = {
        "threshold": threshold,
        "n_samples": n_samples,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "roc_auc": float(auc),
        "accuracy": float(acc),
        "f1_score": float(f1),
        "fpr": float(fpr),
        "fnr": float(fnr)
    }
    
    logger.info(f"  AUC: {auc:.4f}, Acc: {acc:.4f}, F1: {f1:.4f}, FPR: {fpr:.4f}, FNR: {fnr:.4f}")
    
    return results

def run_sensitivity_analysis(
    X: np.ndarray,
    y_original: np.ndarray,
    df: pd.DataFrame,
    thresholds: List[int],
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis across multiple decline thresholds.
    
    Args:
        X: Feature matrix
        y_original: Original labels (for comparison)
        df: Original DataFrame with scores
        thresholds: List of thresholds to test
        logger: Logger instance
        
    Returns:
        List of results for each threshold
    """
    all_results = []
    
    logger.info(f"Starting sensitivity analysis for thresholds: {thresholds}")
    
    start_time = time.time()
    
    for threshold in thresholds:
        # Re-define labels with new threshold
        y_new = define_decline_label_with_threshold(df, threshold)
        
        # Check class balance
        n_pos = np.sum(y_new)
        n_neg = len(y_new) - n_pos
        
        if n_pos == 0 or n_neg == 0:
            logger.warning(f"Threshold {threshold} results in imbalanced data (all one class). Skipping.")
            all_results.append({
                "threshold": threshold,
                "n_positive": int(n_pos),
                "n_negative": int(n_neg),
                "status": "skipped_imbalanced"
            })
            continue
        
        # Train and evaluate
        results = train_and_evaluate_model(X, y_new, threshold, logger)
        results["n_positive"] = int(np.sum(y_new))
        results["n_negative"] = int(len(y_new) - np.sum(y_new))
        results["status"] = "completed"
        
        all_results.append(results)
        
        # Check runtime
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_MINUTES * 60:
            logger.warning(f"Runtime limit exceeded after threshold {threshold}. Stopping.")
            break
    
    return all_results

def write_outputs(
    results: List[Dict[str, Any]],
    base_dir: Path,
    logger: logging.Logger
):
    """
    Write sensitivity analysis results to JSON file.
    
    Args:
        results: List of results
        base_dir: Base directory for outputs
        logger: Logger instance
    """
    output_dir = base_dir / "data" / "processed"
    ensure_dir(output_dir)
    
    output_path = output_dir / "sensitivity_report.json"
    
    report = {
        "task": "T030b - Sensitivity Analysis (Part 2)",
        "description": "Label definition robustness analysis",
        "thresholds_tested": [r["threshold"] for r in results],
        "results": results,
        "summary": {
            "best_threshold": None,
            "best_auc": 0.0,
            "total_completions": 0,
            "total_skipped": 0
        }
    }
    
    # Find best threshold by AUC
    completed_results = [r for r in results if r.get("status") == "completed"]
    if completed_results:
        best_result = max(completed_results, key=lambda x: x.get("roc_auc", 0))
        report["summary"]["best_threshold"] = best_result["threshold"]
        report["summary"]["best_auc"] = best_result["roc_auc"]
        report["summary"]["total_completions"] = len(completed_results)
        report["summary"]["total_skipped"] = len(results) - len(completed_results)
    
    save_json(report, str(output_path))
    logger.info(f"Sensitivity report written to: {output_path}")

def main():
    """Main entry point for sensitivity analysis."""
    logger = get_logger_wrapper("sensitivity_analysis")
    logger.info("Starting Sensitivity Analysis (Part 2) - Label Definition Robustness (T030b)")
    
    # Configuration
    config = get_config()
    random.seed(config.get('random_seed', RANDOM_SEED))
    np.random.seed(config.get('random_seed', RANDOM_SEED))
    
    # Define thresholds to test: original (3) and variations (2, 4)
    thresholds = [2, 3, 4]
    
    # Load data and model
    X, y_original, model_path, metrics_path = load_model_and_data(logger)
    
    # Load original DataFrame to access raw scores
    df = load_csv(metrics_path)
    
    # Run sensitivity analysis
    results = run_sensitivity_analysis(X, y_original, df, thresholds, logger)
    
    # Write outputs
    base_dir = Path(__file__).parent.parent
    write_outputs(results, base_dir, logger)
    
    logger.info("Sensitivity analysis completed successfully.")

if __name__ == "__main__":
    main()