"""
Sensitivity Analysis for Cognitive Decline Prediction Model.

This script performs:
1. Decision threshold sweep over {0.45, 0.50, 0.55} on the trained model.
   Reports false-positive and false-negative rates.
2. (Part 2 placeholder: Label definition sensitivity - to be implemented in T030b)

Outputs:
- data/processed/sensitivity_report.json
"""

import os
import sys
import json
import time
import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.ensemble import RandomForestClassifier
import joblib

# Add project root to path to allow imports from utils and other code modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.io import ensure_dir, save_json, load_csv
from config import get_config

# Configure warnings
warnings.filterwarnings('ignore')

def get_logger_wrapper(name: str):
    """Wrapper to get a logger with the correct project path."""
    return get_logger(name)

def calculate_fpr_fnr(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate False Positive Rate (FPR) and False Negative Rate (FNR).

    Args:
        y_true: True binary labels (0 or 1)
        y_pred: Predicted binary labels (0 or 1)

    Returns:
        Dictionary with 'fpr' and 'fnr'
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return {'fpr': fpr, 'fnr': fnr}

def load_model_and_data(logger) -> Tuple[Any, pd.DataFrame, pd.Series]:
    """
    Load the trained model and the graph metrics data used for training.

    Assumes:
    - Model is at data/processed/model.pkl
    - Graph metrics are at data/processed/graph_metrics.csv
    - Labels were derived from data/processed/eligible_subjects.csv (MMSE/MOCA drop)

    Returns:
        model: Trained RandomForestClassifier
        X: Feature DataFrame
        y: Target Series
    """
    model_path = Path(project_root) / "data" / "processed" / "model.pkl"
    graph_metrics_path = Path(project_root) / "data" / "processed" / "graph_metrics.csv"
    eligible_subjects_path = Path(project_root) / "data" / "processed" / "eligible_subjects.csv"

    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}")
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    if not graph_metrics_path.exists():
        logger.error(f"Graph metrics file not found: {graph_metrics_path}")
        raise FileNotFoundError(f"Graph metrics file not found: {graph_metrics_path}")

    logger.info(f"Loading model from {model_path}")
    model = joblib.load(model_path)

    logger.info(f"Loading graph metrics from {graph_metrics_path}")
    graph_df = load_csv(graph_metrics_path)
    
    # Load eligible subjects to reconstruct labels
    # The label is defined as a drop >= 3 points in MMSE or MOCA
    eligible_df = load_csv(eligible_subjects_path)
    
    # Merge to get labels back
    # Assuming graph_metrics.csv has 'subject_id' and eligible_subjects.csv has 'subject_id', 'mmse_t1', 'mmse_t2', 'moca_t1', 'moca_t2'
    # We need to define the decline label here.
    # Note: The training script (04_train_model.py) likely used a specific definition.
    # We will re-calculate the label based on the drop >= 3 rule.
    
    merged_df = eligible_df.merge(graph_df[['subject_id']], on='subject_id', how='inner')
    
    # Define decline label: drop >= 3 points in MMSE OR MOCA
    # Handle potential missing values
    def define_decline_label(row):
        mmse_drop = None
        moca_drop = None
        
        if pd.notna(row.get('mmse_t1')) and pd.notna(row.get('mmse_t2')):
            mmse_drop = row['mmse_t1'] - row['mmse_t2']
        
        if pd.notna(row.get('moca_t1')) and pd.notna(row.get('moca_t2')):
            moca_drop = row['moca_t1'] - row['moca_t2']
        
        # Decline if either drops >= 3
        decline = False
        if mmse_drop is not None and mmse_drop >= 3:
            decline = True
        if moca_drop is not None and moca_drop >= 3:
            decline = True
        
        return 1 if decline else 0

    merged_df['decline_label'] = merged_df.apply(define_decline_label, axis=1)

    # Prepare X and y
    # Exclude non-feature columns from X
    feature_cols = [col for col in merged_df.columns if col not in ['subject_id', 'decline_label']]
    X = merged_df[feature_cols]
    y = merged_df['decline_label']

    logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")
    return model, X, y

def run_threshold_sweep(model: Any, X: pd.DataFrame, y: pd.Series, thresholds: List[float], logger) -> List[Dict[str, Any]]:
    """
    Run decision threshold sweep over specified thresholds.

    Args:
        model: Trained model with predict_proba method
        X: Feature DataFrame
        y: True labels
        thresholds: List of probability thresholds to test
        logger: Logger instance

    Returns:
        List of dictionaries containing metrics for each threshold
    """
    logger.info(f"Running threshold sweep over {thresholds}")
    
    # Get probability predictions for the positive class (decline)
    if hasattr(model, 'predict_proba'):
        y_proba = model.predict_proba(X)[:, 1]
    else:
        logger.error("Model does not support predict_proba")
        return []

    results = []
    
    for thresh in thresholds:
        logger.info(f"Evaluating threshold: {thresh}")
        y_pred = (y_proba >= thresh).astype(int)
        
        metrics = calculate_fpr_fnr(y.values, y_pred)
        metrics['threshold'] = thresh
        metrics['num_predicted_positive'] = int(y_pred.sum())
        metrics['num_actual_positive'] = int(y.sum())
        
        # Add accuracy for completeness
        accuracy = (y_pred == y.values).mean()
        metrics['accuracy'] = accuracy
        
        results.append(metrics)
        logger.info(f"  Threshold {thresh}: FPR={metrics['fpr']:.4f}, FNR={metrics['fnr']:.4f}, Accuracy={accuracy:.4f}")

    return results

def main():
    logger = get_logger_wrapper("sensitivity_analysis")
    logger.info("Starting Sensitivity Analysis (Part 1: Threshold Sweep)")

    try:
        # Load model and data
        model, X, y = load_model_and_data(logger)

        # Define thresholds
        thresholds = [0.45, 0.50, 0.55]

        # Run threshold sweep
        results = run_threshold_sweep(model, X, y, thresholds, logger)

        if not results:
            logger.error("Threshold sweep produced no results.")
            sys.exit(1)

        # Prepare output
        output_data = {
            "analysis_type": "decision_threshold_sweep",
            "thresholds_tested": thresholds,
            "results": results,
            "metadata": {
                "n_samples": len(X),
                "n_features": X.shape[1],
                "positive_rate": float(y.mean()),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }

        # Save output
        output_path = Path(project_root) / "data" / "processed" / "sensitivity_report.json"
        ensure_dir(output_path)
        save_json(output_data, output_path)
        
        logger.info(f"Sensitivity analysis report saved to {output_path}")
        print(f"Success: Wrote {output_path}")

    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()