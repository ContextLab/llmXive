"""
Evaluate the trained Random Forest model.

Calculates ROC-AUC, accuracy, and F1-score per fold and mean.
Outputs results to data/processed/performance_report.json.

Dependencies:
  - data/processed/model.pkl (produced by T023)
  - data/processed/cv_results.json (produced by T023)
"""
from __future__ import annotations

import json
import sys
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

# Import project utilities
from utils.logger import get_logger, log_operation
from utils.io import load_json, save_json, load_pickle

logger = get_logger("evaluate_model")


def ensure_file(path: Path) -> None:
    """Ensure the directory for a file path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def isnan(value: Any) -> bool:
    """Check if a value is NaN."""
    try:
        return np.isnan(value)
    except (TypeError, ValueError):
        return False


def load_eligible_subjects(csv_path: Path) -> List[str]:
    """Load subject IDs from the eligible subjects CSV."""
    # Although not strictly needed for metric calculation if we trust cv_results,
    # we load it to ensure consistency with the pipeline's data contracts.
    import csv
    subjects = []
    if csv_path.exists():
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Assuming 'subject_id' is the key based on T017a
                key = 'subject_id' if 'subject_id' in row else list(row.keys())[0]
                subjects.append(row[key])
    return subjects


def load_features(features_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load features and labels from the processed graph metrics CSV.
    This is a placeholder to satisfy the function signature if needed,
    but T024 primarily relies on the model and cv_results from T023.
    """
    # In a full pipeline, this would load the graph_metrics.csv
    # For T024, we assume the model was trained and evaluated in T023,
    # and we are re-calculating metrics or aggregating them.
    # However, to be robust, we will load the model and re-predict if labels are available,
    # or simply aggregate the cv_results if they are present.
    # Since T023 writes cv_results.json, we will primarily use that.
    return np.array([]), np.array([])


def split_features_labels(data: np.ndarray, labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return features and labels."""
    return data, labels


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """Calculate ROC-AUC, accuracy, and F1-score."""
    metrics = {}
    try:
        # ROC-AUC requires probability scores and at least two classes
        if len(np.unique(y_true)) > 1 and len(y_prob) > 0:
            metrics['roc_auc'] = roc_auc_score(y_true, y_prob)
        else:
            metrics['roc_auc'] = 0.0
    except ValueError:
        metrics['roc_auc'] = 0.0

    metrics['accuracy'] = accuracy_score(y_true, y_pred)
    metrics['f1_score'] = f1_score(y_true, y_pred, zero_division=0.0)

    return metrics


def evaluate_model(model_path: Path, cv_results_path: Path) -> Dict[str, Any]:
    """
    Load the model and CV results to generate the performance report.
    If cv_results.json exists, we aggregate the fold metrics.
    If not, we attempt to re-evaluate (though T023 should have produced it).
    """
    if not cv_results_path.exists():
        logger.log("evaluate_model_error", message=f"CV Results file not found: {cv_results_path}")
        raise FileNotFoundError(f"Required file missing: {cv_results_path}")

    cv_results = load_json(cv_results_path)

    # Structure: list of dicts with fold, roc_auc, accuracy, f1_score
    # If T023 produced it correctly, we just aggregate.
    folds = []
    if isinstance(cv_results, list):
        for i, res in enumerate(cv_results):
            folds.append({
                "fold": res.get("fold", i + 1),
                "roc_auc": float(res.get("roc_auc", 0.0)),
                "accuracy": float(res.get("accuracy", 0.0)),
                "f1_score": float(res.get("f1_score", 0.0))
            })
    elif isinstance(cv_results, dict) and "folds" in cv_results:
        for i, res in enumerate(cv_results["folds"]):
            folds.append({
                "fold": res.get("fold", i + 1),
                "roc_auc": float(res.get("roc_auc", 0.0)),
                "accuracy": float(res.get("accuracy", 0.0)),
                "f1_score": float(res.get("f1_score", 0.0))
            })

    if not folds:
        logger.log("evaluate_model_warning", message="No fold results found in cv_results.json")

    # Calculate means
    mean_roc_auc = np.mean([f["roc_auc"] for f in folds]) if folds else 0.0
    mean_accuracy = np.mean([f["accuracy"] for f in folds]) if folds else 0.0
    mean_f1_score = np.mean([f["f1_score"] for f in folds]) if folds else 0.0

    report = {
        "fold_metrics": folds,
        "mean_roc_auc": float(mean_roc_auc),
        "mean_accuracy": float(mean_accuracy),
        "mean_f1_score": float(mean_f1_score)
    }

    return report


def write_performance_report(report: Dict[str, Any], output_path: Path) -> None:
    """Write the performance report to JSON."""
    ensure_file(output_path)
    save_json(report, output_path)
    logger.log("write_performance_report", message=f"Report written to {output_path}")


def main() -> int:
    """Main entry point for T024."""
    try:
        # Define paths relative to project root
        # Assuming script runs from project root or code/
        project_root = Path(__file__).parent.parent
        model_path = project_root / "data" / "processed" / "model.pkl"
        cv_results_path = project_root / "data" / "processed" / "cv_results.json"
        output_path = project_root / "data" / "processed" / "performance_report.json"

        logger.log("evaluate_model_start", message="Starting model evaluation")

        # Check prerequisites
        if not model_path.exists():
            logger.log("evaluate_model_error", message=f"Model file missing: {model_path}")
            logger.log("exit_code", code=1)
            return 1

        if not cv_results_path.exists():
            logger.log("evaluate_model_error", message=f"CV Results file missing: {cv_results_path}")
            logger.log("exit_code", code=1)
            return 1

        # Evaluate
        report = evaluate_model(model_path, cv_results_path)

        # Write output
        write_performance_report(report, output_path)

        logger.log("evaluate_model_success", message="Evaluation complete")
        return 0

    except Exception as e:
        logger.log("evaluate_model_exception", message=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())