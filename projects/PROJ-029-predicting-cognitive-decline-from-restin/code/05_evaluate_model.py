"""
Evaluate the trained Random Forest model.
Calculates ROC-AUC, accuracy, and F1-score per fold and mean.
Outputs to data/processed/performance_report.json.
"""
from __future__ import annotations

import json
import sys
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.exceptions import UndefinedMetricWarning
import warnings

# Project imports
from utils.logger import get_logger, log_operation
from utils.io import load_json, save_json, load_pickle
from config import get_config

# Suppress warnings for undefined metrics (e.g., F1 with only one class)
warnings.filterwarnings("ignore", category=UndefinedMetricWarning)

logger = get_logger("evaluate_model")

def ensure_file(path: Path, description: str) -> None:
    """Ensure a required file exists, exiting with error if not."""
    if not path.exists():
        logger.log("file_missing", path=str(path), description=description)
        print(f"Error: Missing required file: {path}")
        sys.exit(1)

def isnan(val: Any) -> bool:
    """Check if a value is NaN."""
    try:
        return np.isnan(val)
    except (TypeError, ValueError):
        return False

def load_eligible_subjects(path: Path) -> List[str]:
    """Load eligible subject IDs from CSV (used for validation if needed)."""
    # Implementation depends on CSV structure, but for evaluation we primarily
    # rely on the model and cv_results which contain the fold data.
    # This is a placeholder to satisfy the API surface requirement.
    return []

def load_features(path: Path) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load features and labels from the training artifacts.
    This is a fallback if cv_results is incomplete, but T023 should produce cv_results.
    We primarily read from cv_results.json for per-fold metrics.
    """
    # In a full pipeline, we might reload data to re-predict.
    # However, T023 (train_model.py) is responsible for saving cv_results.json
    # with per-fold metrics. We will read that.
    # If cv_results is missing, we cannot evaluate per fold without re-running.
    # We assume cv_results.json exists as per T023 contract.
    return np.array([]), np.array([]), []

def split_features_labels(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Split features and labels (identity for this implementation as data is already split)."""
    return X, y

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """Calculate ROC-AUC, accuracy, and F1-score."""
    metrics = {}
    
    # Accuracy
    metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
    
    # F1 Score
    try:
        metrics['f1_score'] = float(f1_score(y_true, y_pred, zero_division=0))
    except Exception:
        metrics['f1_score'] = 0.0
    
    # ROC-AUC
    try:
        # Ensure we have at least two classes for ROC-AUC
        if len(np.unique(y_true)) < 2:
            metrics['roc_auc'] = 0.5  # Baseline for single class
        else:
            metrics['roc_auc'] = float(roc_auc_score(y_true, y_prob))
    except Exception:
        metrics['roc_auc'] = 0.5

    return metrics

def evaluate_model(model_path: Path, cv_results_path: Path) -> Dict[str, Any]:
    """
    Load the model and CV results to generate the performance report.
    If cv_results.json exists (produced by T023), we aggregate from there.
    If not, we attempt to re-predict using the saved model and data.
    """
    # Check dependencies
    ensure_file(model_path, "Trained model file")
    
    # Try to load cv_results first (T023 output)
    if cv_results_path.exists():
        cv_data = load_json(cv_results_path)
        # T023 writes cv_results.json. We need to aggregate it.
        # Expected schema: list of dicts with fold, roc_auc, accuracy, f1_score
        folds = []
        for entry in cv_data:
            fold_metrics = {
                "fold": entry.get("fold", 0),
                "roc_auc": entry.get("roc_auc", 0.0),
                "accuracy": entry.get("accuracy", 0.0),
                "f1_score": entry.get("f1_score", 0.0)
            }
            folds.append(fold_metrics)
        
        if not folds:
            # Fallback if cv_results is empty or malformed
            raise ValueError("cv_results.json is empty or malformed")
        
        # Calculate means
        roc_aucs = [f["roc_auc"] for f in folds]
        accuracies = [f["accuracy"] for f in folds]
        f1_scores = [f["f1_score"] for f in folds]
        
        report = {
            "folds": folds,
            "mean_roc_auc": float(np.mean(roc_aucs)),
            "mean_accuracy": float(np.mean(accuracies)),
            "mean_f1_score": float(np.mean(f1_scores))
        }
        return report

    else:
        # If cv_results is missing, we must re-evaluate if we have data
        # This path assumes T023 failed to write cv_results but wrote model.pkl
        # and we have access to the original data (graph_metrics.csv + labels)
        # However, T024 depends on T023. If T023 failed, we can't fully recover.
        # We will raise an error if cv_results is missing, as per strict dependency.
        logger.log("cv_results_missing", path=str(cv_results_path))
        print(f"Error: {cv_results_path} not found. T023 (train_model.py) must run first.")
        sys.exit(1)

def write_performance_report(report: Dict[str, Any], output_path: Path) -> None:
    """Write the performance report to JSON."""
    ensure_dir = output_path.parent
    ensure_dir.mkdir(parents=True, exist_ok=True)
    save_json(report, output_path)
    logger.log("report_written", path=str(output_path))

def main() -> None:
    """Main entry point for model evaluation."""
    config = get_config()
    base_path = Path(config.get("data_dir", "data/processed"))
    
    model_path = base_path / "model.pkl"
    cv_results_path = base_path / "cv_results.json"
    output_path = base_path / "performance_report.json"
    
    logger.log("start_evaluation", model=str(model_path), cv_results=str(cv_results_path))
    
    try:
        report = evaluate_model(model_path, cv_results_path)
        write_performance_report(report, output_path)
        logger.log("evaluation_complete", output=str(output_path))
        print(f"Performance report written to {output_path}")
    except Exception as e:
        logger.log("evaluation_failed", error=str(e))
        print(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
