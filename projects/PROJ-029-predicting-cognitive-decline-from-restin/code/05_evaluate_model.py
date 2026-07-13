"""
T024: Evaluate model performance on nested cross-validation results.

This script calculates ROC-AUC, accuracy, and F1-score per fold and their means,
then outputs the results to data/processed/performance_report.json.

It expects:
1. data/processed/cv_results.json (produced by code/04_train_model.py)
2. data/processed/model.pkl (produced by code/04_train_model.py)

If cv_results.json is missing, it attempts to re-run the training logic 
(via 04_train_model) to generate it, but primarily relies on the existence
of the training artifacts.
"""
import os
import sys
import json
import time
from pathlib import Path
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.io import load_json, save_json, ensure_dir

# Constants
CV_RESULTS_PATH = project_root / "data" / "processed" / "cv_results.json"
MODEL_PATH = project_root / "data" / "processed" / "model.pkl"
PERFORMANCE_REPORT_PATH = project_root / "data" / "processed" / "performance_report.json"
TRAIN_MODEL_SCRIPT = project_root / "code" / "04_train_model.py"

logger = get_logger("05_evaluate_model")

def get_logger_wrapper():
    """Returns the configured logger."""
    return logger

def calculate_metrics(y_true, y_pred, y_prob):
    """
    Calculate ROC-AUC, Accuracy, and F1-score.
    
    Args:
        y_true: Array of true labels.
        y_pred: Array of predicted labels (0 or 1).
        y_prob: Array of predicted probabilities for class 1.
        
    Returns:
        dict: Metrics including roc_auc, accuracy, f1_score.
    """
    from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
    
    metrics = {}
    try:
        metrics['roc_auc'] = float(roc_auc_score(y_true, y_prob))
    except Exception as e:
        logger.warning(f"Could not calculate ROC-AUC: {e}. Setting to None.")
        metrics['roc_auc'] = None
        
    try:
        metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
    except Exception as e:
        logger.warning(f"Could not calculate Accuracy: {e}. Setting to None.")
        metrics['accuracy'] = None
        
    try:
        metrics['f1_score'] = float(f1_score(y_true, y_pred, zero_division=0))
    except Exception as e:
        logger.warning(f"Could not calculate F1-Score: {e}. Setting to None.")
        metrics['f1_score'] = None
        
    return metrics

def evaluate_model(cv_results):
    """
    Aggregate metrics from nested CV results.
    
    Args:
        cv_results: Dict containing 'outer_folds' list, each with 'y_true', 'y_pred', 'y_prob'.
        
    Returns:
        dict: Aggregated performance report.
    """
    if not cv_results or 'outer_folds' not in cv_results:
        raise ValueError("Invalid CV results format: missing 'outer_folds'.")
    
    folds = cv_results['outer_folds']
    if not folds:
        raise ValueError("No outer folds found in CV results.")
    
    per_fold_metrics = []
    all_y_true = []
    all_y_pred = []
    all_y_prob = []
    
    for i, fold_data in enumerate(folds):
        y_true = fold_data.get('y_true')
        y_pred = fold_data.get('y_pred')
        y_prob = fold_data.get('y_prob')
        
        if y_true is None or y_pred is None or y_prob is None:
            logger.warning(f"Fold {i} missing prediction data, skipping.")
            continue
            
        fold_metrics = calculate_metrics(y_true, y_pred, y_prob)
        fold_metrics['fold_index'] = i
        per_fold_metrics.append(fold_metrics)
        
        all_y_true.extend(y_true)
        all_y_pred.extend(y_pred)
        all_y_prob.extend(y_prob)
    
    # Calculate aggregate metrics across all samples (macro average)
    aggregate_metrics = {}
    if all_y_true:
        aggregate_metrics = calculate_metrics(all_y_true, all_y_pred, all_y_prob)
        aggregate_metrics['description'] = "Aggregate across all test samples"
    else:
        logger.error("No valid data points across all folds to calculate aggregate metrics.")
    
    # Calculate mean of per-fold metrics
    mean_metrics = {}
    if per_fold_metrics:
        for key in ['roc_auc', 'accuracy', 'f1_score']:
            values = [m[key] for m in per_fold_metrics if m[key] is not None]
            if values:
                mean_metrics[key] = float(np.mean(values))
            else:
                mean_metrics[key] = None
        mean_metrics['description'] = "Mean of per-fold metrics"
    
    report = {
        "task_id": "T024",
        "status": "completed",
        "total_folds": len(folds),
        "valid_folds": len(per_fold_metrics),
        "per_fold_metrics": per_fold_metrics,
        "mean_metrics": mean_metrics,
        "aggregate_metrics": aggregate_metrics,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return report

def main():
    """Main entry point for T024."""
    logger.info("Starting model evaluation (T024).")
    
    # Check for cv_results.json
    if not CV_RESULTS_PATH.exists():
        logger.warning(f"CV results file {CV_RESULTS_PATH} not found. Attempting to re-run training script to generate it.")
        # Attempt to run the training script
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(TRAIN_MODEL_SCRIPT)],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if result.returncode != 0:
                logger.error(f"Training script failed: {result.stderr}")
                logger.error("CRITICAL: Cannot evaluate model without training results.")
                sys.exit(1)
            logger.info("Training script re-run successful.")
        except Exception as e:
            logger.error(f"Failed to trigger training script: {e}")
            logger.error("CRITICAL: CV results not found. T023 must produce cv_results.json.")
            sys.exit(1)
    
    if not MODEL_PATH.exists():
        logger.error(f"Model file {MODEL_PATH} not found. Cannot evaluate.")
        sys.exit(1)
    
    # Load CV results
    try:
        cv_results = load_json(CV_RESULTS_PATH)
    except Exception as e:
        logger.error(f"Failed to load CV results: {e}")
        sys.exit(1)
    
    # Evaluate
    try:
        report = evaluate_model(cv_results)
    except Exception as e:
        logger.error(f"Failed to evaluate model: {e}")
        sys.exit(1)
    
    # Save report
    ensure_dir(PERFORMANCE_REPORT_PATH.parent)
    save_json(report, PERFORMANCE_REPORT_PATH)
    
    logger.info(f"Evaluation complete. Report saved to {PERFORMANCE_REPORT_PATH}")
    print(json.dumps(report, indent=2))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())