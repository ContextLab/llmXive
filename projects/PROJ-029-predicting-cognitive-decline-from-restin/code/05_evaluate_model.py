"""
code/05_evaluate_model.py
Evaluate the trained model (from T023) by calculating ROC-AUC, accuracy, and F1-score
per fold and mean, then outputting a JSON report.
"""

import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from joblib import load

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.io import ensure_dir, save_json

def get_logger_wrapper():
    """Initialize logger for this script."""
    return get_logger(__name__)

def calculate_metrics(y_true, y_pred, y_prob):
    """
    Calculate ROC-AUC, accuracy, and F1-score.
    
    Args:
        y_true: Ground truth labels (array-like)
        y_pred: Predicted labels (array-like)
        y_prob: Predicted probabilities for the positive class (array-like)
    
    Returns:
        dict: Metrics dictionary
    """
    metrics = {}
    
    # Ensure inputs are numpy arrays
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    y_prob = np.array(y_prob)
    
    # Check for valid inputs for ROC-AUC (needs at least one positive and one negative)
    if len(np.unique(y_true)) > 1:
        metrics['roc_auc'] = float(roc_auc_score(y_true, y_prob))
    else:
        metrics['roc_auc'] = None
    
    metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
    metrics['f1_score'] = float(f1_score(y_true, y_pred, zero_division=0))
    
    return metrics

def evaluate_model(model_path, data_path, output_path):
    """
    Load the trained model and data, evaluate per-fold metrics, and save report.
    
    Args:
        model_path: Path to the trained model (joblib file) containing CV results
        data_path: Path to the graph metrics CSV (for reference/logging)
        output_path: Path to write the performance report JSON
    """
    logger = get_logger_wrapper()
    logger.info(f"Starting evaluation from model: {model_path}")
    
    # Load the model and training results
    # The model file from T023 (04_train_model.py) is expected to contain the trained RF
    # and ideally the cross-validation results (y_true, y_pred, y_prob per fold)
    # If the model file only contains the estimator, we need to re-run prediction on the
    # held-out folds if they were saved, or load the specific CV results if saved separately.
    # Based on T023 spec, we assume the training script saves the full CV context or we
    # load the model and the data to re-predict if the model object stores history.
    #
    # CRITICAL: T023 (04_train_model.py) must have saved the cross-validation results.
    # We assume it saved a dict: {'model': rf, 'cv_results': [...], ...}
    # If it only saved the model, we cannot calculate per-fold metrics without re-running CV.
    # We will assume the training script saved a 'cv_results' key with the necessary arrays.
    
    try:
        trained_data = load(model_path)
    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}")
        raise
    
    # Check if cv_results are present. If not, we cannot evaluate per-fold.
    if 'cv_results' not in trained_data:
        logger.error("Model file does not contain 'cv_results'. T023 must be fixed to save them.")
        raise ValueError("Missing 'cv_results' in model file. Ensure T023 saves cross-validation outputs.")
    
    cv_results = trained_data['cv_results']
    
    per_fold_metrics = []
    all_y_true = []
    all_y_pred = []
    all_y_prob = []
    
    logger.info(f"Evaluating {len(cv_results)} folds...")
    
    for i, fold_data in enumerate(cv_results):
        y_true_fold = fold_data.get('y_true')
        y_pred_fold = fold_data.get('y_pred')
        y_prob_fold = fold_data.get('y_prob')
        
        if y_true_fold is None or y_pred_fold is None or y_prob_fold is None:
            logger.warning(f"Fold {i} missing prediction data. Skipping.")
            continue
        
        metrics = calculate_metrics(y_true_fold, y_pred_fold, y_prob_fold)
        metrics['fold'] = i + 1
        per_fold_metrics.append(metrics)
        
        all_y_true.extend(y_true_fold)
        all_y_pred.extend(y_pred_fold)
        all_y_prob.extend(y_prob_fold)
    
    if not per_fold_metrics:
        logger.error("No valid fold metrics found.")
        raise ValueError("No valid fold metrics found in cv_results.")
    
    # Calculate mean metrics
    mean_roc_auc = np.mean([m['roc_auc'] for m in per_fold_metrics if m['roc_auc'] is not None])
    mean_accuracy = np.mean([m['accuracy'] for m in per_fold_metrics])
    mean_f1 = np.mean([m['f1_score'] for m in per_fold_metrics])
    
    report = {
        "per_fold": per_fold_metrics,
        "mean_metrics": {
            "roc_auc": float(mean_roc_auc),
            "accuracy": float(mean_accuracy),
            "f1_score": float(mean_f1)
        },
        "total_folds": len(per_fold_metrics),
        "model_path": str(model_path),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Ensure output directory exists
    ensure_dir(output_path)
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Evaluation complete. Report saved to: {output_path}")
    return report

def main():
    """Main entry point."""
    logger = get_logger_wrapper()
    
    # Define paths relative to project root
    # The model is saved by T023 (04_train_model.py) to data/processed/model.pkl
    project_root = Path(__file__).parent.parent
    model_path = project_root / "data" / "processed" / "model.pkl"
    data_path = project_root / "data" / "processed" / "graph_metrics.csv"
    output_path = project_root / "data" / "processed" / "performance_report.json"
    
    if not model_path.exists():
        logger.error(f"Model file not found at {model_path}. Run T023 first.")
        sys.exit(1)
    
    if not data_path.exists():
        logger.warning(f"Graph metrics file not found at {data_path}. Evaluation may proceed without data reference.")
    
    try:
        evaluate_model(str(model_path), str(data_path), str(output_path))
        logger.info("Task T024 completed successfully.")
    except Exception as e:
        logger.error(f"Task T024 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()