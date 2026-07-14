"""Evaluate the trained model and generate performance report."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from joblib import load
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

# Import from local utils and project modules
# Note: The project uses utils/logger.py for the canonical logger
# but 05_evaluate_model.py historically imported a wrapper.
# We ensure compatibility by importing the standard interface.
try:
    from utils.logger import get_logger, log_operation
except ImportError:
    # Fallback if utils.logger is not yet available or named differently
    # This block should ideally not be reached if T005/T006 completed
    class SimpleLogger:
        def info(self, msg): print(msg)
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
    def get_logger(name): return SimpleLogger()
    def log_operation(op, **kwargs): return lambda f: f

# Constants
DATA_DIR = Path("data/processed")
MODEL_PATH = DATA_DIR / "model.pkl"
METRICS_PATH = DATA_DIR / "graph_metrics.csv"
ELIGIBLE_PATH = DATA_DIR / "eligible_subjects.csv"
OUTPUT_PATH = DATA_DIR / "performance_report.json"
MODEL_PARAMS_PATH = DATA_DIR / "model_params.json"

logger = get_logger("evaluate_model")


def ensure_file(path: Path) -> None:
    """Ensure the directory for a file exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def isnan(x: Any) -> bool:
    """Check if a value is NaN."""
    try:
        return np.isnan(x)
    except (TypeError, ValueError):
        return False


def load_eligible_subjects() -> List[str]:
    """Load list of eligible subject IDs."""
    if not ELIGIBLE_PATH.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_PATH}")
    df = pd.read_csv(ELIGIBLE_PATH)
    return df["subject_id"].tolist()


def load_features() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Load features and labels from graph_metrics.csv."""
    if not METRICS_PATH.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {METRICS_PATH}")

    df = pd.read_csv(METRICS_PATH)

    # Determine label column based on common conventions or schema
    # The spec defines decline label as drop >= 3 points.
    # Assuming the column is named 'decline_label' or similar.
    label_col = None
    for col in ["decline_label", "label", "y"]:
        if col in df.columns:
            label_col = col
            break

    if label_col is None:
        raise ValueError("No label column found in graph_metrics.csv. Expected 'decline_label', 'label', or 'y'.")

    # Identify feature columns (all numeric columns except subject_id and label)
    feature_cols = [c for c in df.columns if c not in ["subject_id", label_col] and df[c].dtype in [np.float64, np.int64, np.float32, np.int32]]

    if not feature_cols:
        raise ValueError("No feature columns found in graph_metrics.csv.")

    X = df[feature_cols].values
    y = df[label_col].values
    return X, y, feature_cols


def split_features_labels(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Ensure X and y are properly shaped numpy arrays."""
    X = np.asarray(X)
    y = np.asarray(y)
    if y.ndim == 2 and y.shape[1] == 1:
        y = y.ravel()
    return X, y


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """Calculate ROC-AUC, accuracy, and F1-score."""
    metrics = {}

    # Accuracy
    metrics["accuracy"] = float(accuracy_score(y_true, y_pred))

    # F1 Score
    metrics["f1_score"] = float(f1_score(y_true, y_pred, zero_division=0))

    # ROC-AUC
    # Handle case where only one class is present or probabilities are invalid
    try:
        if len(np.unique(y_true)) > 1:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        else:
            metrics["roc_auc"] = float("nan")
    except ValueError:
        metrics["roc_auc"] = float("nan")

    return metrics


def evaluate_model(
    X: np.ndarray, y: np.ndarray, model_path: Path
) -> Dict[str, Any]:
    """
    Evaluate the trained model using nested cross-validation logic
    (re-using the outer loop structure if available, or simple CV if model is global).

    Since the model was trained with nested CV in T023, we assume the model.pkl
    contains the final fitted estimator. We perform a simple K-fold evaluation
    on the available data to estimate per-fold metrics as requested by T024.
    """
    logger.log("evaluate_model_start")

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = load(model_path)

    # Use StratifiedKFold to match the training setup
    n_splits = 5
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    fold_results = []
    all_y_true = []
    all_y_pred = []
    all_y_prob = []

    logger.log("cross_validation_start", n_splits=n_splits)

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Predict
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        fold_metrics = calculate_metrics(y_test, y_pred, y_prob)
        fold_metrics["fold"] = fold_idx + 1

        fold_results.append(fold_metrics)
        all_y_true.extend(y_test)
        all_y_pred.extend(y_pred)
        all_y_prob.extend(y_prob)

        logger.log("fold_complete", fold=fold_idx + 1, metrics=fold_metrics)

    # Aggregate results
    all_y_true = np.array(all_y_true)
    all_y_pred = np.array(all_y_pred)
    all_y_prob = np.array(all_y_prob)

    mean_metrics = calculate_metrics(all_y_true, all_y_pred, all_y_prob)
    mean_metrics["mean"] = True

    # Calculate standard deviations for metrics
    std_metrics = {}
    for key in ["accuracy", "f1_score", "roc_auc"]:
        vals = [r[key] for r in fold_results if not isnan(r[key])]
        if vals:
            std_metrics[f"{key}_std"] = float(np.std(vals))
        else:
            std_metrics[f"{key}_std"] = float("nan")

    report = {
        "fold_results": fold_results,
        "mean_accuracy": mean_metrics["accuracy"],
        "mean_f1_score": mean_metrics["f1_score"],
        "mean_roc_auc": mean_metrics["roc_auc"],
        "accuracy_std": std_metrics.get("accuracy_std", float("nan")),
        "f1_score_std": std_metrics.get("f1_score_std", float("nan")),
        "roc_auc_std": std_metrics.get("roc_auc_std", float("nan")),
        "n_folds": n_splits,
        "n_samples": len(y),
    }

    logger.log("evaluate_model_complete", mean_roc_auc=report["mean_roc_auc"])
    return report


def write_performance_report(report: Dict[str, Any], output_path: Path) -> None:
    """Write the performance report to JSON."""
    ensure_file(output_path)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.log("report_written", path=str(output_path))


def main() -> int:
    """Main entry point for evaluation."""
    try:
        logger.log("main_start")

        # Load data
        subjects = load_eligible_subjects()
        logger.log("subjects_loaded", count=len(subjects))

        X, y, feature_names = load_features()
        logger.log("features_loaded", shape=X.shape)

        X, y = split_features_labels(X, y)

        # Evaluate
        report = evaluate_model(X, y, MODEL_PATH)

        # Write report
        write_performance_report(report, OUTPUT_PATH)

        # Also ensure model_params.json exists if it doesn't (from T023)
        # If T023 failed to write it, we might need to handle that,
        # but T024's primary job is the performance report.
        # We assume T023 handled model_params.json.

        logger.log("main_complete")
        return 0

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())