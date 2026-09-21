"""
Task T036a: Calculate and log confusion matrix, precision, recall, F1-score,
and standard deviation of accuracy for high/low responders.

This script reads model predictions from T034d-3 (model_predictions.json)
and aggregates metrics into data/results/model_metrics.json.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, accuracy_score

# Add project root to path to allow relative imports if needed
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import get_logger
from utils.config import get_results_path

logger = get_logger(__name__)

def load_model_predictions():
    """Load model predictions from the nested CV output."""
    predictions_path = get_results_path("model_predictions.json")
    if not predictions_path.exists():
        raise FileNotFoundError(f"Model predictions file not found: {predictions_path}")
    
    with open(predictions_path, 'r') as f:
        return json.load(f)

def calculate_confusion_matrix(y_true, y_pred):
    """Calculate confusion matrix and return as dictionary."""
    cm = confusion_matrix(y_true, y_pred)
    return {
        "tn": int(cm[0][0]),
        "fp": int(cm[0][1]),
        "fn": int(cm[1][0]),
        "tp": int(cm[1][1])
    }

def calculate_metrics_for_threshold(predictions_list, threshold_idx):
    """Calculate metrics for a specific threshold's predictions."""
    all_y_true = []
    all_y_pred = []
    fold_accuracies = []

    for fold_idx, fold_data in enumerate(predictions_list):
        y_true = fold_data.get("y_true", [])
        y_pred = fold_data.get("y_pred", [])
        
        if not y_true or not y_pred:
            logger.warning(f"Threshold {threshold_idx}, Fold {fold_idx}: Empty predictions, skipping.")
            continue

        all_y_true.extend(y_true)
        all_y_pred.extend(y_pred)

        # Calculate per-fold accuracy for std calculation
        fold_acc = accuracy_score(y_true, y_pred)
        fold_accuracies.append(fold_acc)

    if not all_y_true:
        logger.error(f"No valid predictions found for threshold {threshold_idx}")
        return None

    # Calculate aggregate metrics
    cm = calculate_confusion_matrix(all_y_true, all_y_pred)
    precision = precision_score(all_y_true, all_y_pred, zero_division=0)
    recall = recall_score(all_y_true, all_y_pred, zero_division=0)
    f1 = f1_score(all_y_true, all_y_pred, zero_division=0)
    mean_acc = np.mean(fold_accuracies)
    std_acc = np.std(fold_accuracies)

    return {
        "confusion_matrix": cm,
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "mean_accuracy": float(mean_acc),
        "std_accuracy": float(std_acc),
        "n_subjects": len(all_y_true),
        "n_folds": len(fold_accuracies)
    }

def aggregate_metrics(all_predictions):
    """Aggregate metrics across all thresholds."""
    results = {
        "thresholds": [],
        "summary": {}
    }

    for threshold_idx, predictions in enumerate(all_predictions):
        logger.info(f"Processing threshold index {threshold_idx}")
        metrics = calculate_metrics_for_threshold(predictions, threshold_idx)
        
        if metrics:
            results["thresholds"].append({
                "threshold_index": threshold_idx,
                **metrics
            })
    
    # Calculate overall summary if we have results
    if results["thresholds"]:
        all_mean_accs = [t["mean_accuracy"] for t in results["thresholds"]]
        all_std_accs = [t["std_accuracy"] for t in results["thresholds"]]
        
        results["summary"] = {
            "overall_mean_accuracy": float(np.mean(all_mean_accs)),
            "overall_std_accuracy": float(np.mean(all_std_accs)),
            "total_thresholds_evaluated": len(results["thresholds"]),
            "status": "completed"
        }
    else:
        results["summary"] = {
            "status": "failed",
            "message": "No valid metrics calculated for any threshold"
        }

    return results

def save_metrics(results):
    """Save aggregated metrics to model_metrics.json."""
    output_path = get_results_path("model_metrics.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def run_metrics_calculation():
    """Main entry point for T036a."""
    logger.info("Starting T036a: Calculate model metrics")
    
    try:
        predictions = load_model_predictions()
        logger.info(f"Loaded predictions for {len(predictions)} thresholds")
        
        metrics_results = aggregate_metrics(predictions)
        save_metrics(metrics_results)
        
        logger.info("T036a completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during metrics calculation: {e}")
        raise

def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    sys.exit(run_metrics_calculation())

if __name__ == "__main__":
    main()